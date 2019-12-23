#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import pathlib
import os

SYS_DEVICE_PATH = '/sys/kernel/config/usb_gadget/zerohidgateway'
SYS_STRINGS_PATH = '%s/strings/0x409' % (SYS_DEVICE_PATH)
SYS_CONFIG_STRINGS_PATH = '%s/configs/c.1/strings/0x409' % (SYS_DEVICE_PATH)
SYS_CONFIG_PATH = '%s/configs/c.1/strings/0x409/configuration' % (SYS_DEVICE_PATH)
SYS_CONFIG_C1_PATH = '%s/configs/c.1' % (SYS_DEVICE_PATH)
SYS_CONFIG_C1_HID_PATH = '%s/configs/c.1/hid.usb0' % (SYS_DEVICE_PATH)
SYS_HID_PATH = '%s/functions/hid.usb0' % (SYS_DEVICE_PATH)
SYS_UDC_PATH = '/sys/class/udc'
VENDOR_ID = '0x1d6b' # Linux Foundation
PRODUCT_ID = '0x0104' # Multifunction Composite Gadget
VERSION_ID = '0x0100'
USB_ID = '0x0200'
SERIAL_NUMBER = 'fedcba9876543210'
MANUFACTURER_NAME = 'Kenneth Falck'
PRODUCT_NAME = 'Zero HID Gateway'
CONFIG_1 = 'Config 1: ECM network'
MAX_POWER = '250'
HID_PROTOCOL = '1'
HID_SUBCLASS = '1'
HID_REPORT_LENGTH = '8'
HID_REPORT_DESC = '\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01' +\
                  '\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x05\x75\x01' +\
                  '\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x03\x95\x06' +\
                  '\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0'

class HIDGatewayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf8')
        self.end_headers()
        message = '404 Not Found\n'
        self.wfile.write(bytes(message, 'utf8'))

# Initialize HID device, based on instructions at https://www.isticktoit.net/?p=1383
def initialize_hid_device():
    if os.path.exists(SYS_DEVICE_PATH):
        print('HID device already exists at %s' % (SYS_DEVICE_PATH), flush=True)
        return

    print('Creating HID device in %s' % (SYS_DEVICE_PATH), flush=True)
    pathlib.Path(SYS_DEVICE_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/idVendor' % (SYS_DEVICE_PATH), 'w') as f: f.write('%s\n' % (VENDOR_ID))
    with open('%s/idProduct' % (SYS_DEVICE_PATH), 'w') as f: f.write('%s\n' % (PRODUCT_ID))
    with open('%s/bcdDevice' % (SYS_DEVICE_PATH), 'w') as f: f.write('%s\n' % (VERSION_ID))
    with open('%s/bcdUSB' % (SYS_DEVICE_PATH), 'w') as f: f.write('%s\n' % (USB_ID))

    pathlib.Path(SYS_STRINGS_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/serialnumber' % (SYS_STRINGS_PATH), 'w') as f: f.write('%s\n' % (SERIAL_NUMBER))
    with open('%s/manufacturer' % (SYS_STRINGS_PATH), 'w') as f: f.write('%s\n' % (MANUFACTURER_NAME))
    with open('%s/product' % (SYS_STRINGS_PATH), 'w') as f: f.write('%s\n' % (PRODUCT_NAME))

    pathlib.Path(SYS_CONFIG_STRINGS_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/configuration' % (SYS_CONFIG_STRINGS_PATH), 'w') as f: f.write('%s\n' % (CONFIG_1))
    with open('%s/MaxPower' % (SYS_CONFIG_C1_PATH), 'w') as f: f.write('%s\n' % (MAX_POWER))

    # HID specific configuration
    pathlib.Path(SYS_HID_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/protocol' % (SYS_HID_PATH), 'w') as f: f.write('%s\n' % (HID_PROTOCOL))
    with open('%s/subclass' % (SYS_HID_PATH), 'w') as f: f.write('%s\n' % (HID_SUBCLASS))
    with open('%s/report_length' % (SYS_HID_PATH), 'w') as f: f.write('%s\n' % (HID_REPORT_LENGTH))
    with open('%s/report_desc' % (SYS_HID_PATH), 'w') as f: f.write(HID_REPORT_DESC)
    os.symlink(SYS_HID_PATH, SYS_CONFIG_C1_HID_PATH)
    # End HID specific configuration

    files = os.listdir(SYS_UDC_PATH)
    with open('%s/UDC' % (SYS_DEVICE_PATH), 'w') as f: f.write('%s\n' % (' '.join(files)))

def main():
    print('Zero HID Gateway by Kenneth Falck <kennu@iki.fi> 2019', flush=True)
    initialize_hid_device()
    server_address = os.environ.get('HOST', '0.0.0.0')
    server_port = int(os.environ.get('PORT', '8088'))
    server = HTTPServer((server_address, server_port), HIDGatewayRequestHandler)
    print('Starting HTTP server at %s:%s' % (server_address, server_port), flush=True)
    server.serve_forever()

if __name__ == '__main__':
    main()
