from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST
import sys, datetime
import asyncio
from bleak import BleakClient

GATT_CHARACTERISTIC_UUID_TX = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
GATT_CHARACTERISTIC_UUID_RX = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'

address = sys.argv[1]
dest = sys.argv[2]
port = int(sys.argv[3])
buffer = bytearray()

s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

def on_value(voltage, current, wattage, timestamp):
    print("{3} {0:.1f}[V] {1:.1f}[mA] {2:.1f}[W]".format(voltage, current, wattage, timestamp))
    msg = '{ "voltage":' + str(voltage) + ',"current":' + str(current) + ',"power":' + str(wattage) + '}'
    s.sendto(msg.encode(), (dest, port))   
 
def on_notify(sender, data: bytearray):
    global buffer
    # print("{0}: {1}".format(sender, data))
    if data[0] == 0xaa:
        global buffer
        buffer[:] = data
    else:
        buffer += bytearray(data) 
        v = int.from_bytes(buffer[5:11], 'little') / (16**6)
        c = int.from_bytes(buffer[11:17], 'little') / (32**6) * 1000
        w = int.from_bytes(buffer[17:23], 'little') / (16**6)
        t = datetime.datetime(1900+buffer[28], buffer[27]+1, *buffer[26:22:-1])
        on_value(v, c, w, t)

async def run(loop):
    client = BleakClient(address)
    await client.connect()
    print("connected!")

    services = await client.get_services()
    print("get_services")

    tx = services.get_characteristic(GATT_CHARACTERISTIC_UUID_TX)
    rx = services.get_characteristic(GATT_CHARACTERISTIC_UUID_RX)    
    print("get_characteristics")

    await client.start_notify(rx, on_notify)
    print("start_notify")

    command = bytearray.fromhex('aa000108b3')
    while True:
        await client.write_gatt_char(tx, command, True)
        # print("write_gatt_char")
    
        await asyncio.sleep(1.0, loop=loop)

    await client.stop_notify(rx)
    print("stop_notify")
   
loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
