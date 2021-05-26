from thingset.cansocket import CANsocket
import json, requests, time

sock = CANsocket('can0')  # or other interface
emonstring = 'http://192.168.178.26/emoncms/input/post?node='
apikey = 'dc8ae3d6a908d75b370ae83b1733a564'
dataObject = {0x00:{0x4001: 'vBat', 0x4002: 'vLoad', 0x4003: 'vCell1', 0x4004: 'vCell2',
			  0x4005: 'vCell3', 0x4006: 'vCell4', 0x4007: 'vCell5', 0x4008: 'iBat',
			  0x4009: 'tempBat', 0x400A: 'SOC'},
			  0x0A:{0x4001: 'vBat', 0x4002: 'vSolar', 0x4003: 'iBat', 0x4004: 'iLoad',
			  0x4005: 'tempExt', 0x4006: 'tempInt', 0x4007: 'loadEn', 0x4008: 'eInputDay_Wh',
			  0x4009: 'eOutputDay_Wh', 0x400A: 'eInputTotal_Wh', 0x400B: 'eOutputTotal_Wh'}}

dataBMS = {'vBat': 0}
dataMPPT = {'vBat': 0}
end = 0

start = time.time()
while(True):
	frame = sock.receive()
	node = -1
	if frame.source == 0x0A:
		node = 'MPPT'
		dataMPPT.update({dataObject[0x0A][frame.dataobjectID]: float(frame.cbor)})
	if frame.source == 0x00:
		node = 'BMS'
		dataBMS.update({dataObject[0x00][frame.dataobjectID]: float(frame.cbor)})
	if node == -1:
		print("Error! Unknown Source")
		break
	if (end - start) > 1:
		emonpostBMS = emonstring + 'BMS' + '&fulljson=' + json.dumps(dataBMS) + '&apikey=' + apikey
		emonpostMPPT = emonstring + 'MPPT' + '&fulljson=' + json.dumps(dataMPPT) + '&apikey=' + apikey
		rBMS = requests.post(emonpostBMS)
		rMPPT = requests.post(emonpostMPPT)
		print('{} : {}'.format(json.dumps(dataBMS), rBMS.content))
		print('{} : {}'.format(json.dumps(dataMPPT), rMPPT.content))
		start = time.time()
	end = time.time()
