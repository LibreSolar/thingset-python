import threading
import time
import datetime
from thingset.cansocket import CANsocket
from thingset.packet import RequestFrame
from cbor2 import loads, dumps


class ThingSet_CAN(threading.Thread):

    __response = None
    __own_id = int()
    __pub_callback = None

    data = dict()

    def __init__(self, if_name: str, own_id: int = 0x01):
        super().__init__()
        if own_id not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(own_id))
        self.__own_id = own_id
        self.__sock = CANsocket(if_name, self.__own_id)  # or other interface
        self.setDaemon(True)

    def setPubCallback(self, callback):
        if hasattr(callback, '__call__'):
            self.__pub_callback = callback

    def subscribe(self, addr: int):
        self.data[addr] = {}
        self.__sock.subscribe(addr)

    def get(self, addr: int, id: int):
        '''Retrieve all data from a path'''
        ret = None
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        data = bytearray(b'\x01')
        data.extend(dumps(id))
        frame = RequestFrame(src=self.__own_id, dst=addr, data=bytes(data))
        self.__sock.send(frame)
        if self.__waitResponse(0.5):
            ret = self.__getResponse()
        else:
            print("GET Timeout!")
        return ret

    def post(self, addr: int, id: int, data):
        '''Append data to an object or execute a function'''
        ret = None
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        frame_data = bytearray(b'\x02')
        frame_data.extend(dumps(id))
        frame_data.extend(dumps(data))
        frame = RequestFrame(src=self.__own_id, dst=addr,
                             data=bytes(frame_data))
        self.__sock.send(frame)
        if self.__waitResponse(0.5):
            ret = self.__getResponse()
        else:
            print("POST Timeout!")
        return ret

    def delete(self, addr: int, data):
        '''Delete data from an object'''
        ret = None
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        frame_data = bytearray(b'\x04')
        frame_data.extend(dumps(data))
        frame = RequestFrame(src=self.__own_id, dst=addr,
                             data=bytes(frame_data))
        self.__sock.send(frame)
        if self.__waitResponse(0.5):
            ret = self.__getResponse()
        else:
            print("DELETE Timeout!")
        return ret

    def fetch(self, addr: int, path_id: int, array: list):
        '''Retrieve a subset of data from a path'''
        ret = None
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        data = bytearray(b'\x05')
        data.extend(dumps(path_id))
        data.extend(dumps(array))
        frame = RequestFrame(src=self.__own_id, dst=addr, data=bytes(data))
        self.__sock.send(frame)
        if self.__waitResponse(1.5):
            ret = self.__getResponse()
        else:
            print("FETCH Timeout!")
        return ret

    def patch(self, addr: int, obj_id: int, map: dict):
        '''Update (overwrite) data of a path'''
        ret = None
        if addr not in range(0, 256):
            raise ValueError(
                "Address must be integer between 0 and 255 (got: {})".format(addr))
        data = bytearray(b'\x07')
        data.extend(dumps(obj_id))
        data.extend(dumps(map))
        self.__sock.send(RequestFrame(
            src=self.__own_id, dst=addr, data=bytes(data)))
        if self.__waitResponse():
            ret = self.__getResponse()
        else:
            print("PATCH Timeout!")

        return ret

    def __waitResponse(self, timeout: float = 1.5):
        '''Wait for response and return False on Timeout and True on Success'''
        ret = bool(False)
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=timeout)
        while datetime.datetime.now() <= timeout:
            if self.__response != None:
                ret = True
                break
        return ret

    def __getResponse(self):
        '''Returns Response Code/Response Data'''
        status, data = self.__response
        self.__response = None
        if data == None:
            ret = status
        else:
            ret = data
        return ret

    def run(self):
        '''Reception Thread Function'''
        while True:
            rx = self.__sock.receive()
            if rx != None:
                pub_frame, status, data, src_id = rx
                if pub_frame == True:
                    id = status
                    self.data[src_id].update({id: data})
                    if self.__pub_callback != None:
                        self.__pub_callback(src_id, id, data)
                else:
                    self.__response = (status, data)
