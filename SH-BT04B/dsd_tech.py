#!/usr/bin/env python
"""
Scan/Discovery
--------------

Example showing how to scan for BLE devices.

Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import argparse
import asyncio

from bleak import BleakScanner, BleakClient

PASSWORD = [0x04,0xD2]


# True = on, False = off
enum_ports = {
    0:{True: [0x01,0x01], False:[0x02,0x01]},
    1:{True: [0x01,0x02], False:[0x02,0x02]},
    2:{True: [0x01,0x03], False:[0x02,0x03]},
    3:{True: [0x01,0x04], False:[0x02,0x04]}
}

port_table = [ False, False, False, False ]
num_ports = 4

def main():
    deviceList = asyncio.get_event_loop().run_until_complete(findDSDTech())
    print("Found %d DSD Tech Devices" % len(deviceList))
    
    if len(deviceList) == 0:
        print("quitting since nothing found")
        return(0)

    elif len(deviceList) == 1:
        myDevice = deviceList[0]
    else:
        print("Too many devices, picker not implemented yet")
        return(1)

    stuff = asyncio.get_event_loop().run_until_complete(noodleAbout(myDevice[0]))

# this version need to XOR the bytes and temrinate with 0xAA
def message_prep(myArray):
    xor_byte = 0
    start_array = [0xA1] + PASSWORD + myArray
    for i in start_array:
        xor_byte = xor_byte ^ i
    returnArray = start_array + [xor_byte, 0xAA]
    return(bytes(returnArray))


async def noodleAbout(device):
    async with BleakClient(device) as client:
        print("Here are some services and characteristics")
        for service in client.services:
            print("Service: %s " % service.uuid)
            for characteristic in service.characteristics:
                print("\tCharacteristic: %s " % characteristic.uuid)
                print("\t\tProperties: %s" % characteristic.properties)
        connected = True
        while connected and client.is_connected:
            try:
                port_number = int(input("Select a port to toggle [1-4]: ")) - 1
            except ValueError:
                continue
            if port_number > 3:
                connected = False
            if port_number > 3 or port_number < 0:
                continue
            port_table[port_number] = not port_table[port_number]
            write_value = enum_ports[port_number][port_table[port_number]]
#            message_prep(write_value)
            await flipPort(client, "0000ffe1-0000-1000-8000-00805f9b34fb", message_prep(write_value))

async def flipPort(client, uuid, write_value):
    await client.write_gatt_char(uuid, write_value)
            

async def findDSDTech():
    print("looking for DSD Tech devices")
    devices = await BleakScanner.discover(
        return_adv=True)
    print(devices.values())
    deviceList = []
    for d, a in devices.values():
        if a.local_name == "DSD TECH":
            deviceList.append((d,a))
    return(deviceList)
 

if __name__ == "__main__":
  #  parser = argparse.ArgumentParser()

   # args = parser.parse_args()

    exit(main())
