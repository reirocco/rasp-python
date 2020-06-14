#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TSL2562 を使って照度(LUX)を取得するライブラリです．
#
# 作成時に使用したのは，Strawberry Linux の
#「TSL2561 照度センサ・モジュール」．
# https://strawberry-linux.com/catalog/items?code=12561

import time
import struct

if __name__ == '__main__':
    import os
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

import i2cbus

class TSL2561:
    NAME                = 'TSL2561'
    
    DEV_ADDR		= 0x39 # 7bit
    
    REG_CTRL		= 0xE0
    REG_TIMING		= 0xA1
    REG_DATA		= 0xAC
    REG_ID		= 0xAA

    INTEG_13MS      	= 0x00
    INTEG_101MS     	= 0x01
    INTEG_402MS     	= 0x02
    
    GAIN_1X         	= 0x00
    GAIN_16X        	= 0x10

    POWER_ON        	= 0x03
    POWER_OFF    	= 0x00
    
    gain = GAIN_1X
    integ = INTEG_402MS

    def __init__(self, bus, dev_addr=DEV_ADDR):
        self.bus = bus
        self.dev_addr = dev_addr
        self.i2cbus = i2cbus.I2CBus(bus)
        self.is_init = False

    def init(self):
        data = self.i2cbus.read(self.DEV_ADDR, 1, 0x90)
        data = int.from_bytes(data, byteorder='big')

        if (data & 0x0F) != 0x03:
            self.set_timing()
            self.enable()
            self.wait()

        self.is_init = True

    def enable(self):
        self.i2cbus.write(self.dev_addr, [self.REG_CTRL, self.POWER_ON])

    def set_timing(self):
        value = self.gain | self.integ
        self.i2cbus.write(self.dev_addr, [self.REG_TIMING, value])
        
    def set_gain(self, gain):
        self.gain = gain

    def set_integ(self, integ):
        self.integ = integ

    def wait(self):
        if self.integ == self.INTEG_13MS:
            time.sleep(0.13 + 0.2)
        if self.integ == self.INTEG_101MS:
            time.sleep(0.101 + 0.2)
        if self.integ == self.INTEG_402MS:
            time.sleep(0.402 + 0.2)

    def ping(self):
        dev_id = 0

        try:
            value = self.i2cbus.read(self.DEV_ADDR, 1, self.REG_ID)
            dev_id = int.from_bytes(value, byteorder='little')
        except:
            pass

        return (dev_id >> 4) == 0x1
    
    def get_value(self):
        if not self.is_init:
            self.init()

        value = self.i2cbus.read(self.dev_addr, 4, self.REG_DATA)

        ch0 = int.from_bytes(value[0:2], byteorder='little')
        ch1 = int.from_bytes(value[2:4], byteorder='little')

        if (self.gain == self.GAIN_1X):
            ch0 *=16
            ch1 *=16

        if (self.integ == self.INTEG_13MS):
            ch0 *= 322.0/11
            ch1 *= 322.0/11
        elif (self.integ == self.INTEG_101MS):
            ch0 *= 322.0/81
            ch1 *= 322.0/81

        if (ch0 == 0):
            return [ 0.0 ]

        if (ch1/ch0) <= 0.52:
            return [ round(0.0304*ch0 - 0.062*ch0*((ch1/ch0)**1.4), 1) ]
        elif (ch1/ch0) <= 0.65:
            return [ round(0.0224*ch0 - 0.031*ch1, 1) ]
        elif (ch1/ch0) <= 0.80:
            return [ round(0.0128*ch0 - 0.0153*ch1, 1) ]
        elif (ch1/ch0) <= 1.30:
            return [ round(0.00146*ch0 - 0.00112*ch1, 1) ]
        else:
            return [ 0.0 ];

    def get_value_map(self):
        value = self.get_value()

        return { 'lux': value[0] }

        
if __name__ == '__main__':
    # TEST Code
    import pprint
    import sensor.tsl2561
    I2C_BUS = 0x1 # I2C のバス番号 (Raspberry Pi は 0x1)

    tsl2561 = sensor.tsl2561.TSL2561(I2C_BUS)
    ping = tsl2561.ping()
    print('PING: %s' % ping)

    if (ping):
        pprint.pprint(tsl2561.get_value_map())
