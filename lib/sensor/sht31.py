#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SHT-31 を使って温度や湿度を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「SHT-31 １チップ温度・湿度センサ・モジュール」．
# https://strawberry-linux.com/support/80031/1870819

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class SHT31:
    NAME                = 'SHT-31'
    DEV_ADDR		= 0x44 # 7bit
    REG_MEASURE		= [0x24, 0x00]
    REG_STATUS		= [0xF3, 0x2D]
    REG_RESET		= [0x30, 0xA2]
    
    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)

    def crc(self, msg):
        poly = 0x31
        crc = 0xFF
    
        for data in bytearray(msg):
            crc ^= data
            for i in range(8):
                if crc & 0x80:
                    crc = (crc << 1 ) ^ poly
                else:
                    crc <<= 1
            crc &= 0xFF

        return crc
            
    def ping(self):
        data = b'   '
        try:
            self.i2cbus.write(self.dev_addr, self.REG_STATUS)
            data = self.i2cbus.read(self.DEV_ADDR, 3)
        except:
            pass

        return data[2] == self.crc(data[0:2])
    
    def get_value(self):
        self.i2cbus.write(self.dev_addr, self.REG_RESET)
        time.sleep(0.01)

        self.i2cbus.write(self.dev_addr, self.REG_MEASURE)
        time.sleep(0.05)

        data = self.i2cbus.read(self.DEV_ADDR, 6)

        if (self.crc(data[0:2]) != data[2]) or (self.crc(data[3:5]) != data[5]):
            raise IOError("ERROR: CRC unmatch.")

        temp = -45 + (175 *  int.from_bytes(data[0:2], byteorder='big')) / float(2**16 - 1)
        humi = 100 * int.from_bytes(data[3:5], byteorder='big') / float(2**16 - 1)

        return [ round(temp, 4), round(humi, 1) ]

    def get_value_map(self):
        data = self.get_value()

        return { 'temp': data[0], 'humi': data[1] }


if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.sht31
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    sht31 = sensor.sht31.SHT31(I2C_BUS)

    ping = sht31.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(sht31.get_value_map())
