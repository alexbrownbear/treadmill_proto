from __future__ import print_function

import logging

logging.basicConfig()
logging.getLogger('pygatt').setLevel(logging.INFO)

import binascii
import pygatt

import os
import sys

ADDRESS = "FF:FF:00:00:95:BD"
# Many devices, e.g. Fitbit, use random addressing - this is required to
# connect.
ADDRESS_TYPE = pygatt.BLEAddressType.random

address = ADDRESS

# if os.environ['BACKEND'] == "gatttool":
#     adapter = pygatt.GATTToolBackend(hci_device="hci1")
# else:
#     adapter = pygatt.BGAPIBackend()
adapter = pygatt.GATTToolBackend(hci_device="hci0")
adapter.start()

devices = adapter.scan(run_as_root=True, timeout=3)
# for device in devices:
#     address = device['address']
try:
    print("Connecting...")
    device = adapter.connect(ADDRESS) #, address_type=ADDRESS_TYPE)
    print("Connected")

    for uuid in device.discover_characteristics().keys():
        if str(uuid) == "0000fff1-0000-1000-8000-00805f9b34fb":
            print("Skipping evil UUID %s" % uuid)
            #continue
        try:
            print("Read UUID %s: %s" % (uuid, binascii.hexlify(device.char_read(uuid))))
        except:
            print('Read failed ++')
            # continue
        else:
            break
    device.disconnect()
except pygatt.exceptions.NotConnectedError:
    print("failed to connect to %s" % address)
    #continue
#helse:
#    break
# else:
#     print("failed to connect and read from any device")
#     sys.exit(1)