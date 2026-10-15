# Input box

This controls a physical input box. The box consists of:

- USB joystick input device
- One 'simple' button
- One button, with an LED and configurable LEDs
- USB LED controller (Ultimarc PAC-DRIVE)
- 12v power supply for LEDs

## USB joystick input

This step was fairly straightforward. The joystick controller maps the buttons to inputs which can be directly read using `get_gamepad()`. You might want to update the `event_code` to reflect the actual codes used with your specific board.

## LED controller

The SDK from Ultimarc wasn't available for Python. A [C library exists](https://github.com/katie-snow/Ultimarc-linux/tree/master) or a [reworked version of an older libary (also in C)](http://www.zumbrovalley.net/readpost.php?artid=33).

Because I only need to send simple commands, I figured only basic stuff from pyUSB should be enough.

I determined the right vendor and product ID.

Here's how:

Make sure the device isn't connected.
Run:

`lsusb > a.txt`

Plug it in, then:

```bash
lsusb > b.txt
diff a.txt f.txt
```

It should show something as:

> Bus 003 Device 021: ID d209:1500 Ultimarc LED Controller

Update the values in `led.py` if they differ from these values.

## Speaking

For the TTS (text to speech) [Piper](https://github.com/OHF-Voice/piper1-gpl) is used. Playing might require [installing additional system requirements](https://pypi.org/project/PyAudio/) for PyAudio e.g. `portaudio19-dev` on Linux. It also requires downloading a voice (by default nl_NL-alex is used).
