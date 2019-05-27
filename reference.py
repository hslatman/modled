#!/usr/bin/env python
"""
Pymodbus Asynchronous Server Example
--------------------------------------------------------------------------
The asynchronous server is a high performance implementation using the
twisted library as its backend.  This allows it to scale to many thousands
of nodes which can be helpful for testing monitoring software.
"""
# --------------------------------------------------------------------------- # 
# import the various server implementations
# --------------------------------------------------------------------------- # 
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.server.asynchronous import StartUdpServer
from pymodbus.server.asynchronous import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import (ModbusRtuFramer,
                                  ModbusAsciiFramer,
                                  ModbusBinaryFramer)
#from custom_message import CustomModbusRequest

# --------------------------------------------------------------------------- # 
# configure the service logging
# --------------------------------------------------------------------------- # 
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

from pymodbus.pdu import ModbusRequest, ModbusResponse
from pymodbus.register_write_message import WriteSingleRegisterRequest, WriteSingleRegisterResponse

class LedstripControlRequest(WriteSingleRegisterRequest):

    def __init__(self, address=None, **kwargs):
        super(LedstripControlRequest, self).__init__(self, **kwargs)
        self.address = address
        self.count = 16
    
    def encode(self):
        """ Encodes response pdu

        :returns: The encoded packet message
        """
        #print('encode request')
        result = super().encode()
        return result

    def decode(self, data):
        """ Decodes response pdu

        :param data: The packet data to decode
        """
        #print('decode request')
        super().decode(data)

    def execute(self, context):
        #print('execute request')
        result = super().execute(context)

        if isinstance(result, ModbusResponse):
            address = result.address
            value = result.value

            #print(address, value)
            print(f"Value {value} written at {address}")

        #print(result)
        #print(context)
        #print(self.address)
        #print(self.count)

        return result

class LedstripControlResponse(WriteSingleRegisterResponse):

    # NOTE: currently unused; would need to be instantiated in execute() function

    def __init__(self, values=None, **kwargs):
        super(LedstripControlResponse, self).__init__(self, **kwargs)
        self.values = values or []
    
    def encode(self):
        """ Encodes response pdu

        :returns: The encoded packet message
        """
        print('encode response')
        result = super().encode()
        return result

    def decode(self, data):
        """ Decodes response pdu

        :param data: The packet data to decode
        """
        print('decode response')
        super().decode(data)


