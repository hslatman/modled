#!/usr/bin/env python
"""
ModLed - Driving a ws281x ledstrip using Modbus
"""

import argparse
import logging
import signal
import struct
import sqlite3
import threading
import time
import queue

from multiprocessing import Process

from pymodbus.server.asynchronous import StartTcpServer, StopServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore.database import SqlSlaveContext
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.register_write_message import WriteSingleRegisterRequest, WriteSingleRegisterResponse

from twisted.logger._levels import LogLevel
from twisted.internet import reactor
from twisted.internet import task
from twisted.python import log

import sqlalchemy
import sqlalchemy.types as sqltypes
from sqlalchemy.sql import and_
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.sql.expression import bindparam
from sqlalchemy import select, func

FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

observer = log.PythonLoggingObserver()
observer.start()

from signals.signals import Signal
control_signal = Signal(providing_args=['address', 'value'])

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

            logger.debug(f"Value {value} written at {address}") # NOTE: the address reported here should probably be incremented to properly reflect the value in get/set-values

            control_signal.send_robust(sender=None, address=address, value=value)

            logger.debug('control_signal sent')

        return result

class LedstripSwitchException(Exception):
    pass

class ExceptionRaisingLedstripMock(object):
    def __init__(self, queue: queue.Queue):
        super(ExceptionRaisingLedstripMock, self).__init__()
        self._queue = queue

    def show(self):
        # NOTE: we're overriding the show() function as a natural break point during normal ledstrip operation
        if not self._queue.empty():
            value = self._queue.get()
            logger.debug(f"Value: {value}")
            logger.debug('raising LedstripSwitchException')
            raise LedstripSwitchException()

        logger.debug('showing ledstrip')


class ModLedController(threading.Thread):

    def __init__(self, configuration: {}, queue, disable_ledstrip=False):
        super(ModLedController, self).__init__()

        self._queue = queue
        self._stop_event = threading.Event()
        self._ledstrip_enabled = not disable_ledstrip

        self._configuration = None

        self._number_of_leds = configuration['number_of_leds']
        self._pin = configuration['pin']
        self._brightness = configuration['brightness']

        self._on = False
        self._program = None
        self._color_tuple = None

        self._has_bugun = False
        self._state = 'off'

        self.updateConfiguration(configuration)

        if self._ledstrip_enabled:
            import ledstrip

            # TODO: we want the ledstrip to be initialized with some settings that can be set
            # using Modbus. We need to device a solution for this. For now, we pick the hardcoded defaults.
            self.ledstrip = ledstrip.ExceptionRaisingLedstrip(
                queue=self._queue,
                num=self._number_of_leds, # ledstrip.LED_COUNT
                pin=self._pin, # ledstrip.LED_PIN
                freq_hz=ledstrip.LED_FREQUENCE,
                dma=ledstrip.LED_DMA,
                invert=ledstrip.LED_INVERT,
                brightness=self._brightness # ledstrip.LED_BRIGHTNESS
            )
        else:
            self.ledstrip = ExceptionRaisingLedstripMock(self._queue)

    def updateConfiguration(self, configuration: {}):
        self._configuration = configuration
        logger.debug(f"Configuration: {self._configuration}")
        self._on = configuration['on']

        program = configuration['program'] if configuration['program'] else 'fixed'
        self._program = program
        self._configuration['program'] = program

        red, green, blue = configuration['red'], configuration['green'], configuration['blue']
        self._color_tuple = (red, green, blue)


    def getConfiguration(self):
        return self._configuration

    def run(self):
        self.drive()

    def drive(self):
        logger.debug('starting ledstrip')
        logger.debug(f"Configuration: {self._configuration}")
        while not self.stopped():
            should_check_state = False
            if self._on:
                if self._ledstrip_enabled:
                    if not self._has_bugun:
                        self.ledstrip.begin()
                        self._has_bugun = True
                    try:
                        # TODO: drive the ledstrip, by configuring it right, starting the program, etc.
                        logger.debug('driving ledstrip')
                        if self._program == 'rainbow':
                            self.ledstrip.rainbow()
                        elif self._program == 'strandtest':
                            self.ledstrip.theaterChase() # TODO: strandtest?
                        else:
                            from rpi_ws281x import Color
                            color = Color(self._color_tuple[0], self._color_tuple[1], self._color_tuple[2])
                            self.ledstrip.fill(color)
                    except ledstrip.LedstripSwitchException as e:
                        logger.debug(e)
                        logger.debug('LedstripSwitchException handled')
                        should_check_state = True
                else:
                    # NOTE: this implementation is provided for the sole purpose of simulating the ledstrip
                    try:
                        self.ledstrip.show()
                        logger.debug(f"Program: {self._program}")
                        if self._program == 'fixed':
                            logger.debug(f"Colors: {self._color_tuple}")
                        time.sleep(5)
                    except LedstripSwitchException as e:
                        logger.debug(e)
                        logger.debug('LedstripSwitchException handled')
                        should_check_state = True
                    
                # TODO: logic for changing the ledstrip color, program, etc.
                # TODO: can we make this work with asyncio?
            #else:
                # When we should be off, we'll sleep for a little while, to not seem too busy...
            #    time.sleep(1)
            #    should_check_state = True

            if should_check_state:
                if self._on:
                    if self._state == 'off':
                        # we should turn on
                        self._state = 'on' # leds will go in next loop?
                else:
                    if self._state == 'on':
                        self.clear()


    def loop(self):
        # TODO: check whether we should change the program and/or configuration for ledstrip
        # Should be performed in a thread safe manner, because we're in a different thread
        logger.debug('controller loop')

    def clear(self):
        logger.debug('clearing ledstrip')
        if self._ledstrip_enabled and hasattr(self, 'ledstrip') and self.ledstrip:
            self.ledstrip.clear()

    def stop(self):
        logger.debug('stopping ledstrip')
        self.clear()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def reset(self):
        logger.debug('resetting controller')
        self._stop_event = threading.Event()


