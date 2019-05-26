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

from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.register_write_message import WriteSingleRegisterRequest, WriteSingleRegisterResponse

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


def run(host, port):

    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [17]*10)
    )
    context = ModbusServerContext(slaves=store, single=True)
    
    # NOTE: initializing the Modbus server identification
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'hslatman'
    identity.ProductCode = 'MLS'
    identity.VendorUrl = 'https://github.com/hslatman/ledstrip'
    identity.ProductName = 'ModLed Server'
    identity.ModelName = 'ModLed X'
    identity.MajorMinorRevision = '0.1.0'
    
    # NOTE: starting the server with custom LedstripControlRequest
    StartTcpServer(
        context, 
        identity=identity, 
        address=(host, port),
        custom_functions=[LedstripControlRequest]
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Ledstrip Controller.')
    parser.add_argument('-H', '--host', nargs='?', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP)')
    parser.add_argument('-P', '--port', nargs='?', type=int, default=502, help='The Modbus server port number')

    args = parser.parse_args()

    host = args.host
    port = args.port

    try:
        run(host, port)
    except Exception as e:
        logger.error(e)
    