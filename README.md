# Raspberry Pi Zero HID Gateway for OTG USB
Kenneth Falck <kennu@iki.fi> 2019

## Overview

The zero-hid-gateway works on Raspberry Pi Zero. It acts as a virtual USB HID
device and provides a REST API for emitting keypresses.

Currently the keycodes are mapped for TheC64, but you can connect any device
you want to send keypresses to, to the Raspberry Pi Zero's USB port.

## REST API

GET /keypress?key=x&downtime=n

Use /keypress to emit a single keypress. Downtime specifies how long the key
will be down before it is released. The default value for downtime is 50ms.

GET /type?text=xxx&downtime=n&interval=n

Use /type to emit a sequence of keypresses. Downtime specifies how long keys
are held down and interval specifies the delay between keypresses. The default
value for both is 50ms.
