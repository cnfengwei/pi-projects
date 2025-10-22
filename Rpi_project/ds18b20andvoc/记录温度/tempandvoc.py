#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动记录温度与空气质量(TVOC/CH2O/CO2)到 SQLite 数据库。
支持断线重连、错误日志、防崩溃循环。
每 1 小时采样一次。
"""

import os
import time
import sqlite3
import serial
from datetime import datetime
from w1thermsensor import W1ThermSensor

# === 配置区 ===
SERIAL_PORT = '/dev/serial0'
BAUD_RATE = 9600
DATA_FRAME_LENGTH = 9
DB_PATH = '/home/fengweipi/Rpi_project/ds18b20/temperature/temp_ds.db'
TABLE_NAME = 'tempanvoc'
INTERVAL_SECONDS = 3600   # 每小时记录一次
LOG_FILE = '/home/fengweipi/Rpi_project/ds18b20/temperature/tempandvoc.log'

MODULE_ADDR_H = 0x2C
MODULE_ADDR_L = 0xE4


def log(msg: str):
    """写入日志文件"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def calculate_checksum(data):
    return sum(data[0:8]) & 0xFF if len(data) >= 8 else -1


def read_tvoc_sensor(ser):
    """读取 TVOC/CH2O/CO2 数据"""
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
        log(f"读取 TVOC 错误: {e}")
        return None


def read_temperature():
    """读取 DS18B20 温度"""
    try:
        sensors = W1ThermSensor.get_available_sensors()
        if not sensors:
            return None
        return sensors[0].get_temperature()
    except Exception as e:
        log(f"读取温度错误: {e}")
        return None


def setup_database():
    """确保数据库和表存在"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temp REAL,
            ch2o REAL,
            tvoc REAL,
            co2 REAL
        )
    """)
    conn.commit()
    return conn, cur


def open_serial():
    """尝试打开串口"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        log(f"串口已打开: {SERIAL_PORT}")
        return ser
    except Exception as e:
        log(f"串口打开失败: {e}")
        return None


def main():
    log("==== 启动温度与空气质量记录程序 ====")
    conn, cur = setup_database()
    ser = open_serial()

    while True:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            temp = read_temperature()
            air = read_tvoc_sensor(ser)

            if temp is None and air is None:
                log("传感器数据读取失败，稍后重试。")
            else:
                ch2o = air['CH2O'] if air else None
                tvoc = air['TVOC'] if air else None
                co2 = air['CO2'] if air else None
                cur.execute(f"""
                    INSERT INTO {TABLE_NAME} (timestamp, temp, ch2o, tvoc, co2)
                    VALUES (?, ?, ?, ?, ?)
                """, (now, temp, ch2o, tvoc, co2))
                conn.commit()
                log(f"写入成功 | T={temp:.2f}°C | CH2O={ch2o:.3f} | TVOC={tvoc:.3f} | CO2={co2:.3f}")

        except (sqlite3.Error, serial.SerialException) as e:
            log(f"数据库或串口错误: {e}")
            time.sleep(5)
            ser = open_serial()
            conn, cur = setup_database()
        except Exception as e:
            log(f"未知错误: {e}")
            ser = open_serial()
            time.sleep(5)

        # 1 小时后再测
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("用户终止程序。")
    except Exception as e:
        log(f"致命错误: {e}")
