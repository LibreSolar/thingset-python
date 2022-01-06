## Send and receive message via ThingSet protocol over CAN

### Create CAN socket
``` shell
sudo modprobe vcan
sudo ip link add vcan0 type vcan
sudo ip link set vcan0 up
```

### Test socket
``` shell
candump -L vcan0
cansend vcan0 012#deadbeef
```

## prepare python env (not needed but advised)
In directory with requirements.txt:

``` shell
virtualenv -p python3 .thingset
source .thingset/bin/activate
pip install -r requirements.txt
```
You can skip the first two commands, then all python packages will be added to your computer's python installation! You can leave the environment simply with
``` shell
deactivate
```

## Usage:

### Initialization

```python
from thingset.thingset_can import ThingSet_CAN

# Define some addresses
own_id = 0x01
bms_id = 0x0A
mppt_id = 0x14

# Create ThingSet client object with CAN interface and source ID
ts = ThingSet_CAN(if_name='can0', own_id=own_id)
# Subscribe to publication messages of specific devices
ts.subscribe(bms_id)
ts.subscribe(mppt_id)
# Start reception process
rx_thread.start()
```

### Callback Mechanism

It is possible to register a callback function that is called on every received publication frame to process the frame directly after reception.

```python
def pub_callback(src:int, id:int, data):
    '''Callback function for received Publication Frames'''
    print(f'Message from ID {src} -> {id}: {data}')

ts.setPubCallback(pub_callback)
```

### Request API

* Return data is dependent on request type
  * can be:
    * status code (string)
    * bool
    * int
    * float
    * string
    * array (Python List)
    * map (Python Dictionary)

#### get

```python
# Retrieve all data from a path
meas_id = ts.get(bms_id, 0x02)))
meas_str = ts.get(bms_id, 'meas')))

# Retrieve single data items
deviceID = ts.get(bms_id, 0x1D)))
can_enable = ts.get(bms_id, 0xF6)))
bat_V = ts.get(bms_id, 0x71)))

# Retrieve array data items
cell_V = ts.get(bms_id, 0x80)))
```

#### fetch

```python
# fetch BatNom_Ah from CONF Path
batNom_Ah = ts.fetch(bms_id, 0x06, [0x31])

# fetch multiple items with an array
response = ts.fetch(bms_id, 0x06, [0x31, 0x41])
```

#### post

```python
# call print-registers function
response = ts.post(bms_id, 0xEC, [])

# call print-register function with argument
response = ts.post(bms_id, 0xEA, [0x4B])))

# Athenticate
response = ts.post(bms_id, 0xEE, ["maker456"])
response = ts.post(bms_id, 0xEE, ["expert123"])
```

#### patch

```python
# iPatch (bool) - can.enable = False
response = ts.patch(bms_id, 0xF5, {0xF6: False})
```
