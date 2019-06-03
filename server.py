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


# class SIGINT_handler():
#     def __init__(self):
#         self.SIGINT = False

#     def signal_handler(self, signal, frame):
#         logger.debug('signal received')
#         if not self.SIGINT:
#             self.SIGINT = True
#             raise ModLedSigintException()

#     def reset(self):
#         logger.debug('resetting signal handler')
#         self.SIGINT = False

class ModLedSigintException(Exception):
    pass

class ModLedController(threading.Thread):

    def __init__(self, disable_ledstrip=False):
        super(ModLedController, self).__init__()

        self._stop_event = threading.Event()
        self._ledstrip_enabled = not disable_ledstrip

        if self._ledstrip_enabled:
            import ledstrip

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

    def run(self):

        while not self.stopped():
            logger.debug('do some stuff here')
            time.sleep(1)

            # TODO: logic for changing the ledstrip color, program, etc.
            # TODO: can we make this work with asyncio?

    def loop(self):
        # TODO: check whether we should change the program and/or configuration for ledstrip
        # Should be performed in a thread safe manner, because we're in a different thread
        logger.debug('controller loop')
    
    def stop(self):
        logger.debug('stopping ledstrip')
        if self._ledstrip_enabled and hasattr(self, 'ledstrip') and self.ledstrip:
            self.ledstrip.clear()
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class ModLedSqlSlaveContext(SqlSlaveContext):
    def __init__(self):
        table = 'modled'
        db_file = 'modled.sqlite3'
        database = f"sqlite:///{db_file}"
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


def run(host, port, disable_ledstrip=False):

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
    store = ModLedSqlSlaveContext()
    store.initialize(hr=block) # NOTE: we're initializing with a block for Holding Registers only now.
    context = ModbusServerContext(
        slaves={unit: store}, # NOTE: Currently the SqlSlaveContext does not seem to support multiple slaves? How to distinguish?
        single=False
    )

    function = 3 # read holding registers
    address = 0
    count = 10

    values = context[unit].getValues(function, address, count)
    logger.debug("Values from datastore: " + str(values))
    
    # NOTE: initializing the Modbus server identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'hslatman'
    identity.ProductCode = 'MLS'
    identity.VendorUrl = 'https://github.com/hslatman/modled'
    identity.ProductName = 'ModLed Server'
    identity.ModelName = 'ModLed X'
    identity.MajorMinorRevision = '0.1.0'

    #signal_handler = SIGINT_handler()
    #signal.signal(signal.SIGINT, signal_handler.signal_handler)

    # NOTE: we're running the ModLedController as a separate thread
    controller = ModLedController(disable_ledstrip=disable_ledstrip)
    controller.start()

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
    #ontroller_loop = task.LoopingCall(controller.loop)
    #controller_loop.start(5.0)

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
    parser.add_argument('-DL', '--disable-ledstrip', action='store_true', help='Disable the ledstrip operation (for debugging)')

    args = parser.parse_args()

    host = args.host
    port = args.port
    disable_ledstrip = args.disable_ledstrip

    try:
        run(host, port, disable_ledstrip)
    except Exception as e:
        logger.error(e)
    