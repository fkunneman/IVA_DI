from typing import Dict
import time
import usb.core
import sys

LED_ID_VENDOR = 0xD209
LED_ID_PRODUCT = 0x1500

# Update with the physical LED number
LED_GREEN = 1
LED_YELLOW = 2
LED_RED = 3
LED_BLUE = 4

dev = usb.core.find(idVendor=LED_ID_VENDOR, idProduct=LED_ID_PRODUCT)

if dev is None:
    print("LED device not attached")
    sys.quit()

# disconnect if attached
if dev.is_kernel_driver_active(0):
    try:
        dev.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detach kernel driver from interface")

# These values could be found in pacdrive.c
# https://github.com/katie-snow/Ultimarc-linux/blob/master/src/libs/pacdrive.c


def convert_led_map(leds: Dict[int, bool]):
    # LEDs and whether they are on;
    # idx is one-based (the number on the board)

    # first two are always 0
    vals = [0] * 4

    # third is used for higher number LEDs 9-16
    # fourth is used for lower number LEDs 1-8
    for idx, on in leds.items():
        if idx < 9:
            if on:
                vals[3] |= 2 ** (idx - 1)
        else:
            if on:
                vals[2] |= 2 ** (idx - 9)

    return "".join(chr(val) for val in vals)


def set_leds(leds: Dict[int, bool]):
    """Turns the LEDs on or off depending on their index

    Args:
        leds (Dict[int, bool]): index of the LED and whether it's on
    """
    dev.ctrl_transfer(0x21, 9, 0x0200, 0, convert_led_map(leds))


led_status = {}


def toggle_led(idx: int, on: bool):
    led_status[idx] = on
    set_leds(led_status)

# Everything off
set_leds({})
