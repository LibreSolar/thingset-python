from socket import CAN_EFF_FLAG
from cbor2 import loads

class TSPacket(object):
    TS_FRAME_FLAG = (1 << 24)

    def __init__(self, source=0, timestamp=0.0):
        self.source = source
        self.timestamp = timestamp

    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, source):
        if source not in range(0,256):
            raise ValueError("Source ID must be integer between 0 and 255 (got: {})".format(source))
        self._source = source

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        if not isinstance(timestamp, float):
            raise TypeError("Timestamp must be float (got: {})".format(type(timestamp)))
        self._timestamp = timestamp


class PublicationFrame(TSPacket):
    def __init__(self, dataobjectID=0, priority=6):
        super().__init__()
        self.dataobjectID = dataobjectID
        self._messageType = True
        self.priority = priority

    @property
    def messageType(self):
        return "Publication message"

    @property
    def dataobjectID(self):
        return self._dataobjectID

    @dataobjectID.setter
    def dataobjectID(self, dataobjectID):
        if not dataobjectID in range(0,65537):
            raise ValueError("Data object ID must be integer between 0 and 65536 (got: {}).".format(dataobjectID))
        self._dataobjectID = dataobjectID


class SingleFrame(PublicationFrame):
    SINGLE_ID_MASK = (0b11 << 24)

    def __init__(self, data=None, dataobjectID=0, priority=6, source=0, timestamp=0.0):
        super().__init__()
        self._cbor = None
        self.data = data
        self.dataobjectID = dataobjectID
        self.priority = priority
        self.source = source
        self.timestamp = timestamp

    def parseIdentifier(self, identifier):
        if not isinstance(identifier, int):
            raise ValueError("Identifier must be integer, not {}.".format(identifier))
        if identifier >= (1 << 30):
            raise ValueError("Identifier too big. Cannot contain more than 29 bits")
        if not (identifier & TSPacket.TS_FRAME_FLAG):
            raise ValueError("Not a publication message.")
        self.priority = identifier >> 26
        self.dataobjectID = (identifier & 0xffffff) >> 8
        self.source = identifier & 0xff

    @property
    def identifier(self):
        id_prio = self._priority << 26
        id_doid = self._dataobjectID << 8
        return id_prio | self.SINGLE_ID_MASK | id_doid | self.source

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, priority):
        self._priority = priority

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        if data is None:
            self._data = bytes()
        elif not isinstance(data, bytes):
            raise TypeError("Wrong data type. Must be bytes, not {}".format(type(data)))
        self._data = data
        self._cbor = loads(self._data)

    @property
    def cbor(self):
        return self._cbor
