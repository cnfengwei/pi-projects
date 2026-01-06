#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动记录温度与空气质量(TVOC/CH2O/CO2)到 SQLite 数据库并显示到 OLED 屏幕。
支持断线重连、错误日志、防崩溃循环。
每 1 小时采样一次。
"""

import sqlite3
import time
from datetime import datetime

import serial

# === OLED 依赖新增 ===
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import ImageFont
from w1thermsensor import W1ThermSensor

# === 配置区 ===
SERIAL_PORT = "/dev/serial0"
BAUD_RATE = 9600
DATA_FRAME_LENGTH = 9
DB_PATH = "/home/fengweipi/Rpi_project/ds18b20/temperature/temp_ds.db"
TABLE_NAME = "tempanvoc"
INTERVAL_SECONDS = 3600  # 每小时记录一次
LOG_FILE = "/home/fengweipi/Rpi_project/ds18b20/temperature/tempandvoc.log"

MODULE_ADDR_H = 0x2C
MODULE_ADDR_L = 0xE4

# === OLED 配置和初始化新增 ===
device = None
font = None
font_large = None
OLED_ADDRESS = 0x3C  # SSD1306 默认地址

try:
    # 尝试初始化 I2C 接口
    serial_oled = i2c(port=1, address=OLED_ADDRESS)
    device = ssd1306(serial_oled)
    log("OLED 屏幕初始化成功 (I2C)。")

    # 加载字体（使用系统默认的等宽字体）
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        # 尝试使用 10 号和 14 号字体
        font = ImageFont.truetype(font_path, 10)
        font_large = ImageFont.truetype(font_path, 14)
    except Exception:
        # 如果字体加载失败，使用 PIL 默认字体
        font = ImageFont.load_default()
        font_large = ImageFont.load_default()
        log("字体加载失败，使用默认字体。")

except Exception as e:
    device = None
    log(f"OLED 初始化失败，请检查接线和 I2C 启用状态: {e}")
# ==================================


def log(msg: str):
    """写入日志文件"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
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


# === 新增 OLED 绘制函数 ===
def draw_data_on_oled(temp, ch2o, tvoc, co2, now_time):
    """绘制数据到 OLED 屏幕"""
    global device, font, font_large

    if not device:
        return

    with canvas(device) as draw:
        # 清空屏幕
        draw.rectangle(device.bounding_box, outline="black", fill="black")

        # 1. 顶部时间（显示小时和分钟）
        time_str = now_time.split(" ")[1]
        draw.text((0, 0), time_str, font=font_large, fill="white")

        # 2. 温度 (右侧)
        temp_str = f"T: {temp:.1f} C" if temp is not None else "T: N/A"
        draw.text((65, 0), temp_str, font=font_large, fill="white")

        # 3. CH2O
        ch2o_str = f"CH2O: {ch2o:.3f}" if ch2o is not None else "CH2O: N/A"
        draw.text((0, 18), ch2o_str, font=font, fill="white")

        # 4. TVOC
        tvoc_str = f"TVOC: {tvoc:.3f}" if tvoc is not None else "TVOC: N/A"
        draw.text((0, 32), tvoc_str, font=font, fill="white")

        # 5. CO2
        co2_val = co2 if co2 is not None else 0
        co2_str = f"CO2: {co2_val:.0f}" if co2_val > 0 else "CO2: N/A"
        draw.text((0, 46), co2_str, font=font, fill="white")


# ===========================


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
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            temp = read_temperature()
            air = read_tvoc_sensor(ser)

            if temp is None and air is None:
                log("传感器数据读取失败，稍后重试。")
                # 【OLED】传感器失败，显示 N/A
                draw_data_on_oled(None, None, None, None, now_str)
            else:
                ch2o = air["CH2O"] if air else None
                tvoc = air["TVOC"] if air else None
                co2 = air["CO2"] if air else None

                # 数据库写入
                cur.execute(
                    f"""
                    INSERT INTO {TABLE_NAME} (timestamp, temp, ch2o, tvoc, co2)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (now_str, temp, ch2o, tvoc, co2),
                )
                conn.commit()
                log(
                    f"写入成功 | T={temp:.2f}°C | CH2O={ch2o:.3f} | TVOC={tvoc:.3f} | CO2={co2:.3f}"
                )

                # 【OLED】数据成功，在屏幕上显示
                draw_data_on_oled(temp, ch2o, tvoc, co2, now_str)

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