def run_async_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    # The datastores only respond to the addresses that they are initialized to
    # Therefore, if you initialize a DataBlock to addresses from 0x00 to 0xFF,
    # a request to 0x100 will respond with an invalid address exception.
    # This is because many devices exhibit this kind of behavior (but not all)
    #
    #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
    #
    # Continuing, you can choose to use a sequential or a sparse DataBlock in
    # your data context.  The difference is that the sequential has no gaps in
    # the data while the sparse can. Once again, there are devices that exhibit
    # both forms of behavior::
    #
    #     block = ModbusSparseDataBlock({0x00: 0, 0x05: 1})
    #     block = ModbusSequentialDataBlock(0x00, [0]*5)
    #
    # Alternately, you can use the factory methods to initialize the DataBlocks
    # or simply do not pass them to have them initialized to 0x00 on the full
    # address range::
    #
    #     store = ModbusSlaveContext(di = ModbusSequentialDataBlock.create())
    #     store = ModbusSlaveContext()
    #
    # Finally, you are allowed to use the same DataBlock reference for every
    # table or you you may use a seperate DataBlock for each table.
    # This depends if you would like functions to be able to access and modify
    # the same data or not::
    #
    #     block = ModbusSequentialDataBlock(0x00, [0]*0xff)
    #     store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
    #
    # The server then makes use of a server context that allows the server to
    # respond with different slave contexts for different unit ids. By default
    # it will return the same context for every unit id supplied (broadcast
    # mode).
    # However, this can be overloaded by setting the single flag to False
    # and then supplying a dictionary of unit id to context mapping::
    #
    #     slaves  = {
    #         0x01: ModbusSlaveContext(...),
    #         0x02: ModbusSlaveContext(...),
    #         0x03: ModbusSlaveContext(...),
    #     }
    #     context = ModbusServerContext(slaves=slaves, single=False)
    #
    # The slave context can also be initialized in zero_mode which means that a
    # request to address(0-7) will map to the address (0-7). The default is
    # False which is based on section 4.4 of the specification, so address(0-7)
    # will map to (1-8)::
    #
    #     store = ModbusSlaveContext(..., zero_mode=True)
    # ----------------------------------------------------------------------- # 
    store = ModbusSlaveContext(
        #di=ModbusSequentialDataBlock(0, [17]*100),
        #co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [18]*3)
        #ir=ModbusSequentialDataBlock(0, [17]*100))
    #store.register(CustomModbusRequest.function_code, 'cm',
                   #ModbusSequentialDataBlock(0, [17] * 100)
                   )
    context = ModbusServerContext(slaves=store, single=True)


    # DI: functie 1; coil status (Modbus Doctor)?
    # CO: Input status? COIL?
    # HR: Holding Register
    # IR: Input Register

    # What are we doing here: set address value 0 (1 in Modbus Docter?)
    # Holding Register starts at 40000. So, address 400001.
    # 30000 is for Input Register.
    #
    # Examples include setting 100 * 17 in a list. These are 100 
    # registers. On address 0, (1, 40001) there are 100 register
    # values.
    #
    # Register 'should' start at index 1 (40001), so example:
    # hr=ModbusSequentialDataBlock(0, [18]*2) writes 18 at the 40001 position (and 40000?)
    #
    # Example write by Modbus Doctor
    # Green little balls: bits (yes/no)
    # Purple little balls: value of the entire register (16 bits) 
    # 
    # The green ones affect the values in the entire register
    # 
    # Bit 0: Ledstrip On/Off (40001.0)
    # Bit 1: Ledstrip fixed color (40001.1)
    #   If bit 1 is set, read the following addresses
    #   40002: R; 40003: G; 40004: B;
    #   So, reading continuously from the 40002, 3, 4; 
    #   Update the values for RGB 'in the background'
    #   Update the ledstrip when values change
    # Bit 2: Activate rainbow (40001.2)
    # Bit 3: Activate color mix / strandtest (40001.3)
    # 40005: number of leds to use;
    #   Only read at the start of ledstrip initialization
    # 40006: brigtness to set
    #   Only read at the start of ledstrip initialization
    # 40007: LED pin (digital pin)
    #   Only read at the start of ledstrip initialization
    # Add handling of UNITs (devices, device addresses)
    #   See https://github.com/riptideio/pymodbus/blob/master/examples/common/asynchronous_server.py#L77
    #   Idea is to run 'multiple instances' of the ledstrip for different
    #   contexts / hardware. The logic is exactly the same, only the
    #   'database' of values stores is different.
    # 40008: Which program should be active
    #   Value 1, 2, 3, (etc)
    #   1: fixed color, 2: rainbow, 3: color mix
    #
    # Look into CustomModbusRequest for handling data changes
    #   See ModbusTcpServer.StartTCPServer logging functionality
    #   Also see request.execute; https://github.com/riptideio/pymodbus/blob/13de8ab0a840d04b41cf53b9aaa98875d96ac5ec/pymodbus/server/async.py#L58
    #   Framer, decoder, custom_functions, custom messages
    #   https://github.com/riptideio/pymodbus/blob/2ef91e9e565b10fc9abc0840c87cf4a29f3d9bbf/pymodbus/server/asynchronous.py#L233
    #
    # Proposed solution: create LedstripRequest, extending ModbusRequest
    # Override the default function code (3), register the LedstripRequest,
    # override the execute funtion to react to specific data changes on specific
    # addresses, store data from the changed data from registers in local variables
    # update the ledstrip code to lookup values from local variables and react to 
    # changes
    #
    # Bit values are on/off; react to on/off states. Toggle function.
    # No function active: ledstip should shutdown
    # 


    
    # ----------------------------------------------------------------------- # 
    # initialize the server information
    # ----------------------------------------------------------------------- # 
    # If you don't set this or any fields, they are defaulted to empty strings.
    # ----------------------------------------------------------------------- # 
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'hslatman'
    identity.ProductCode = 'MLS'
    identity.VendorUrl = 'https://github.com/hslatman/ledstrip'
    identity.ProductName = 'ModLed Server'
    identity.ModelName = 'ModLed X'
    identity.MajorMinorRevision = '0.1.0'
    
    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 

    # TCP Server

    # StartTcpServer(context, identity=identity, address=("0.0.0.0", 502),
    #                custom_functions=[CustomModbusRequest])

    #StartTcpServer(context, identity=identity, address=("0.0.0.0", 502))
    
    StartTcpServer(context, identity=identity, address=("0.0.0.0", 502),
        custom_functions=[LedstripControlRequest]
    )

    # TCP Server with deferred reactor run

    # from twisted.internet import reactor
    # StartTcpServer(context, identity=identity, address=("localhost", 5020),
    #                defer_reactor_run=True)
    # reactor.run()

    # Server with RTU framer
    # StartTcpServer(context, identity=identity, address=("localhost", 5020),
    #                framer=ModbusRtuFramer)

    # UDP Server
    # StartUdpServer(context, identity=identity, address=("127.0.0.1", 5020))

    # RTU Server
    # StartSerialServer(context, identity=identity,
    #                   port='/dev/ttyp0', framer=ModbusRtuFramer)

    # ASCII Server
    # StartSerialServer(context, identity=identity,
    #                   port='/dev/ttyp0', framer=ModbusAsciiFramer)

    # Binary Server
    # StartSerialServer(context, identity=identity,
    #                   port='/dev/ttyp0', framer=ModbusBinaryFramer)


if __name__ == "__main__":
    run_async_server()