class ModLedSqlSlaveContext(SqlSlaveContext):
    def __init__(self, database='modled'):
        table = database
        database = f"sqlite:///{table}.sqlite3"
        super(ModLedSqlSlaveContext, self).__init__(table=table, database=database)

    def initialize(self, hr, force=False):
        # NOTE: this function is currently hardcoded to work with Holding Registers only
        logger.info('Initializing SQLite database')
        number_of_existing_holding_registers = self._count('h')
        if number_of_existing_holding_registers == 0:
            logger.info(f"Initializing {self.database} with {hr}.")
            address = hr.address
            values = hr.values
            # NOTE: this is rather naive, but it works for now; we can improve later
            self._set('h', address, values)
        else:
            logger.info(f"{self.database} already contains {number_of_existing_holding_registers} register addresses.")

    def _count(self, type):
        count = select([func.count()]).select_from(self._table).where(self._table.c.type == type).scalar()
        return count


def run(host, port, database='modled', disable_ledstrip=False):

    # store = ModbusSlaveContext(
    #     hr=ModbusSequentialDataBlock(0, [17]*10)
    # )

    # context = ModbusServerContext(
    #     slaves=store, 
    #     single=True
    # )

    # NOTE: currently we don't do anything with the block, although it's given in the
    # example usage at https://github.com/riptideio/pymodbus/blob/2ef91e9e565b10fc9abc0840c87cf4a29f3d9bbf/examples/common/dbstore_update_server.py
    # The code for initialization seems a bit off, because the block values are NOT used for initialisation of the
    # SQLite database when the SqlSlaveContext is created. Perhaps this requires a bug fix in the _create_db function?
    # We should probably parse all the kwargs for blocks, these should be added by default.
    block = ModbusSequentialDataBlock(1, [17]*10)
    
    # NOTE: below we're defining our modled.sqlite3 database (on disk) and table (modled) that
    # pymodbus should use to write its values to. Initialisation of the ModbusSequentialDataBlock is
    # ignored by the SqlSlaveContext for some reason (bug?). We don't have any values at the start,
    # so, trying to read and/or write from/to these addresses will fail. We can manually initialise the
    # database though. The schema is as follows:
    #
    # 1 table, with three columns: type, index and value
    #
    # type: varchar(1), h is for Holding Registers, which is what we need; others are d, c and i? See IModbusSlaveContext.
    # index: the address of the register; I've observed a difference of 1 between Modbus Doctor and SQLite (address = address + 1, unconditionally)
    # value: the value that is stored at the address
    #
    # So, as an example, we can read from register 1 using Modbus Doctor, we would need to 
    # query for type 'h', address 1 (translated to 2 by SqlSlaveContext)
    # 
    # Solutions to fixing the initialisation:
    #  
    #  1) fix the SqlSlaveContext implementation (best), including the address mode
    #  2) override _create_db function locally and make sure that we can parse the block (good)
    #  3) prefil the SQLite database, with the values we want when it does not exist (easiest?)

    # TODO: create and write the right configuration in the ModbusSequentialDataBlock (block) for normal operation

    unit = 0 # NOTE: unit functions like an identifier for a slave
    store = ModLedSqlSlaveContext(database=database)
    store.initialize(hr=block) # NOTE: we're initializing with a block for Holding Registers only now.
    context = ModbusServerContext(
        slaves={unit: store}, # NOTE: Currently the SqlSlaveContext does not seem to support multiple slaves? How to distinguish?
        single=False
    )

    def determine_configuration():

        function = 3 # read holding registers
        address = 0
        count = 10

        values = context[unit].getValues(function, address, count)
        logger.debug("Values from datastore: " + str(values))

        a40001, a40002, a40003, a40004, a40005, a40006, a40007, a40008 = values[1:9] # take 8 values
        on = (a40001 & 1 << 0 != 0) # zero'th bit
        fixed = (a40001 & 1 << 1 != 0) # first bit set
        rainbow = (a40001 & 1 << 2 != 0) # second bit set
        strandtest = (a40001 & 1 << 3 != 0) # third bit set
        red = a40002
        green = a40003
        blue = a40004
        number_of_leds = a40005
        brightness = a40006
        pin = a40007

        program = 'fixed'
        if rainbow:
            program = 'rainbow'
        if strandtest:
            program = 'strandtest'

        configuration = {
            'on': on,
            'red': red,
            'green': green,
            'blue': blue,
            'number_of_leds': number_of_leds,
            'brightness': brightness,
            'pin': pin,
            'program': program
        }
        
        return configuration

    configuration = determine_configuration()
    
    # NOTE: initializing the Modbus server identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'hslatman'
    identity.ProductCode = 'MLS'
    identity.VendorUrl = 'https://github.com/hslatman/modled'
    identity.ProductName = 'ModLed Server'
    identity.ModelName = 'ModLed X'
    identity.MajorMinorRevision = '0.1.0'

    signal_queue = queue.Queue()
    controller = ModLedController(configuration=configuration, queue=signal_queue, disable_ledstrip=disable_ledstrip)
    controller.start()

    def handler(sender, **kwargs):
        
        # TODO: do something with the address and value in kwargs
        # TODO: determine whether a reset of the ledstrip is required? e.g. first a clear, for some programs?
        # TODO: restart the controller process

        new_configuration = determine_configuration()
        old_configuration = controller.getConfiguration()

        logger.debug(f"Old configuration: {old_configuration}")
        logger.debug(f"New configuration: {new_configuration}")
        
        should_signal = False
        if new_configuration['on'] != old_configuration['on']:
            should_signal = True
        if new_configuration['program'] != old_configuration['program']:
            should_signal = True
        if new_configuration['program'] == 'fixed':
            if new_configuration['red'] != old_configuration['red']:
                should_signal = True
            if new_configuration['green'] != old_configuration['green']:
                should_signal = True
            if new_configuration['blue'] != old_configuration['blue']:
                should_signal = True

        program = new_configuration['program']
        logger.debug(f"program to run next: {program}")

        controller.updateConfiguration(new_configuration)

        logger.debug(f"Should signal: {should_signal}")
        if should_signal:
            logger.debug('signaling to trigger an exception')
            value = {'address': kwargs['address'], 'value': kwargs['value']}
            signal_queue.put(value)

    control_signal.connect(handler)

    # NOTE: starting the server with custom LedstripControlRequest
    StartTcpServer(
        context, 
        identity=identity, 
        address=(host, port),
        custom_functions=[LedstripControlRequest],
        defer_reactor_run=True
    )

    # NOTE: registering an additional looping task on the Twisted reactor
    # TODO: look into https://github.com/riptideio/pymodbus/blob/master/examples/common/dbstore_update_server.py
    # for an example using SQLite and reading values from the Modbus context; we could inject the context into
    # the controller.loop() call as an argument, read the values, react to that, store it in the controller.
    # Otherwise we could to a different loop, extract values and inject them into the controller. We need to
    # check whether the context is thread safe. We're only reading, so it's relatively safe. Otherwise we would
    # need to inject the values using a queue, for example. Downside is that it's not really reactive, but based
    # on polling the values. The custom LedstripControlRequest approach could lead to a more reactive integration.
    # controller_loop = task.LoopingCall(controller.loop)
    # controller_loop.start(5.0)

    def log_sigint(event):
        if event.get("log_text") == 'Received SIGINT, shutting down.':
            logger.debug("Stopping for: ", event)
            controller.stop()
            controller.join()
            # if reactor.running:
            #     reactor.stop()

    # NOTE: we're adding an observer that checks for SIGINT; we can then stop the controller properly
    log.addObserver(log_sigint)

    # NOTE: starting the Twisted reactor
    logger.debug('starting server')
    reactor.run()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ModLed X Controller.')
    parser.add_argument('-H', '--host', nargs='?', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP)')
    parser.add_argument('-P', '--port', nargs='?', type=int, default=502, help='The Modbus server port number')
    parser.add_argument('-D', '--database', nargs='?', type=str, default='modled', help='The datatabase file (prefix) to use')
    parser.add_argument('-DL', '--disable-ledstrip', action='store_true', help='Disable the ledstrip operation (for debugging)')
    
    args = parser.parse_args()

    host = args.host
    port = args.port
    database = args.database
    disable_ledstrip = args.disable_ledstrip

    try:
        run(host, port, database=database, disable_ledstrip=disable_ledstrip)
    except Exception as e:
        logger.error(e)
    