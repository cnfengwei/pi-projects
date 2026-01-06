# pc_sender_test.py - PC 端 LoRa 数据发送测试脚本
import serial
import time
from datetime import datetime
import sys

# === 配置区 (请根据实际情况修改) ===
SERIAL_PORT = '/dev/ttyUSB0' # <-- ***请修改为 PC 上的实际串口号 (例如：COM3 或 /dev/ttyUSB0)***
BAUD_RATE = 9600
INTERVAL_SECONDS = 5        # 每 5 秒发送一次

def send_test_data(ser, counter):
    """发送测试数据到串口"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 构建测试消息
    message = f"PC_TEST_ID:{counter}, TIME:{timestamp}\n"
    data_to_send = message.encode('utf-8')
    
    try:
        # 写入数据到串口
        bytes_written = ser.write(data_to_send)
        
        # 确认是否发送成功的关键：检查写入的字节数
        if bytes_written == len(data_to_send):
            print(f"[{timestamp}] ✅ 发送成功: {bytes_written} bytes | '{message.strip()}'")
        else:
            print(f"[{timestamp}] ⚠️ 发送警告: 期望 {len(data_to_send)} bytes, 实际写入 {bytes_written} bytes")
        
    except serial.SerialTimeoutException:
        print(f"[{timestamp}] ❌ 写入超时。")
    except Exception as e:
        print(f"[{timestamp}] ❌ 写入错误: {e}")

def main():
    # 确保 M0/M1 处于透传模式 (连接到 GND)
    print("---------------------------------------------------")
    print("请确认 PC 端 LoRa 模块 M0/M1 已连接到 GND (透传模式)。")
    print("---------------------------------------------------")

    try:
        # 初始化串口连接
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2, write_timeout=2) 
        print(f"✅ 串口 {SERIAL_PORT} @ {BAUD_RATE} 已打开。")
    except serial.SerialException as e:
        print(f"❌ 串口打开失败: {e}")
        return

    counter = 1
    while True:
        send_test_data(ser, counter)
        counter += 1
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户终止程序。")
    except Exception as e:
        print(f"\n发生致命错误: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口连接已关闭。")