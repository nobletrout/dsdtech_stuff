#!/usr/bin/env python
"""
Scan/Discovery
--------------

Example showing how to scan for BLE devices.

Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>

"""

import argparse
import asyncio
import threading
import time
import struct
import inputimeout

from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic

PASSWORD = [0x04,0xD2]
programContinues = False



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
        await client.start_notify("0000ffe1-0000-1000-8000-00805f9b34fb", callback)
        time.sleep(5)
        await asyncio.gather(
            relayStatusThread(client),
            switch_loop(client),
        )
        

def select_port():
    try:
        return (int(inputimeout.inputimeout(prompt="Select a port to toggle [1-4]: ", timeout=3))-1)
    except:
        raise ValueError

async def switch_loop(client): 
    global port_table, programContinues
    connected = True
    while connected and client.is_connected:
        await client.write_gatt_char("0000ffe1-0000-1000-8000-00805f9b34fb", message_prep([0x05,0x00]))
        print(port_table)
        try:
            port_number = await asyncio.to_thread(select_port)
        except ValueError:
            continue
        if port_number > 3:
            connected = False
        if port_number > 3 or port_number < 0:
            continue
        write_value = enum_ports[port_number][not port_table[port_number]]
        port_table[port_number] = not port_table[port_number]
        await flipPort(client, "0000ffe1-0000-1000-8000-00805f9b34fb", message_prep(write_value))
    programContinues = False


async def relayStatusThread(client):
    while programContinues:
        #print("I am thread")
        await client.write_gatt_char("0000ffe1-0000-1000-8000-00805f9b34fb", message_prep([0x05,0x00]), response=False)
        await asyncio.sleep(5)


def checkXor(somebytes):
    xor_byte = somebytes[0]
    for i in somebytes[1:-1]:
        xor_byte = xor_byte ^ i
    return (xor_byte == somebytes[-1])

# returned bytes are sent 1 byte at a time
# thanks guys
returnbytes = []
messageState = False
def callback(sender: BleakGATTCharacteristic, data: bytearray):
    global returnbytes, messageState
    if messageState == False and data[0] == 0xA1:
        messageState = True
        returnbytes = []
    if messageState == True and data[0] == 0xAA:
        if checkXor(returnbytes):
            returnbytes += data
            messageState = False
            updatePortStatus(returnbytes)
            #print(returnbytes)
    if messageState:
        returnbytes += data

def updatePortStatus(somebytes):
    global port_table
    # if this is a port status message
    if somebytes[0:2] == [0xA1, 0x05]:
        for idx, i in enumerate(reversed(somebytes[3:3+somebytes[2]])):
            port_table[idx] = (i == 1)

async def flipPort(client, uuid, write_value):
    await client.write_gatt_char(uuid, write_value, response=False)


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
