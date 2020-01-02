#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import pathlib
import os
import time
import json

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

DEFAULT_KEY_DOWNTIME_MS = 50 # time a key is held down while typing (ms)
DEFAULT_KEY_INTERVAL_MS = 50 # time between keypresses while typing (ms)

# Source for codes: https://github.com/girst/hardpass-sendHID/blob/master/scancodes.c
# Another source: https://www.usb.org/sites/default/files/documents/hut1_12v2.pdf
# Modifiers: 0x01 Left Ctrl, 0x02 Left Shift, 0x04 Left Alt, 0x08 Left Meta, 0x10 Right Ctrl, 0x20 Right Shift, 0x40 Right Alt, 0x80 Right Meta
KEY_SCAN_CODES = {
    'thec64-mini-uk': {
        # With shift
        'A': b'\x04\x02',
        'B': b'\x05\x02',
        'C': b'\x06\x02',
        'D': b'\x07\x02',
        'E': b'\x08\x02',
        'F': b'\x09\x02',
        'G': b'\x0a\x02',
        'H': b'\x0b\x02',
        'I': b'\x0c\x02',
        'J': b'\x0d\x02',
        'K': b'\x0e\x02',
        'L': b'\x0f\x02',
        'M': b'\x10\x02',
        'N': b'\x11\x02',
        'O': b'\x12\x02',
        'P': b'\x13\x02',
        'Q': b'\x14\x02',
        'R': b'\x15\x02',
        'S': b'\x16\x02',
        'T': b'\x17\x02',
        'U': b'\x18\x02',
        'V': b'\x19\x02',
        'W': b'\x1a\x02',
        'X': b'\x1b\x02',
        'Y': b'\x1c\x02',
        'Z': b'\x1d\x02',
    
        # Without shift
        'a': b'\x04\x00',
        'b': b'\x05\x00',
        'c': b'\x06\x00',
        'd': b'\x07\x00',
        'e': b'\x08\x00',
        'f': b'\x09\x00',
        'g': b'\x0a\x00',
        'h': b'\x0b\x00',
        'i': b'\x0c\x00',
        'j': b'\x0d\x00',
        'k': b'\x0e\x00',
        'l': b'\x0f\x00',
        'm': b'\x10\x00',
        'n': b'\x11\x00',
        'o': b'\x12\x00',
        'p': b'\x13\x00',
        'q': b'\x14\x00',
        'r': b'\x15\x00',
        's': b'\x16\x00',
        't': b'\x17\x00',
        'u': b'\x18\x00',
        'v': b'\x19\x00',
        'w': b'\x1a\x00',
        'x': b'\x1b\x00',
        'y': b'\x1c\x00',
        'z': b'\x1d\x00',
    
        # Numbers
        '1': b'\x1e\x00',
        '2': b'\x1f\x00',
        '3': b'\x20\x00',
        '4': b'\x21\x00',
        '5': b'\x22\x00',
        '6': b'\x23\x00',
        '7': b'\x24\x00',
        '8': b'\x25\x00',
        '9': b'\x26\x00',
        '0': b'\x27\x00',
    
        # Special keys above numbers (C-64)
        '!': b'\x1e\x02',
        '"': b'\x1f\x02',
        '#': b'\x32\x00',
        '$': b'\x21\x02',
        '%': b'\x22\x02',
        '&': b'\x24\x02',
        #'': b'\x23\x02', # arrow up
        '\'': b'\x34\x00',
        '(': b'\x26\x02', 
        ')': b'\x27\x02', 
    
        # Control keys
        '\n': b'\x28\x00', # enter
        '\x1b': b'\x29\x00', # escape
        '\b': b'\x2a\x00', # backspace
        '\t': b'\x2b\x00', # tab
        ' ': b'\x2c\x00', # space

        # Graphics keys
    
        # Other special keys (C-64)
        '=': b'\x2e\x00',
        ':': b'\x33\x20', # with shift
        ';': b'\x33\x00',
        '@': b'\x31\x00',
        '*': b'\x25\x20', # with shift
        ',': b'\x36\x00',
        '.': b'\x37\x00',
        '/': b'\x38\x00',
        '[': b'\x2f\x00',
        ']': b'\x30\x00',
        '<': b'\x36\x20', # with shift
        '>': b'\x37\x20', # with shift
        '?': b'\x38\x20', # with shift
        #'': b'\x35\x00', # arrow left
        '+': b'\x2e\x20',
        '-': b'\x2d\x00',
    },
    'thec64': {
        # With shift
        'A': b'\x04\x02',
        'B': b'\x05\x02',
        'C': b'\x06\x02',
        'D': b'\x07\x02',
        'E': b'\x08\x02',
        'F': b'\x09\x02',
        'G': b'\x0a\x02',
        'H': b'\x0b\x02',
        'I': b'\x0c\x02',
        'J': b'\x0d\x02',
        'K': b'\x0e\x02',
        'L': b'\x0f\x02',
        'M': b'\x10\x02',
        'N': b'\x11\x02',
        'O': b'\x12\x02',
        'P': b'\x13\x02',
        'Q': b'\x14\x02',
        'R': b'\x15\x02',
        'S': b'\x16\x02',
        'T': b'\x17\x02',
        'U': b'\x18\x02',
        'V': b'\x19\x02',
        'W': b'\x1a\x02',
        'X': b'\x1b\x02',
        'Y': b'\x1c\x02',
        'Z': b'\x1d\x02',
    
        # Without shift
        'a': b'\x04\x00',
        'b': b'\x05\x00',
        'c': b'\x06\x00',
        'd': b'\x07\x00',
        'e': b'\x08\x00',
        'f': b'\x09\x00',
        'g': b'\x0a\x00',
        'h': b'\x0b\x00',
        'i': b'\x0c\x00',
        'j': b'\x0d\x00',
        'k': b'\x0e\x00',
        'l': b'\x0f\x00',
        'm': b'\x10\x00',
        'n': b'\x11\x00',
        'o': b'\x12\x00',
        'p': b'\x13\x00',
        'q': b'\x14\x00',
        'r': b'\x15\x00',
        's': b'\x16\x00',
        't': b'\x17\x00',
        'u': b'\x18\x00',
        'v': b'\x19\x00',
        'w': b'\x1a\x00',
        'x': b'\x1b\x00',
        'y': b'\x1c\x00',
        'z': b'\x1d\x00',
    
        # Numbers
        '1': b'\x1e\x00',
        '2': b'\x1f\x00',
        '3': b'\x20\x00',
        '4': b'\x21\x00',
        '5': b'\x22\x00',
        '6': b'\x23\x00',
        '7': b'\x24\x00',
        '8': b'\x25\x00',
        '9': b'\x26\x00',
        '0': b'\x27\x00',
    
        # Special keys above numbers (C-64)
        '!': b'\x1e\x02',
        '"': b'\x1f\x02',
        '#': b'\x20\x02',
        '$': b'\x21\x02',
        '%': b'\x22\x02',
        '&': b'\x23\x02',
        '\'': b'\x24\x02',
        '(': b'\x25\x02',
        ')': b'\x26\x02',
    
        # Control keys
        '\n': b'\x28\x00', # enter
        '\x1b': b'\x29\x00', # escape
        '\b': b'\x2a\x00', # backspace
        '\t': b'\x2b\x00', # tab
        ' ': b'\x2c\x00', # space
    
        # Graphics keys
    
        # Other special keys (C-64)
        '=': b'\x2e\x00',
        ':': b'\x2f\x00',
        ';': b'\x30\x00',
        '@': b'\x31\x00',
        #'@': b'\x32\x00', # same as 31
        '*': b'\x33\x00',
        #'': b'\x34\x00', # arrow up
        #'': b'\x35\x00', # arrow left
        ',': b'\x36\x00',
        '.': b'\x37\x00',
        '/': b'\x38\x00',
        '[': b'\x2f\x20', # with shift
        ']': b'\x30\x20', # with shift
        '<': b'\x36\x20', # with shift
        '>': b'\x37\x20', # with shift
        '?': b'\x38\x20', # with shift
        '+': b'\x57\x00', # keypad +
        '-': b'\x56\x00', # keypad -
    },
}

