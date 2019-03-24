import argparse
import logging
import time

#import board
#import neopixel

#import neopixel

from neopixel import *

LEDCOUNT = 300
GPIOPIN = 18
FREQ = 800000
DMA = 5
INVERT = False
BRIGHTNESS = 255
COLOR = Color(255, 255, 255)


#PIXEL_PIN = 18

#ORDER = neopixel.RGB

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)-20s - %(levelname)-16s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

from pymodbus.client.sync import ModbusTcpClient

strip = Adafruit_NeoPixel(LEDCOUNT, GPIOPIN, FREQ, DMA, INVERT, BRIGHTNESS)
strip.begin()

strip.setPixelColor(1, COLOR)
strip.show()

def colorize(args, value):
    brightness = args.brightness
    num_pixels = args.num_pixels

    #pixels = neopixel.NeoPixel(PIXEL_PIN, num_pixels, brightness=brightness, auto_write=False, pixel_order=ORDER)

    # NOTE: doe iets met value; ik weet nog niet precies wat de waarde kan zijn
    logger.info(value)
    color = None
    if value == 0:
        color = (255, 0, 0) # rood
    elif value == 1:
        color = (0, 255, 0) # groen
    else:
        # NOTE: alle andere gevallen
        color = (0, 0, 255) # blauw
    
    #pixels.fill(color) 
    #pixels.show()

    strip.setPixelColor(1, color)
    strip.setPixelColor(2, color)
    strip.setPixelColor(3, color)
    strip.setPixelColor(4, color)
    strip.setPixelColor(5, color)
    strip.setPixelColor(6, color)
    strip.setPixelColor(7, color)
    strip.setPixelColor(8, color)
    strip.setPixelColor(9, color)
    strip.setPixelColor(10, color)
    strip.show()


def main(args):
    print(args)

    host = args.host
    port = args.port
    unit = args.unit

    # TODO: logica voor verbinden
    client = ModbusTcpClient(host, port)

    # NOTE: verbindt de client met de server
    client.connect()

    while True:

        try:
            # NOTE: hier wellicht read_coils index aanpassen?
            # De read_coils doet volgens mij ook een connect() elke keer een connect()
            #result = client.read_coils(1, 1, unit=unit)

            # NOTE: hier wordt het eerste bit op index 0 van het resultaat ingeladen; wellicht aanpassen
            #value = result.bits[0]
            value = 0

            # NOTE: alternatief lezen van discrete inputs?
            #result = client.read_discrete_inputs(0, 8, unit=unit)

            # NOTE: alternatief lezen van een holding register?
            #result = client.read_holding_registers(1, 1, unit=unit)
            #value = result.registers[0]

            # NOTE: meer voorbeelden: https://github.com/riptideio/pymodbus/blob/master/examples/common/synchronous_client.py
        
            colorize(args, value)

            client.close()

        except:
            # NOTE: we doen niks om de fout op te vangen; we gaan gewoon door.
            pass

        time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ledstrip Control.')
    parser.add_argument('host', type=str, help='The Modbus server host (hostname / IP)')
    parser.add_argument('port', nargs='?', default=502, type=int, help='The Modbus server port number')
    parser.add_argument('brightness', nargs='?', type=float, default=0.2, help='The Modbus server port number')
    parser.add_argument('num_pixels', nargs='?', type=int, default=300, help='The number of pixels')
    parser.add_argument('unit', nargs='?', type=int, default=0x00)
    #parser.add_argument('--mock', action='store_true', help='Whether or not to mock the connection')


    args = parser.parse_args()

    main(args)