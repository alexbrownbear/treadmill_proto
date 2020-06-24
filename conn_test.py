import pygatt
from binascii import hexlify
import pprint
import time
from tph_modified import *

adapter = pygatt.GATTToolBackend()

CLIENT_CHARACTERISTIC_CONFIG = "00002902-0000-1000-8000-00805f9b34fb"
UUID_HEART_RATE_MEASUREMENT = "00002a37-0000-1000-8000-00805f9b34fb"
UUID_ISSC_CHAR_RX = "0000fff1-0000-1000-8000-00805f9b34fb"
UUID_ISSC_CHAR_TX = "0000fff2-0000-1000-8000-00805f9b34fb"
UUID_TX_RX_WITHOUT_RES = '00010203-0405-0607-0809-0a0b0c0d2b12'

FIRST_AGREEMENT = bytearray([0x08, 0x01, 0x86])
SEC_AGREEMENT = bytearray([0xA9, 0x08, 0x01, 0x86, 0x26])

tph = TreadmillProtocolHelper()
tph.agreement_status = 2

data_received = None
def handle_data(handle, value):
    # print('Received data %s' % hexlify(value))
    global data_received
    data_received = value

device = None
try:
    adapter.start(reset_on_start=True)
    device = adapter.connect('ff:ff:00:00:95:bd')
    dev_characts = device.discover_characteristics()
    print(pprint.pformat(dev_characts))
    device.char_write(UUID_ISSC_CHAR_TX, FIRST_AGREEMENT, wait_for_response=False)
    # time.sleep(1)
    device.char_write(UUID_ISSC_CHAR_TX, SEC_AGREEMENT, wait_for_response=False)
    # time.sleep(1)
    device.subscribe(UUID_ISSC_CHAR_RX, callback=handle_data)
    # time.sleep(1)
    # value = device.char_read(UUID_ISSC_CHAR_RX)
    # print(value)
    repeat = 5
    while repeat:
        time.sleep(1)
        repeat -= 1
        if data_received is not None:
            print(hexlify(data_received))
            response = tph.manage_data(np.array(data_received, dtype=np.int8))
            # print('response %s %s' % (response, SEC_AGREEMENT))

            device.char_write(UUID_ISSC_CHAR_TX, response, wait_for_response=False)
            data_received = None
        else:
            print('....')
    device.unsubscribe(UUID_ISSC_CHAR_RX)
finally:
    # device.unsubscribe(UUID_ISSC_CHAR_RX)
    adapter.stop()
    adapter.reset()
