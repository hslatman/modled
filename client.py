#!/usr/bin/env python

import argparse
import logging

from pymodbus.client.sync import ModbusTcpClient

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def main(host, port):

    client = ModbusTcpClient(host, port=port)
    client.connect()

    unit = 0 # NOTE: the unit is like an identifier for the slave; it corresponds to the identifier for a store
    logger.debug("Write to a holding register and read back")
    rq = client.write_register(1, 11, unit=unit)
    rr = client.read_holding_registers(1, 1, unit=unit)
    assert(not rq.isError())     # test that we are not an error
    assert(rr.registers[0] == 11)       # test the expected value

    # logger.debug("Write to multiple holding registers and read back")
    # rq = client.write_registers(1, [10]*8, unit=UNIT)
    # rr = client.read_holding_registers(1, 8, unit=UNIT)
    # assert(not rq.isError())     # test that we are not an error
    # assert(rr.registers == [10]*8)      # test the expected value

    client.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='ModLed X Client.')
    parser.add_argument('-H', '--host', nargs='?', type=str, default='127.0.0.1', help='The Modbus server host (hostname / IP) to connect to')
    parser.add_argument('-P', '--port', nargs='?', type=int, default=502, help='The Modbus server port number to connect to')
    
    args = parser.parse_args()

    # TODO: add some additional parameters to set the address and values to read/write?

    host = args.host
    port = args.port

    main(host, port)
