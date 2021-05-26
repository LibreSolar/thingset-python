
from thingset.cansocket import CANsocket
sock = CANsocket('can0')  # or other interface

while(True):
	frame = sock.receive()
	if isinstance(frame.cbor, float):
		print("device: 0x%x  data id: 0x%x   value: %.2f" % (frame.source, frame.dataobjectID, frame.cbor))
	else:
		print("device:", hex(frame.source), " data id:", hex(frame.dataobjectID), "  value:", frame.cbor)
