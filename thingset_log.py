
import json
import time
from datetime import datetime

from thingset.cansocket import CANsocket
sock = CANsocket('can0')  # or other interface

mppt_id = 0x14
bms_id = 0xa

mppt_map = {
    0x71: 'Bat_V',
    0x72: 'Bat_A',
    0x76: 'SOC_pct',
    0x7C: 'ChgState',
    0x7D: 'DcdcState',
    0x80: 'Solar_V',
    0x81: 'Solar_A',
    0x89: 'Load_A',
    0x8B: 'LoadInfo',
    0x8C: 'UsbInfo',
    0x9F: 'ErrorFlags',
    0xA1: 'SolarInDay_Wh',
    0xA2: 'LoadOutDay_Wh',
    0xA3: 'BatChgDay_Wh',
    0xA4: 'BatDisDay_Wh',
    0xA5: 'Dis_Ah',
}

bms_map = {
    0x71: 'Bat_V',
    0x72: 'Bat_A',
    0x73: 'Bat_degC',
    0x74: 'IC_degC',
    0x7C: 'SOC_pct',
    0x7E: 'ErrorFlags',
    0x7F: 'BmsState',
    0x9A: 'CellAvg_V',
    0x9B: 'CellMin_V',
    0x9C: 'CellMax_V',
    0x9D: 'BalancingStatus',
}

mppt_data = {}
mppt_updated = False
mppt_file = open("data/%s_mppt.csv" % datetime.now().strftime("%Y%m%d_%H%M%S"), "a")

bms_data = {}
bms_updated = False
bms_file = open("data/%s_bms.csv" % datetime.now().strftime("%Y%m%d_%H%M%S"), "a")

last_update = int(time.time())

def csv_header(file, id_map):
    names = ['Timestamp_s']
    for key in id_map:
        names.append(id_map[key])
    file.write(','.join(names) + '\n')

def csv_data(file, id_map, timestamp, data):
    values = [str(timestamp)]
    for key in id_map:
        if id_map[key] in data:
            values.append(str(data[id_map[key]]))
        else:
            values.append('')
    file.write(','.join(values) + '\n')
    file.flush()

csv_header(mppt_file, mppt_map)
csv_header(bms_file, bms_map)

try:
    while True:
        frame = sock.receive()

        data_name = str(frame.dataobjectID)
        if frame.source == mppt_id and frame.dataobjectID in mppt_map:
            data_name = mppt_map[frame.dataobjectID]
            mppt_data[data_name] = frame.cbor
            mppt_updated = True
        elif frame.source == bms_id and frame.dataobjectID in bms_map:
            data_name = bms_map[frame.dataobjectID]
            bms_data[data_name] = frame.cbor
            bms_updated = True

        now = int(time.time())

        # store data in CSV file
        if now > last_update:
            try:
                print("BMS: Bat %.2fV %.2fA, Cells %.2fV < %.2fV < %.2fV, Err %d     " % ( \
                    bms_data['Bat_V'], bms_data['Bat_A'], bms_data['CellMin_V'], \
                    bms_data['CellAvg_V'], bms_data['CellMax_V'], bms_data['ErrorFlags']), end='' \
                )
            except:
                pass

            try:
                print("MPPT: Bat %.2fV %.2fA, Solar %.2fV, Load %.2fA, Err %d" % ( \
                    mppt_data['Bat_V'], mppt_data['Bat_A'], mppt_data['Solar_V'], \
                    mppt_data['Load_A'], mppt_data['ErrorFlags']) \
                )
            except:
                print("")
                #pass

            if mppt_updated:
                #print(json.dumps(mppt_data))
                csv_data(mppt_file, mppt_map, now, mppt_data)
                mppt_data = {}
                mppt_updated = False
            if bms_updated:
                #print(json.dumps(bms_data))
                csv_data(bms_file, bms_map, now, bms_data)
                bms_data = {}
                bms_updated = False
            last_update = now

except KeyboardInterrupt:
    mppt_file.close()
    bms_file.close
