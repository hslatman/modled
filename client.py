#!/usr/bin/env python

import argparse
import logging

from pymodbus.client.sync import ModbusTcpClient

FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def main(host, port, address, write=None, unit=1): # NOTE: the unit is like an identifier for the slave; it corresponds to the identifier for a store

    client = ModbusTcpClient(host, port=port)
    client.connect()

    if write != None:
        value = write
        logger.debug(f"Writing value {value} to address {address}")
        rq = client.write_register(address, value, unit=unit)
        assert(not rq.isError())     # test that we are not an error
    
    rr = client.read_holding_registers(address, 1, unit=unit)
    logger.info(f"Value at address {address} is {rr.registers[0]}")
    #assert(rr.registers[0] == 11)       # test the expected value

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
    parser.add_argument('-W', '--write', nargs='?', type=int, default=None, help='Enable writing to the address, otherwise it will be read')
    parser.add_argument('-A', '--address', type=int, default=1, help='The address to read from / write to (in case -W was given)')
    parser.add_argument('-U', '--unit', type=int, default=1, help='The unit (slave identifier) to use')

    args = parser.parse_args()

    print(args)

    host = args.host
    port = args.port
    address = args.address
    write = args.write
    unit = args.unit

    main(host, port, address, write, unit)
