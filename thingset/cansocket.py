import datetime
import socket
import struct
import time
from cbor2 import loads
from thingset.packet import TSPacket, SingleFrame, RequestFrame


class CANsocket(object):
    FMT = '<IB3x8s'

    databuffer = bytearray()
    packetsize = int()
    last_index = int()
    flow_control = {}
    sub_addresses = list()
    address = int()

    status_code = {
        0x81: 'Created',
        0x82: 'Deleted',
        0x83: 'Valid',
        0x84: 'Changed',
        0x85: 'Content',
        0xA0: 'ERROR: Bad Request',
        0xA1: 'ERROR: Unauthorized',
        0xA3: 'ERROR: Forbidden',
        0xA4: 'ERROR: Not Found',
        0xA5: 'ERROR: Method not allowed',
        0xA8: 'ERROR: Request Incomplete',
        0xA9: 'ERROR: Conflict',
        0xAD: 'ERROR: Request too large',
        0xAF: 'ERROR: Unsupported Format',
        0xC0: 'ERROR: Internal Server Error',
        0xC1: 'ERROR: Not Implemented',
        0xE1: 'ERROR: Response too large',
    }

    fc_flags = {0x00: 'Continue', 0x01: 'Wait', 0x02: 'Abort'}

    def __init__(self, interface: str, address: int = 0x01):
        self.s = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.s.bind((interface,))
        self.address = address

    def subscribe(self, addr: int) -> None:
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        if not addr in self.sub_addresses:
            self.sub_addresses.append(addr)

    def receive(self) -> tuple:
        '''Receive function with ThingSet/ISO-TP Frame handling
        Returns a tuple with 4 entries:
            1: Is Publication Frame: bool
            2: Status or Data Object ID: int
            3: Data: Deserialized Object (bool, int, float, list, dict)
            4: Publication Frame Source ID
        '''
        ret = None
        packet = self.s.recv(64)
        can_id, length, data = struct.unpack(self.FMT, packet)
        can_id &= socket.CAN_EFF_MASK

        if (can_id & TSPacket.TS_FRAME_FLAG):
            frame = SingleFrame(data=data)
            frame.parseIdentifier(can_id)
            if frame.source in self.sub_addresses:
                ret = (True, frame.dataobjectID, frame.cbor, frame.source)
        else:
            frame = RequestFrame(data=data)
            frame.parseIdentifier(can_id)
            if frame.destination == self.address:
                if frame.type == RequestFrame.FRAME_TYPE_SINGLE:
                    status = self.status_code[data[1]]
                    if status == 'Content':
                        ret = (False, status, loads(frame.data[2:]), None)
                    else:
                        ret = (False, status, None, None)
                if frame.type == RequestFrame.FRAME_TYPE_FIRST:
                    self.packetsize = frame.framesize
                    self.databuffer.clear()
                    self.databuffer.extend(frame.data[2:])
                    self.last_index = 0
                    fc_frame = RequestFrame(
                        src=self.address, dst=frame.source, data=b'\x30\x00\x00')
                    self.send(fc_frame)
                if frame.type == RequestFrame.FRAME_TYPE_CONSEC:
                    expected_index = (self.last_index + 1) % 16
                    if frame.index == expected_index:
                        self.last_index = expected_index
                        frame.data = data[1:]
                        self.databuffer.extend(frame.data)
                        if len(self.databuffer) >= self.packetsize:
                            status = self.status_code[self.databuffer[0]]
                            ret = (False, status,
                                   (loads(self.databuffer[1:])), None)
                if frame.type == RequestFrame.FRAME_TYPE_FLOWC:
                    self.flow_control['flag'] = frame.fcflag
                    self.flow_control['blocksize'] = frame.fcflag
                    self.flow_control['delay'] = frame.fcflag

        return ret

    def send(self, message: RequestFrame) -> bool:
        '''Send function with basic ThingSet/ISO-TP handling
        Returns True on Success
        '''
        can_id = message.identifier | socket.CAN_EFF_FLAG

        if message.type == RequestFrame.FRAME_TYPE_FLOWC:
            can_packet = struct.pack(
                self.FMT, can_id, len(message.data), message.data)
            self.s.send(can_packet)
        else:
            if len(message.data) <= 7:
                # data fits in single frame
                frame_data = bytearray()
                frame_data.append(len(message.data))
                frame_data.extend(message.data)
                can_packet = struct.pack(
                    self.FMT, can_id, len(frame_data), frame_data)
                self.s.send(can_packet)
            else:
                # First Frame
                data = bytearray(message.data)
                index = 0
                block = 0
                length = len(data)
                len_bytes = length.to_bytes(2, byteorder='little')
                frame_data = bytearray()
                frame_data.append(0x10 | len_bytes[1])
                frame_data.append(len_bytes[0])
                frame_data.extend(data[:6])
                del data[:6]
                can_packet = struct.pack(self.FMT, can_id, 8, frame_data)
                self.s.send(can_packet)
                if self.waitFC():
                    # Consecutive Frames
                    flag, blocksize, delay_s = self.evalFCFlags()
                    if flag == 'Abort':
                        return False
                    self.flow_control.clear()
                    while len(data) != 0:
                        if len(data) >= 7:
                            frame_data = bytearray()
                            index += 1
                            index %= 16
                            frame_data.append(0x20 | index)
                            frame_data.extend(data[:7])
                            del data[:7]
                            self.s.send(struct.pack(
                                self.FMT, can_id, len(frame_data), frame_data))
                            block += 1
                            if block == blocksize:
                                block = 0
                                if self.waitFC():
                                    flag, blocksize, delay_s = self.evalFCFlags()
                                    if flag == 'Abort':
                                        return False
                                    self.flow_control.clear()
                                else:
                                    print("Flow Control Timeout while sending")
                                    return False
                            else:
                                time.sleep(delay_s)
                        else:
                            frame_data = bytearray()
                            index += 1
                            frame_data.append(0x20 | index)
                            frame_data.extend(data)
                            self.s.send(struct.pack(
                                self.FMT, can_id, len(frame_data), frame_data))
                            del data[:]
                else:
                    print("Flow Control Timeout before sending")
                    return False
        return True

    def waitFC(self, timeout: float = 0.5):
        '''Wait for Flow Control Frame and return False on Timeout and True on Success'''
        ret = bool(False)
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() <= timeout:
            if self.flow_control:
                ret = True
                break
        return ret

    def evalFCFlags(self):
        fcflag = self.flow_control['flag']
        blocksize = self.flow_control['blocksize']
        delay_code = self.flow_control['delay']
        if delay_code <= 127:
            delay_s = float(delay_code) / 1000.0
        elif delay_code >= 0xF1 and delay_code <= 0xF9:
            delay_s = float(delay_code & 0xF) / 10000.0
        else:
            delay_s = 0.0
        if self.fc_flags[fcflag] == 'Wait':
            time.sleep(1.0)
        return (self.fc_flags[fcflag], blocksize, delay_s)
