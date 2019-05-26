#!/usr/bin/env python
"""
Pymodbus Asynchronous Server Example
--------------------------------------------------------------------------
The asynchronous server is a high performance implementation using the
twisted library as its backend.  This allows it to scale to many thousands
of nodes which can be helpful for testing monitoring software.
"""

import argparse
import logging
import signal
import threading
import time

from pymodbus.server.asynchronous import StartTcpServer, StopServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.register_write_message import WriteSingleRegisterRequest, WriteSingleRegisterResponse

from twisted.internet import reactor

import ledstrip

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class LedstripControlRequest(WriteSingleRegisterRequest):

    def __init__(self, address=None, **kwargs):
        super(LedstripControlRequest, self).__init__(self, **kwargs)
        self.address = address
        self.count = 16

    def execute(self, context):
        result = super().execute(context)

        if isinstance(result, ModbusResponse):
            address = result.address
            value = result.value

            logger.debug(f"Value {value} written at {address}")

            # TODO: signal controller to do something with the value at address

        return result


class SIGINT_handler():
    def __init__(self):
        self.SIGINT = False

    def signal_handler(self, signal, frame):
        logger.debug('signal received')
        if not self.SIGINT:
            self.SIGINT = True
            raise ModLedSigintException()

    def reset(self):
        logger.debug('resetting signal handler')
        self.SIGINT = False

class ModLedSigintException(Exception):
    pass

class ModLedController(threading.Thread):

    def __init__(self):
        super(ModLedController, self).__init__()

        #self.daemon = True
        self._stop_event = threading.Event()

        count = ledstrip.LED_COUNT
        pin = ledstrip.LED_PIN
        frequence = ledstrip.LED_FREQUENCE
        dma = ledstrip.LED_DMA
        invert = ledstrip.LED_INVERT
        brightness =  ledstrip.LED_BRIGHTNESS

        # TODO: we want the ledstrip to be initialized with some settings that can be set
        # using Modbus. We need to device a solution for this. For now, we pick the hardcoded defaults.
        self.ledstrip = ledstrip.SwitchableLedstrip(
            count=count, 
            pin=pin, 
            frequence=frequence, 
            dma=dma, 
            invert=invert, 
            brightness=brightness
        )

        logger.debug('here')


    def run(self):

        while True:
            logger.debug('do some stuff here')


            time.sleep(1)

        self.stop()
    
    def stop(self):
        logger.debug('stopping')
        self.ledstrip.clear()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def run(host, port):

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [17]*10)
    )

    context = ModbusServerContext(
        slaves=store, 
        single=True
    )
    
    # NOTE: initializing the Modbus server identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'hslatman'
    identity.ProductCode = 'MLS'
    identity.VendorUrl = 'https://github.com/hslatman/ledstrip'
    identity.ProductName = 'ModLed Server'
    identity.ModelName = 'ModLed X'
    identity.MajorMinorRevision = '0.1.0'

    #signal_handler = SIGINT_handler()
    #signal.signal(signal.SIGINT, signal_handler.signal_handler)

    # NOTE: we're running the ModLedController as a thread
    controller = ModLedController()
    controller.start()

    # NOTE: starting the server with custom LedstripControlRequest
    # StartTcpServer(
    #     context, 
    #     identity=identity, 
    #     address=(host, port),
    #     custom_functions=[LedstripControlRequest]
    # )

    logger.debug('starting server')

    try:
        StartTcpServer(
            context, 
            identity=identity, 
            address=(host, port),
            custom_functions=[LedstripControlRequest],
            defer_reactor_run=False
        )
    except ModLedSigintException as e:
        logger.debug('stopping')
        controller.stop()
        StopServer()

    logger.debug('finished')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ModLed X Controller.')
    parser.add_argument('-H', '--host', nargs='?', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP)')
    parser.add_argument('-P', '--port', nargs='?', type=int, default=502, help='The Modbus server port number')

    args = parser.parse_args()

    host = args.host
    port = args.port

    try:
        run(host, port)
    except Exception as e:
        logger.error(e)
    