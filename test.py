# Tested with BMS-8S50-IC
#   HW v0.1.1
#   FW v21.0-57-g6c0fb5f-dirty

import threading
import time
from thingset.thingset_can import ThingSet_CAN

own_id = 0x01
bms_id = 0x0A
mppt_id = 0x14


def pub_callback(src: int, id: int, data):
    '''Callback function for received Publication Frames'''
    print(f'Message from ID {src} -> {id}: {data}')


ts = ThingSet_CAN(if_name='can0', own_id=own_id)
ts.subscribe(bms_id)
ts.subscribe(mppt_id)
ts.setPubCallback(pub_callback)
ts.start()

print("Python ThingSet Client for CAN (Binary Mode)")
print("--------------------------------------------")

# WORKING  =====================================================

# GET
print("  > Get - INFO Path: " + str(ts.get(bms_id, 0x01)))
print("  > Get - INFO Path: " + str(ts.get(bms_id, 'info')))
print("  > Get - MEAS Path: " + str(ts.get(bms_id, 0x02)))
print("  > Get - MEAS Path: " + str(ts.get(bms_id, 'meas')))
print("  > Get - INPUT Path: " + str(ts.get(bms_id, 0x05)))
print("  > Get - CONF Path: " + str(ts.get(bms_id, 0x06)))
print("  > Get - can.Enable: " + str(ts.get(bms_id, 0xF6)))
print("  > Get - meas.Bat_V: " + str(ts.get(bms_id, 0x71)))
print("  > Get - meas.Cell_V: " + str(ts.get(bms_id, 0x80)))
print("  > Get - DeviceID: " + str(ts.get(bms_id, 0x1D)))

# PATCH
print("  > iPatch (bool) - Discharge disable: " + str(ts.patch(bms_id, 0x05, {0x61: False})))
print("  > iPatch (bool) - Discharge enable: " + str(ts.patch(bms_id, 0x05, {0x61: True})))
print("  > iPatch (string) - Password = abcd: " + str(ts.patch(bms_id, 0xEE, {0xEF: 'abcd'})))
print("   iPatch (int) - PcbDisSC_us = 200: " + str(ts.patch(bms_id, 0x06, {0x41: 200})))
print("   iPatch (bool) - .pub.can.enable = False: " + str(ts.patch(bms_id, 0xF5, {0xF6: False})))

# FETCH
print("  > Fetch - Request BatNom_Ah from CONF Path: " + str(ts.fetch(bms_id, 0x06, [0x31])))
print("  > Fetch - Request Array: " + str(ts.fetch(bms_id, 0x06, [0x31, 0x41])))

# POST - Execute Function
print("  > Post - print-registers: " + str(ts.post(bms_id, 0xEC, [])))
print("  > Post - print-register: " + str(ts.post(bms_id, 0xEA, [0x4B])))
print("  > Post - auth: " + str(ts.post(bms_id, 0xEE, ["maker456"])))
print("  > Post - auth: " + str(ts.post(bms_id, 0xEE, ["expert123"])))

# ISSUES =======================================================

# print("  > Fetch - MEAS item IDs: " + str(ts.fetch(bms_id, 0x02, 0xF7)))
# Returs: Error - Response too large (0xE1)

# print("  > Post - Append : " + str(ts.post(bms_id, 0x100, 0x74)))

# print("  > Get - .pub Path: " + str(ts.get(bms_id, 0x100)))
# returns: 1EDA010A 06 85 A2 18 F1 18 F5
# cbor2.loads(b'\xa2\x18\xf1\x18\xf5') -> premature end of stream (expected to read 1 bytes, got 0 instead)

# print("  > Get - serial: " + str(ts.get(bms_id, 0xF3)))
# Returns: 1EDA010A 01 85
# print("  > Get - can: " + str(ts.get(bms_id, 0xF7)))
# Returns: 1EDA010A 01 85

# print("  > Get - serial: " + str(ts.get(bms_id, 0xF1)))
# Returns: 1EDA010A 07 85 A2 18 F3 18 F2 F4
# cbor2.loads(b'\xa2\x18\xf3\x18\xf2\xf4') -> premature end of stream (expected to read 1 bytes, got 0 instead)
# print("  > Get - can: " + str(ts.get(bms_id, 0xF5)))
# Returns: 1EDA010A 07 85 A2 18 F7 18 F6 F5
# cbor2.loads(b'\xa2\x18\xf7\x18\xf6\xf5') -> premature end of stream (expected to read 1 bytes, got 0 instead)

# Fetch Names returns values not strings (diff from spec)
# print("  > Fetch - Names: " + str(ts.fetch(bms_id, 0x17, [0x40, 0x41])))
# returns: 1EDA010A 10 09 85 82 FA 00 00 00
#          1EDA010A 21 BE 18 C8

# ==============================================================

print("Exit with Ctrl+C ")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('interrupted!')

print("Latest BMS Pub. Data: " + str(ts.data[bms_id]))
print("Latest MPPT Pub. Data: " + str(ts.data[mppt_id]))
