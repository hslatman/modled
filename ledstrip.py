import argparse
import asyncio
import logging
import signal
import sys
import time

from rpi_ws281x import *

from signals.signals import Signal
switch = Signal(providing_args=['switch'])

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

class Ledstrip(Adafruit_NeoPixel):

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


class LedstripSignalSender(object):
    pass

class LedstripSwitchException(Exception):
    pass


class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        logger.debug('signal received')
        if not self.SIGINT:
            logger.debug('triggering switch')
            self.SIGINT = True
            switch.send(sender=LedstripSignalSender, switch=True)

    def reset(self):
        logger.debug('resetting signal handler')
        self.SIGINT = False


class SwitchableLedstrip(Ledstrip):
    def __init__(self, num, pin, freq_hz=800000, dma=10, invert=False, brightness=255, channel=0):
        super(SwitchableLedstrip, self).__init__(num, pin, freq_hz, dma, invert, brightness, channel)

    def triggerSwitch(self, sender, **kwargs):
        # NOTE: we're not doing anything with sender nor the available kwargs; could be an improvement
        raise LedstripSwitchException('Triggered LedstripSwitchException')


class LedstripController(object):
    def __init__(self):
        #super(SwitchableLedstrip, self).__init__()
        self.ledstrip = SwitchableLedstrip(LED_COUNT, LED_PIN, LED_FREQUENCE, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

        # NOTE: we register the SIGINT signal to be handled by SIGINT_handler
        # This means that whenever we get a SIGINT, termination will be handled by the signal_handler function
        self.signal_handler = SIGINT_handler()
        signal.signal(signal.SIGINT, self.signal_handler.signal_handler)

        # NOTE: we connect the switch signal to the triggerSwitch in ledstrip
        switch.connect(self.ledstrip.triggerSwitch)

    def start(self):
        logger.debug('starting')
        should_continue = 0
        max_count = 10
        self.ledstrip.begin()
        while True and should_continue < max_count: # NOTE: we loop 10 times for debugging.
            try:
                program3(self.ledstrip)
                program4(self.ledstrip)
                program5(self.ledstrip)
                program6(self.ledstrip)
            except LedstripSwitchException as e:
                logger.debug(e)
                should_continue += 1

                logger.debug(should_continue)

                # NOTE: we reset the signal_handler, such that we can trigger again
                self.signal_handler.reset()

                # TODO: read what we should do; then reinitialize, set the right settings, the right program and continue.
                # TODO: instead of (just) reacting to the SIGINT signal, we should use the switch signal, and perhaps
                # some other signals (to be defined) to react to changes from other systems, such as the internal Modbus server (to be implemented)
                # TODO: instead of a hard switch between the programs, can we define some way to make it switch smoothly?
                # perhaps using some fade mechanism, first clearing everything and then starting, etc.

        # NOTE: we're quitting just to be sure.
        self.stop()
    
    def stop(self):
        
        logger.debug('stopping')
        self.ledstrip.clear()


def main(args):
    
    controller = LedstripController()
    controller.start()


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