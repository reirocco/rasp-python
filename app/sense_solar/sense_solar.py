#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# 太陽電池の発電量センシング用スクリプト．
# 以下のセンサを使用して，測定を行います．
# センサの存在は自動検出します．
#
# [センサ一覧]
# - SHT-35      : 温度，湿度
# - INA226      : 電圧，電流，電力

import os
import sys
import re
import time
import json
import subprocess

json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'lib'))

import sensor.sht35
import sensor.ina226


I2C_BUS = 0x1 	      # I2C のバス番号 (Raspberry Pi は 0x1)
RETRY   = 3           # デバイスをスキャンするときのリトライ回数

SHT35_DEV_ADDR          = 0x44 # SHT-35 の I2C デバイスアドレス
INA226_PANEL_DEV_ADDR   = 0x40 # 発電電力計測用 INA226 の I2C デバイスアドレス
INA226_CHARGE_DEV_ADDR  = 0x41 # 充電電力計測用 INA226 の I2C デバイスアドレス
INA226_BATTERY_DEV_ADDR = 0x42 # 出力電力計測用 INA226 の I2C デバイスアドレス

def scan_sensor(sensor_list):
    value_map = {}
    for sensor in sensor_list:
        for i in range(RETRY):
            try:
                val = sensor.get_value_map()
                value_map.update(val)
                break
            except:
                pass
            time.sleep(0.1)

    return value_map

value_map = scan_sensor(
    [
        sensor.sht35.SHT35(I2C_BUS, SHT35_DEV_ADDR),
        sensor.ina226.INA226(I2C_BUS, INA226_PANEL_DEV_ADDR, 'panel_'),
        sensor.ina226.INA226(I2C_BUS, INA226_CHARGE_DEV_ADDR, 'charge_'),
        sensor.ina226.INA226(I2C_BUS, INA226_BATTERY_DEV_ADDR, 'battery_'),
    ]
)

rssi = subprocess.check_output("sudo iwconfig 2>/dev/null | grep 'Signal level' | sed 's/.*Signal level=\\(.*\\) dBm.*/\\1/'", shell=True)
rssi = rssi.rstrip().decode()

if re.compile('-\d+').search(rssi):
    value_map['wifi_rssi'] = int(rssi)

print(json.dumps(value_map))