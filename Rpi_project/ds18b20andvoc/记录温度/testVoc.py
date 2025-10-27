#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 UART4 读取 VOC 数据并打印。
用于测试 LoRa 前的 VOC 通信是否正常。
"""

import serial
import time
from datetime import datetime

# === 配置区 ===
SERIAL_PORT = '/dev/ttyAMA4'   # 使用 UART4
BAUD_RATE = 9600
DATA_FRAME_LENGTH = 9

# VOC 模块地址
MODULE_ADDR_H = 0x2C
MODULE_ADDR_L = 0xE4


def calculate_checksum(data):
    """计算 VOC 模块的校验和"""
    return sum(data[0:8]) & 0xFF if len(data) >= 8 else -1


def read_tvoc_sensor(ser):
    """读取 VOC 模块数据"""
    try:
        if not ser or not ser.is_open:
            return None

        ser.flushInput()
        raw = ser.read(DATA_FRAME_LENGTH)
        if len(raw) != DATA_FRAME_LENGTH:
            return None

        data = list(raw)
        if data[0] != MODULE_ADDR_H or data[1] != MODULE_ADDR_L:
            return None
        if data[8] != calculate_checksum(data):
            return None

        tvoc = (data[2] * 256 + data[3]) * 0.001
        ch2o = (data[4] * 256 + data[5]) * 0.001
        co2 = (data[6] * 256 + data[7]) * 0.001
        return {"TVOC": tvoc, "CH2O": ch2o, "CO2": co2}

    except Exception as e:
        print(f"[错误] 读取 TVOC 失败: {e}")
        return None


def main():
    print("==== VOC 数据测试 (UART4) ====")

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"[OK] 串口已打开: {SERIAL_PORT}")
    except Exception as e:
        print(f"[错误] 无法打开串口: {e}")
        return

    while True:
        air = read_tvoc_sensor(ser)
        if air:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                  f"TVOC={air['TVOC']:.3f} mg/m³ | "
                  f"CH2O={air['CH2O']:.3f} mg/m³ | "
                  f"CO2={air['CO2']:.3f} mg/m³")
        else:
            print(f"[{datetime.now():%H:%M:%S}] 未接收到有效 VOC 数据")
        time.sleep(2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("用户终止程序。")
