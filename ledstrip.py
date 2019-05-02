import argparse
import asyncio
import logging
import signal
import sys
import time

from rpi_ws281x import *

LED_COUNT = 240
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
logging.basicConfig(level=logging.DEBUG, handlers=[handler])
logger = logging.getLogger(__name__)

#from signals import Signal
#should_switch = Signal(arguments=['should_switch'])

class LedstripSignalSender(object):
    pass

class LedstripException(Exception):
    pass

class Ledstrip(Adafruit_NeoPixel):

    def __init__(self, num, pin, freq_hz=800000, dma=10, invert=False, brightness=255, channel=0):
        super(Ledstrip, self).__init__(num, pin, freq_hz, dma, invert, brightness, channel)
        
        self.should_continue = True

        #should_switch.connect(sender=LedstripSignalSender, receiver=self.trigger_switch)


    # @asyncio.coroutine
    # def trigger_switch(self, sender, should_switch):
    #     if should_switch:
    #         self.should_continue = False
    #         raise LedstripException()

    def triggerSwitch(self):
        raise LedstripException()

    def show(self):

        if self.should_continue:
            super(Ledstrip, self).show()

    def fill(self, color, walk=False, reverse=False):
        if walk:
            for index in range(self.numPixels()):
                self.setPixelColor(index, color)
                self.show()
                time.sleep(SLEEP)
        else:
            for index in range(self.numPixels()):
                self.setPixelColor(index, color)
            self.show()
    
    def clear(self, walk=False, reverse=False):
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

    def theaterChase(self, color, iterations=10):
        """Movie theater light style chaser animation."""
        for j in range(iterations):
            for q in range(3):
                for i in range(0, self.numPixels(), 3):
                    self.setPixelColor(i+q, color)
                self.show()
                time.sleep(SLEEP)
                for i in range(0, self.numPixels(), 3):
                    self.setPixelColor(i+q, 0)

    def wheel(self, pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    def rainbow(self, iterations=1):
        """Draw rainbow that fades across all pixels at once."""
        for j in range(256 * iterations):
            for i in range(self.numPixels()):
                self.setPixelColor(i, self.wheel((i+j) & 255))
            self.show()
            time.sleep(0.02)

    def rainbowCycle(self, iterations=5):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256 * iterations):
            for i in range(self.numPixels()):
                self.setPixelColor(i, self.wheel((int(i * 256 / self.numPixels()) + j) & 255))
            self.show()
            time.sleep(0.02)

    def theaterChaseRainbow(self):
        """Rainbow movie theater light style chaser animation."""
        for j in range(256):
            for q in range(3):
                for i in range(0, self.numPixels(), 3):
                    self.setPixelColor(i+q, self.wheel((i+j) % 255))
                self.show()
                time.sleep(SLEEP)
                for i in range(0, self.numPixels(), 3):
                    self.setPixelColor(i+q, 0)


# def colorize(args, value):
#     #brightness = args.brightness
#     #num_pixels = args.num_pixels

#     #pixels = neopixel.NeoPixel(PIXEL_PIN, num_pixels, brightness=brightness, auto_write=False, pixel_order=ORDER)

#     # NOTE: doe iets met value; ik weet nog niet precies wat de waarde kan zijn
#     logger.info(value)
#     color = None
#     if value == 0:
#         color = Color(255, 0, 0) # rood
#     elif value == 1:
#         color = Color(0, 255, 0) # groen
#     else:
#         # NOTE: alle andere gevallen
#         color = Color(0, 0, 255) # blauw

#     if color != None:
#         for index in range(LEDCOUNT):
#             strip.setPixelColor(index, color)
#             strip.show()
#             time.sleep(SLEEP)

#     time.sleep(1)

def program1(strip):

    red = Color(127, 0, 0) # rood
    green = Color(0, 127, 0) # groen
    blue = Color(0, 0, 127) # blauw

    colors = [red, green, blue]
    
    strip.cycle(colors, times=3)

def program2(strip):

    red = Color(127, 0, 0) # rood
    green = Color(0, 127, 0) # groen
    blue = Color(0, 0, 127) # blauw
    
    strip.fill(red, walk=True)
    strip.fill(green, walk=True)
    strip.fill(blue, walk=True)

def program3(strip):

    white = Color(127, 127, 127)
    strip.theaterChase(white)

    green = Color(127, 0, 0)
    strip.theaterChase(green)

    red = Color(0, 127, 0)
    strip.theaterChase(red)

    blue = Color(0, 0, 127)
    strip.theaterChase(blue)

def program4(strip):

    strip.rainbow()

def program5(strip):
    
    strip.rainbowCycle()

def program6(strip):

    strip.theaterChaseRainbow()

from signals import Signal
switch = Signal(providing_args=['switch'])

class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False
        #self.ledstrip = ledstrip

    def signal_handler(self, signal, frame):
        logger.debug('signal received')
        if not self.SIGINT:
            logger.debug('triggering switch')
            # only trigger it once, for now
            self.SIGINT = True
            #self.ledstrip.triggerSwitch()
            switch.send(sender=self.__class__, switch=True)

    def reset(self):
        logger.debug('resetting signal handler')
        self.SIGINT = False

class SwitchableLedstrip(object):
    def __init__(self):
        super(SwitchableLedstrip, self).__init__()
        self.ledstrip = Ledstrip(LED_COUNT, LED_PIN, LED_FREQUENCE, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

        self.signal_handler = SIGINT_handler()
        signal.signal(signal.SIGINT, self.signal_handler.signal_handler)

        switch.connect(ledstrip.triggerSwitch)

    def start(self):
        logger.debug('starting')
        should_continue = 0
        self.ledstrip.begin()
        while True and should_continue < 3:
            try:
                blue = Color(0, 0, 127)
                self.ledstrip.theaterChase(blue)
            except LedstripException as e:
                logger.debug(e)
                should_continue += 1

                logger.debug(should_continue)
                self.signal_handler.reset()


                # TODO: read what we should do; then reinitialize and continue?

        self.stop()
    
    def stop(self):
        
        logger.debug('stopping')
        self.ledstrip.clear()


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

    # strip = Ledstrip(LED_COUNT, LED_PIN, LED_FREQUENCE, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # strip.begin()

    # while True and strip != None:

    #     #program1(strip)
    #     #program2(strip)
    #     program3(strip)
    #     program4(strip)
    #     program5(strip)
    #     program6(strip)

    #     if signal_handler.SIGINT:
    #         strip.clear(walk=True)
    #         strip = None
    #         break

    strip = SwitchableLedstrip()
    strip.start()


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