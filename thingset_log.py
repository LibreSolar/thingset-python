import json
import time
from datetime import datetime

from thingset.thingset_can import ThingSet_CAN

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
    0x76: 'MOSFETs_degC',
    0x7C: 'SOC_pct',
    0x7E: 'ErrorFlags',
    0x7F: 'BmsState',
    0x9A: 'CellAvg_V',
    0x9B: 'CellMin_V',
    0x9C: 'CellMax_V',
    0x9D: 'BalancingStatus',
}

mppt_file = open("data/%s_mppt.csv" %
                 datetime.now().strftime("%Y%m%d_%H%M%S"), "a")

bms_file = open("data/%s_bms.csv" %
                datetime.now().strftime("%Y%m%d_%H%M%S"), "a")


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


ts = ThingSet_CAN(if_name='can0')
ts.subscribe(bms_id)
ts.subscribe(mppt_id)
ts.start()

csv_header(mppt_file, mppt_map)
csv_header(bms_file, bms_map)

last_update = int(time.time())

try:
    while True:

        time.sleep(1)
        now = int(time.time())

        try:
            bms_data = ThingSet_CAN.translate(ts.data[bms_id], bms_map)
            csv_data(bms_file, bms_map, now, bms_data)
            #print(json.dumps(bms_data))
            print("BMS: Bat %.2fV %.2fA, Cells %.2fV < %.2fV < %.2fV, Err %d" % (
                bms_data['Bat_V'], bms_data['Bat_A'], bms_data['CellMin_V'],
                bms_data['CellAvg_V'], bms_data['CellMax_V'], bms_data['ErrorFlags']), end=''
            )
        except KeyError as exc:
            #print(exc)
            pass

        try:
            mppt_data = ThingSet_CAN.translate(ts.data[mppt_id], mppt_map)
            csv_data(mppt_file, mppt_map, now, mppt_data)
            # print(json.dumps(mppt_data))
            print("MPPT: Bat %.2fV %.2fA, Solar %.2fV, Load %.2fA, Err %d" % (
                mppt_data['Bat_V'], mppt_data['Bat_A'], mppt_data['Solar_V'],
                mppt_data['Load_A'], mppt_data['ErrorFlags'])
            )
        except KeyError as exc:
            # print(exc)
            print("")
            


except KeyboardInterrupt:
    mppt_file.close()
    bms_file.close
