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

* Ledstrip finalization (or changing procedures) does not work smoothly using the signal handler.
We should look into the examples at https://github.com/jgarff/rpi_ws281x/tree/master/python/examples to see how we can clean the old program, reset the strip and continue a different program. The approach using signal handler and custom show function resulted in weird behaviour.