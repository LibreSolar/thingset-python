import socket
import struct
from thingset.packet import TSPacket, SingleFrame

class CANsocket(object):
    FMT = '<IB3x8s'

    def __init__(self, interface):
        self.s = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        self.s.bind((interface,))

    def receive(self):
        packet = self.s.recv(64)
        can_id, length, data = struct.unpack(self.FMT, packet)
        can_id &= socket.CAN_EFF_MASK
        frame = SingleFrame(data=data)
        if (can_id & TSPacket.TS_FRAME_FLAG):
            frame.parseIdentifier(can_id)

        return(frame)

    def send(self, message):
        can_id = message.identifier | socket.CAN_EFF_FLAG
        can_packet = struct.pack(self.FMT, can_id, len(message.data), message.data)
        self.s.send(can_packet)
