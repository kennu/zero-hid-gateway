#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import pathlib
import os
import time

SYS_DEVICE_PATH = '/sys/kernel/config/usb_gadget/zerohidgateway'
SYS_STRINGS_PATH = '%s/strings/0x409' % (SYS_DEVICE_PATH)
SYS_CONFIG_STRINGS_PATH = '%s/configs/c.1/strings/0x409' % (SYS_DEVICE_PATH)
SYS_CONFIG_PATH = '%s/configs/c.1/strings/0x409/configuration' % (SYS_DEVICE_PATH)
SYS_CONFIG_C1_PATH = '%s/configs/c.1' % (SYS_DEVICE_PATH)
SYS_CONFIG_C1_HID_PATH = '%s/configs/c.1/hid.usb0' % (SYS_DEVICE_PATH)
SYS_HID_PATH = '%s/functions/hid.usb0' % (SYS_DEVICE_PATH)
SYS_UDC_PATH = '/sys/class/udc'
DEV_HID_PATH = '/dev/hidg0'

VENDOR_ID = b'0x1d6b' # Linux Foundation
PRODUCT_ID = b'0x0104' # Multifunction Composite Gadget
VERSION_ID = b'0x0100'
USB_ID = b'0x0200'
SERIAL_NUMBER = b'fedcba9876543210'
MANUFACTURER_NAME = b'Kenneth Falck'
PRODUCT_NAME = b'Zero HID Gateway'
CONFIG_1 = b'Config 1: ECM network'
MAX_POWER = b'250'
HID_PROTOCOL = b'1'
HID_SUBCLASS = b'1'
HID_REPORT_LENGTH = b'8'
HID_REPORT_DESC = b'\x05\x01\x09\x06\xa1\x01\x05\x07\x19\xe0\x29\xe7\x15\x00\x25\x01' +\
                  b'\x75\x01\x95\x08\x81\x02\x95\x01\x75\x08\x81\x03\x95\x05\x75\x01' +\
                  b'\x05\x08\x19\x01\x29\x05\x91\x02\x95\x01\x75\x03\x91\x03\x95\x06' +\
                  b'\x75\x08\x15\x00\x25\x65\x05\x07\x19\x00\x29\x65\x81\x00\xc0'

DEFAULT_KEY_DOWNTIME_MS = 300 # time a key is held down while typing (ms)
DEFAULT_KEY_INTERVAL_MS = 300 # time between keypresses while typing (ms)

# Initialize HID device, based on instructions at https://www.isticktoit.net/?p=1383
def initialize_hid_device():
    if os.path.exists(SYS_DEVICE_PATH):
        print('HID device already exists at %s' % (SYS_DEVICE_PATH), flush=True)
        return

    print('Creating HID device in %s' % (SYS_DEVICE_PATH), flush=True)
    pathlib.Path(SYS_DEVICE_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/idVendor' % (SYS_DEVICE_PATH), 'wb') as f: f.write(b'%s\n' % (VENDOR_ID))
    with open('%s/idProduct' % (SYS_DEVICE_PATH), 'wb') as f: f.write(b'%s\n' % (PRODUCT_ID))
    with open('%s/bcdDevice' % (SYS_DEVICE_PATH), 'wb') as f: f.write(b'%s\n' % (VERSION_ID))
    with open('%s/bcdUSB' % (SYS_DEVICE_PATH), 'wb') as f: f.write(b'%s\n' % (USB_ID))

    pathlib.Path(SYS_STRINGS_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/serialnumber' % (SYS_STRINGS_PATH), 'wb') as f: f.write(b'%s\n' % (SERIAL_NUMBER))
    with open('%s/manufacturer' % (SYS_STRINGS_PATH), 'wb') as f: f.write(b'%s\n' % (MANUFACTURER_NAME))
    with open('%s/product' % (SYS_STRINGS_PATH), 'wb') as f: f.write(b'%s\n' % (PRODUCT_NAME))

    pathlib.Path(SYS_CONFIG_STRINGS_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/configuration' % (SYS_CONFIG_STRINGS_PATH), 'wb') as f: f.write(b'%s\n' % (CONFIG_1))
    with open('%s/MaxPower' % (SYS_CONFIG_C1_PATH), 'wb') as f: f.write(b'%s\n' % (MAX_POWER))

    # HID specific configuration
    pathlib.Path(SYS_HID_PATH).mkdir(parents=True, exist_ok=True)
    with open('%s/protocol' % (SYS_HID_PATH), 'wb') as f: f.write(b'%s\n' % (HID_PROTOCOL))
    with open('%s/subclass' % (SYS_HID_PATH), 'wb') as f: f.write(b'%s\n' % (HID_SUBCLASS))
    with open('%s/report_length' % (SYS_HID_PATH), 'wb') as f: f.write(b'%s\n' % (HID_REPORT_LENGTH))
    with open('%s/report_desc' % (SYS_HID_PATH), 'wb') as f: f.write(HID_REPORT_DESC)
    os.symlink(SYS_HID_PATH, SYS_CONFIG_C1_HID_PATH)
    # End HID specific configuration

    files = os.listdir(SYS_UDC_PATH)
    with open('%s/UDC' % (SYS_DEVICE_PATH), 'wb') as f: f.write(b'%s\n' % (bytes(' '.join(files), 'utf8')))

def send_hid_key_down(key):
    print('KEY DOWN %s' % (key), flush=True)
    with open(DEV_HID_PATH, 'wb') as f: f.write(b'\x00\x00\x04\x00\x00\x00\x00\x00')

def send_hid_key_up(key):
    print('KEY UP %s' % (key), flush=True)
    with open(DEV_HID_PATH, 'wb') as f: f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')

# Send specified keypresses, with each key held down for downtime seconds, with interval seconds between keypresses
def send_hid_keypresses(text, downtime_ms, interval_ms):
    downtime_s = float(downtime_ms) / 1000
    interval_s = float(interval_ms) / 1000
    for index, key in enumearte(text):
        if index > 0:
            time.sleep(interval_s)
        send_hid_key_down(key)
        time.sleep(downtime_s)
        send_hid_key_up(key)

class HIDGatewayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        if parsed_path.path == '/keypress':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            message = self.get_keypress(query)
            self.wfile.write(bytes(message, 'utf8'))
        elif parsed_path.path == '/type':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            message = self.get_type(query)
            self.wfile.write(bytes(message, 'utf8'))
        else:
            self.send_error(404, '404 Not Found')

    # Invoke a single keypress (down, up)
    def get_keypress(self, query):
        key = bytes(''.join(query.get('key', [])), 'utf8')
        downtime_ms = int(''.join(query.get('downtime', [str(DEFAULT_KEY_DOWNTIME_MS)])))
        interval_ms = int(''.join(query.get('interval', [str(DEFAULT_KEY_INTERVAL_MS)])))
        print('get_keypress %s' % (query))
        send_hid_keypresses(key, downtime_ms, interval_ms)
        return '{}\n'

    # Invoke multiple keypresses
    def get_type(self, query):
        text = bytes(''.join(query.get('text', [])), 'utf8')
        enter = False if ''.join(query.get('enter', [])) == '0' else True
        if enter:
            text += b'\r'
        downtime_ms = int(''.join(query.get('downtime', [str(DEFAULT_KEY_DOWNTIME_MS)])))
        interval_ms = int(''.join(query.get('interval', [str(DEFAULT_KEY_INTERVAL_MS)])))
        print('get_type %s %s' % (text, enter))
        send_hid_keypresses(text, downtime_ms, interval_ms)
        return '{}\n'

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
