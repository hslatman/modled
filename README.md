# ledstrip
Drive a ledstrip with modbus

## Description

This project contains a utility for driving a ws281x ledstrip.

After some unfruitful trials with the Adafruit neopixel library, I decided to 
settle on the rpi-ws281x-python library available [here](https://github.com/rpi-ws281x/rpi-ws281x-python).

## Examples

We've included some of the examples available from the rpi-ws281x-python library from the [examples](https://github.com/rpi-ws281x/rpi-ws281x-python/tree/master/examples) directory.
The ones that are included in the repository have been adapted slightly

## TODO

* Add Modbus server and logic for updating the strip.
* React to data changes on registers (parse data, hex to int, etc)
* Modbus configuration of Ledstrip (initial)
* Continuous reconfiguration of program and color settings
* Toggling programs on/off
* Improvement for closing the ledstrip: immediate action upon ending program by checking enabled/disabled value before showing the ledstrip again.
* Initialization of Ledstrip from a Modbus command?
* Smooth program switches?
