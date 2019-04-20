import argparse
import logging
import signal
import sys
import time

from rpi_ws281x import *

LED_COUNT = 300
LED_PIN = 18
LED_FREQUENCE = 800000
LED_DMA = 10
LED_INVERT = False
LED_BRIGHTNESS = 255

COLOR = Color(255, 255, 255)
CLEAR = Color(0, 0, 0)      # clear (or second color)
SLEEP=50/1000 # 50 milliseconds

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)-20s - %(levelname)-16s - %(message)s')
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

from pymodbus.client.sync import ModbusTcpClient

class Ledstrip(Adafruit_NeoPixel):

    def fill(self, color, walk=False):
        if walk:
            for index in range(self.numPixels()):
                self.setPixelColor(index, color)
                self.show()
                time.sleep(SLEEP)
        else:
            for index in range(self.numPixels()):
                self.setPixelColor(index, color)
            self.show()
    
    def clear(self, walk=False):
        if walk:
            for index in range(self.numPixels()):
                self.setPixelColor(index, CLEAR)
                self.show()
                time.sleep(SLEEP)
        else:
            for index in range(self.numPixels()):
                self.setPixelColor(index, CLEAR)
            self.show()

    def cycle(self, colors, times=1, sleep=1):
        # TODO: how long should one 'loop' take?
        loop = 0
        while loop < (len(colors) * times):
            color = colors[int(loop % len(colors))]

            self.fill(color)
            self.show()
            
            time.sleep(sleep)
            loop += 1


class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        print('Please wait for LEDs to turn off...')
        self.SIGINT = True

signal_handler = SIGINT_handler()
signal.signal(signal.SIGINT, signal_handler.signal_handler)

def colorize(args, value):
    #brightness = args.brightness
    #num_pixels = args.num_pixels

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

    if color != None:
        for index in range(LEDCOUNT):
            strip.setPixelColor(index, color)
            strip.show()
            time.sleep(SLEEP)

    time.sleep(1)

def program1(strip):

    green = Color(255, 0, 0) # rood
    red = Color(0, 255, 0) # groen
    blue = Color(0, 0, 255) # blauw

    colors = [red, green, blue]
    
    strip.cycle(colors)


def main(args):
    #print(args)

    #host = args.host
    #port = args.port
    #unit = args.unit

    # TODO: logica voor verbinden
    #client = ModbusTcpClient(host, port)

    # NOTE: verbindt de client met de server
    #client.connect()




    #loop = 0

    #while True:

    #    color = colors[int(loop % 3)]

        #for index in range(LEDCOUNT):
        #    strip.setPixelColor(index, color)
        #    strip.show()

    #    strip.fill(color)
    #    strip.show()

    #    time.sleep(1)

    #    loop += 1

    #   if signal_handler.SIGINT:
    #        strip.clear()
    #        strip.show()
    #        break

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

    strip = Ledstrip(LED_COUNT, LED_PIN, LED_FREQUENCE, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    strip.begin()

    while True:

        program1(strip)

        if signal_handler.SIGINT:
            strip.clear()
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ledstrip Control.')
    #parser.add_argument('host', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP)')
    #parser.add_argument('port', nargs='?', default=502, type=int, help='The Modbus server port number')
    #parser.add_argument('brightness', nargs='?', type=float, default=0.2, help='The Modbus server port number')
    #parser.add_argument('num_pixels', nargs='?', type=int, default=300, help='The number of pixels')
    #parser.add_argument('unit', nargs='?', type=int, default=0x00)
    #parser.add_argument('--mock', action='store_true', help='Whether or not to mock the connection')


    args = parser.parse_args()

    main(args)