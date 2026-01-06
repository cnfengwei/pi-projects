#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集 DS18B20 温度和 VOC 传感器数据，并通过 LoRa 模块发送到 PC 端。
使用 /dev/serial0 硬件 UART 进行 LoRa 通信。
使用 pigpio 软件 UART 读取 VOC 传感器。
LoRa 的通讯接口连接到 GPIO UART (TXD: GPIO14, RXD: GPIO15)。必须使用硬件默认 UART。
信道是 23，地址是 1，两个地址都要设置成一样的。若地址不一样，则无法通信。
"""
import os
import time
import serial
import json
import RPi.GPIO as GPIO
import pigpio
from datetime import datetime
from w1thermsensor import W1ThermSensor


# ==================================
# === 配置区 (请根据实际情况修改) ===
# ==================================

# --- LoRa 模块配置 (使用硬件 UART) ---
LORA_PORT = '/dev/serial0'
LORA_BAUD = 9600
M0_PIN = 9     # LoRa M0 引脚 (BCM 编号)
M1_PIN = 10    # LoRa M1 引脚 (BCM 编号)

# --- VOC 传感器配置 (使用软件 UART) ---
VOC_BAUD = 9600
VOC_RX_PIN = 21  # 软件 UART 接收引脚
VOC_TX_PIN = 20  # 软件 UART 发送引脚
DATA_FRAME_LENGTH = 9
MODULE_ADDR_H = 0x2C
MODULE_ADDR_L = 0xE4

# --- 程序控制 ---每5秒采集并发送一次数据
INTERVAL_SECONDS = 5
LOG_FILE = '/home/fengweipi/lora_voc_sender.log'

# ==================================

def log(msg: str):
    """写入日志文件"""
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
    except Exception:
        pass


def setup_lora_mode(mode='normal'):
    """通过 GPIO 设置 LoRa 模块模式"""
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(M0_PIN, GPIO.OUT)
    GPIO.setup(M1_PIN, GPIO.OUT)

    level = GPIO.LOW if mode == 'normal' else GPIO.HIGH
    GPIO.output(M0_PIN, level)
    GPIO.output(M1_PIN, level)

    mode_name = "透传模式" if mode == 'normal' else "配置模式"
    log(f"LoRa 模块 M0/M1 已切换到 {mode_name}。")
    time.sleep(0.1)


def calculate_checksum(data):
    """计算 VOC 数据的校验和"""
    return sum(data[0:8]) & 0xFF if len(data) >= 8 else -1


def read_tvoc_sensor(pi):
    """使用 pigpio 软件 UART 读取 TVOC/CH2O/CO2 数据"""
    try:
        pi.bb_serial_read_open(VOC_RX_PIN, VOC_BAUD)
        pi.bb_serial_read_open(VOC_TX_PIN, VOC_BAUD)

        log("等待读取 VOC 传感器数据...")
        start_time = time.time()
        raw = []

        while time.time() - start_time < 2:
            count, data = pi.bb_serial_read(VOC_RX_PIN)
            if count > 0:
                raw.extend(data)
                if len(raw) >= DATA_FRAME_LENGTH:
                    break
            time.sleep(0.01)

        if len(raw) < DATA_FRAME_LENGTH:
            log(f"读取 VOC 失败: 只收到 {len(raw)} 个字节。")
            return None

        data = list(raw[-DATA_FRAME_LENGTH:])

        if data[0] != MODULE_ADDR_H or data[1] != MODULE_ADDR_L:
            log("VOC 校验失败: 模块地址不匹配。")
            return None
        if data[8] != calculate_checksum(data):
            log(f"VOC 校验失败: 校验和错误。计算 {calculate_checksum(data)} != 接收 {data[8]}。")
            return None

        tvoc = (data[2] * 256 + data[3]) * 0.001
        ch2o = (data[4] * 256 + data[5]) * 0.001
        co2 = (data[6] * 256 + data[7]) * 0.001
        return {"TVOC": tvoc, "CH2O": ch2o, "CO2": co2}

    except Exception as e:
        log(f"读取 TVOC 传感器时发生 pigpio 错误: {e}")
        return None
    finally:
        try:
            pi.bb_serial_read_close(VOC_RX_PIN)
        except Exception:
            pass
        try:
            pi.bb_serial_read_close(VOC_TX_PIN)
        except Exception:
            pass


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


def send_lora_data(lora_ser, payload: dict):
    """将数据打包成 JSON，并通过 LoRa 模块发送"""
    try:
        json_data = json.dumps(payload)
        data_to_send = (json_data + '\n').encode('utf-8')
        lora_ser.write(data_to_send)
        log(f"LoRa 发送成功: {json_data}")
    except Exception as e:
        log(f"LoRa 发送失败: {e}")


def open_lora_serial():
    """尝试打开 LoRa 串口"""
    try:
        lora_ser = serial.Serial(LORA_PORT, LORA_BAUD, timeout=2)
        log(f"LoRa 串口已打开: {LORA_PORT}")
        return lora_ser
    except Exception as e:
        log(f"LoRa 串口打开失败: {e}")
        return None


def main():
    log("==== 启动 LoRa 采集与发送程序 ====")

    try:
        setup_lora_mode('normal')
        lora_ser = open_lora_serial()
        if not lora_ser:
            return

        pi = pigpio.pi()
        if not pi.connected:
            log("❌ pigpiod 服务未运行或连接失败，无法读取 VOC 传感器。")
            return

    except Exception as e:
        log(f"初始化失败: {e}")
        return

    counter = 1
    while True:
        try:
            temp = read_temperature()
            air = read_tvoc_sensor(pi)

            ch2o = air.get('CH2O') if air else None
            tvoc = air.get('TVOC') if air else None
            co2 = air.get('CO2') if air else None

            payload = {
                "id": counter,
                "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "temp": f"{temp:.2f}" if temp is not None else "N/A",
                "ch2o": f"{ch2o:.3f}" if ch2o is not None else "N/A",
                "tvoc": f"{tvoc:.3f}" if tvoc is not None else "N/A",
                "co2": f"{co2:.3f}" if co2 is not None else "N/A"
            }

            send_lora_data(lora_ser, payload)
            counter += 1

        except serial.SerialException as e:
            log(f"LoRa 串口错误: {e}")
            time.sleep(5)
            lora_ser = open_lora_serial()
        except Exception as e:
            log(f"未知错误: {e}")
            time.sleep(5)

        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("用户终止程序。")
    except Exception as e:
        log(f"致命错误: {e}")
    finally:
        try:
            GPIO.cleanup()
            pigpio.pi().stop()
        except Exception:
            pass
