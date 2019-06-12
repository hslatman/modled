# modled

Drive a ledstrip using the Modbus protocol

## Description

This project drives a ws281x ledstrip using the Modbus protocol.

## Driver

After some unfruitful trials with the Adafruit neopixel library, I decided to 
settle on the rpi-ws281x-python library available [here](https://github.com/rpi-ws281x/rpi-ws281x-python).

## WS281x Examples

We've included some of the examples available from the rpi-ws281x-python library from the [examples](https://github.com/rpi-ws281x/rpi-ws281x-python/tree/master/examples) directory.
The ones that are included in the repository have been adapted slightly

## TODO

* ~~Add Modbus server and logic for initializing the strip.~~
* ~~Add Modbus server and logic for updating the strip.~~
* ~~Continuous reconfiguration of program and color settings~~
* ~~Toggling programs on/off~~
* ~~Improvement for closing the ledstrip: immediate action upon ending program by checking enabled/disabled value before showing the ledstrip again.~~
* ~~Initialization of Ledstrip from a Modbus command?~~
* Smooth ledstrip program switches?
* Smooth script kills, restarts, etc. Should we properly daemonize it? Persist current state when stopping the server?
* Add option to start/pause the strip from running? StopException, StartException? Currently we're using a single signal.
* ~~Break on permission error?~~
* Extend the number of programs and improve maintainability of handling programs
* Settings for configuring walk vs. no walk in ledstrip show
* Integrate with [Home Assistant](https://www.home-assistant.io/components/modbus/)? 