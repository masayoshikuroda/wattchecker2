#!/usr/bin/env python3
# coding=utf-8
import sys
import datetime
from argparse import ArgumentParser
from socket import socket, AF_INET, SOCK_DGRAM
from socket import SOL_SOCKET, SO_BROADCAST
import asyncio
from bleak import BleakClient

GATT_CHARACTERISTIC_UUID_TX = '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
GATT_CHARACTERISTIC_UUID_RX = '6e400003-b5a3-f393-e0a9-e50e24dcca9e'

argparser =  ArgumentParser(description='Connect BTWATTCH2 via bluetooth and broadcast measured values via UDP.')
argparser.add_argument('-d', '--dest', type=str,   dest='dest', default='255.255.255.255', help='destination mac address to broadcast')
argparser.add_argument('-p', '--port', type=int,   dest='port', default=6667,              help='destination port number to broadcast')
argparser.add_argument('-s', '--sec',  type=float, dest='sec',  default=1.0,               help='measurement interval') 
argparser.add_argument('-v', '--verbose',          dest='verbose', action='store_true',    help='dump result to stdout')
argparser.add_argument('id',           type=str,                                           help='device mac addres to connect')
args = argparser.parse_args()

id = args.id
dest = args.dest
port = args.port
sec = args.sec
verbose = args.verbose

buffer = bytearray()

s = socket(AF_INET, SOCK_DGRAM)
s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

def on_value(voltage, current, wattage, timestamp):
    if verbose:
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
    client = BleakClient(id)
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
    
        await asyncio.sleep(sec, loop=loop)

    await client.stop_notify(rx)
    print("stop_notify")
   
loop = asyncio.get_event_loop()
loop.run_until_complete(run(loop))
