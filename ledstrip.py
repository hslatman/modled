import argparse
import logging
import time
import signal
import sys

#import board
#import neopixel

#import neopixel

from neopixel import *
from neopixel import Color
from neopixel import Adafruit_NeoPixel

LEDCOUNT = 300
GPIOPIN = 18
FREQ = 800000
DMA = 5
INVERT = False
BRIGHTNESS = 255

COLOR = Color(255, 255, 255)
CLEAR = Color(0, 0, 0)      # clear (or second color)


#PIXEL_PIN = 18
#ORDER = neopixel.RGB

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)-20s - %(levelname)-16s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

from pymodbus.client.sync import ModbusTcpClient

class Strip(Adafruit_NeoPixel):

    def fill(self, color):
        for index in self.numPixels():
            self.setPixelColor(index, color)
    
    def clear(self):
        for index in self.numPixels():
            self.setPixelColor(index, CLEAR)


#strip = Adafruit_NeoPixel(LEDCOUNT, GPIOPIN, FREQ, DMA, INVERT, BRIGHTNESS)
#strip.begin()

strip = Strip(LEDCOUNT, GPIOPIN, FREQ, DMA, INVERT, BRIGHTNESS)
strip.begin()

class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        print('Please wait for LEDs to turn off...')
        self.SIGINT = True

signal_handler = SIGINT_handler()
signal.signal(signal.SIGINT, signal_handler.signal_handler)

def colorize(args, value):
    brightness = args.brightness
    num_pixels = args.num_pixels

    #pixels = neopixel.NeoPixel(PIXEL_PIN, num_pixels, brightness=brightness, auto_write=False, pixel_order=ORDER)

    # NOTE: doe iets met value; ik weet nog niet precies wat de waarde kan zijn
    logger.info(value)
    color = None
    if value == 0:
        color = Color(255, 0, 0) # rood
    elif value == 1:
        color = Color(0, 255, 0) # groen
    else:
        # NOTE: alle andere gevallen
        color = Color(0, 0, 255) # blauw
    
    #pixels.fill(color) 
    #pixels.show()

    #print('here')

    if color != None:

        for index in range(LEDCOUNT):
            strip.setPixelColor(index, color)
            strip.show()

    time.sleep(1)


def main(args):
    print(args)

    host = args.host
    port = args.port
    unit = args.unit

    # TODO: logica voor verbinden
    #client = ModbusTcpClient(host, port)

    # NOTE: verbindt de client met de server
    #client.connect()

    green = Color(255, 0, 0) # rood
    red = Color(0, 255, 0) # groen
    blue = Color(0, 0, 255) # blauw

    colors = [red, green, blue]
    loop = 0

    while True:

        color = colors[int(loop % 3)]

        #for index in range(LEDCOUNT):
        #    strip.setPixelColor(index, color)
        #    strip.show()

        strip.fill(blue)
        strip.show()

        if signal_handler.SIGINT:
            for index in range(LEDCOUNT):
                strip.setPixelColor(index, CLEAR)
                strip.show()
            break

        loop += 1

    #while True:

    #    try:
            # NOTE: hier wellicht read_coils index aanpassen?
            # De read_coils doet volgens mij ook een connect() elke keer een connect()
            #result = client.read_coils(1, 1, unit=unit)

            # NOTE: hier wordt het eerste bit op index 0 van het resultaat ingeladen; wellicht aanpassen
            #value = result.bits[0]
    #        value = 0

            # NOTE: alternatief lezen van discrete inputs?
            #result = client.read_discrete_inputs(0, 8, unit=unit)

            # NOTE: alternatief lezen van een holding register?
            #result = client.read_holding_registers(1, 1, unit=unit)
            #value = result.registers[0]

            # NOTE: meer voorbeelden: https://github.com/riptideio/pymodbus/blob/master/examples/common/synchronous_client.py
        
    #        colorize(args, value)

    #        client.close()

    #    except:
            # NOTE: we doen niks om de fout op te vangen; we gaan gewoon door.
    #        pass

    #    time.sleep(1)

    #    if signal_handler.SIGINT:
    #        for index in range(LEDCOUNT):
    #            strip.setPixelColor(index, CLEAR)
    #            strip.show()
    #        break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ledstrip Control.')
    parser.add_argument('host', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP)')
    parser.add_argument('port', nargs='?', default=502, type=int, help='The Modbus server port number')
    parser.add_argument('brightness', nargs='?', type=float, default=0.2, help='The Modbus server port number')
    parser.add_argument('num_pixels', nargs='?', type=int, default=300, help='The number of pixels')
    parser.add_argument('unit', nargs='?', type=int, default=0x00)
    #parser.add_argument('--mock', action='store_true', help='Whether or not to mock the connection')


    args = parser.parse_args()

    main(args)