DEFAULT_KEYMAP = 'thec64-mini-uk'

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

def send_hid_key_down(key, keymap):
    try:
        (scancode, modifier) = KEY_SCAN_CODES[keymap][key]
    except KeyError:
        print('Skip unknown scancode for %s' % key)
        return (-1, -1)
    print('SCANCODE %x %x' % (scancode, modifier), flush=True)
    with open(DEV_HID_PATH, 'wb') as f: f.write(b'%c\x00%c\x00\x00\x00\x00\x00' % (modifier, scancode))
    return (scancode, modifier)

def send_hid_key_up():
    with open(DEV_HID_PATH, 'wb') as f: f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')

# Send specified keypresses, with each key held down for downtime seconds, with interval seconds between keypresses
def send_hid_keypresses(text, downtime_ms, interval_ms, keymap):
    downtime_s = float(downtime_ms) / 1000
    interval_s = float(interval_ms) / 1000
    scancodes = []
    for index, key in enumerate(text):
        if index > 0:
            time.sleep(interval_s)
        scancode = send_hid_key_down(key, keymap)
        scancodes.append(scancode)
        time.sleep(downtime_s)
        send_hid_key_up()
    return scancodes

class HIDGatewayRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        print('Parsed URL query', parsed_path.query)
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
        # Use Unicode for key, it's mapped to bytes later
        key = ''.join(query.get('key', []))
        downtime_ms = int(''.join(query.get('downtime', [str(DEFAULT_KEY_DOWNTIME_MS)])))
        interval_ms = int(''.join(query.get('interval', [str(DEFAULT_KEY_INTERVAL_MS)])))
        keymap = ''.join(query.get('keymap', [])) or DEFAULT_KEYMAP
        scancodes = send_hid_keypresses(key, downtime_ms, interval_ms, keymap)
        return json.dumps({
            'scancodes': scancodes,
        }) + '\n'

    # Invoke multiple keypresses
    def get_type(self, query):
        # Use Unicode for text, it's mapped to bytes later
        text = ''.join(query.get('text', []))
        enter = False if ''.join(query.get('enter', [])) == '0' else True
        if enter:
            text += '\n'
        downtime_ms = int(''.join(query.get('downtime', [str(DEFAULT_KEY_DOWNTIME_MS)])))
        interval_ms = int(''.join(query.get('interval', [str(DEFAULT_KEY_INTERVAL_MS)])))
        keymap = ''.join(query.get('keymap', [])) or DEFAULT_KEYMAP
        scancodes = send_hid_keypresses(text, downtime_ms, interval_ms, keymap)
        return json.dumps({
            'scancodes': scancodes,
        }) + '\n'

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
