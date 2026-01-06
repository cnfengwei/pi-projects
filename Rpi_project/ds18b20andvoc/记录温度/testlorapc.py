# pc_receiver.py - PC LoRa 接收端代码
import serial
import time
import json
from datetime import datetime
import sys

# === LoRa 模块配置 ===
SERIAL_PORT = '/dev/ttyUSB0' # <-- ***请修改为 PC 上的实际串口号***
BAUD_RATE = 9600

def main():
    try:
        # 初始化串口连接
        # timeout=None 设置为阻塞式读取，等待直到收到数据
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=None) 
        print("===================================================")
        print(f"✅ 串口 {SERIAL_PORT} @ {BAUD_RATE} 已打开。")
        print("等待接收来自 Pi 端的 LoRa 数据...")
        print("===================================================")
    except serial.SerialException as e:
        print(f"❌ 串口打开失败，请检查串口号是否正确，或是否被占用: {e}")
        return

    while True:
        try:
            # 1. 接收数据
            # readline() 会一直读取直到遇到换行符 ('\n')，与 Pi 端的发送匹配
            raw_data = ser.readline().decode('utf-8').strip()
            print(f"接收到原始数据: {raw_data}")
            if raw_data:
                # 2. 解析 JSON
                try:
                    data = json.loads(raw_data)
                    
                    # 3. 打印解析结果
                    print("\n---------------------------------------------------")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 接收到数据包 (ID: {data.get('id', 'N/A')})")
                    print("---------------------------------------------------")
                    
                    print(f"  时间戳 : {data.get('ts')}")
                    print(f"  温度 (T): {data.get('temp')} °C")
                    print(f"  甲醛 (CH2O): {data.get('ch2o')} mg/m³")
                    print(f"  TVOC : {data.get('tvoc')} mg/m³")
                    print(f"  CO2 : {data.get('co2')} ppm (如果已配置)")
                    print("---------------------------------------------------")
                    
                except json.JSONDecodeError:
                    print(f"\n⚠️ [{datetime.now().strftime('%H:%M:%S')}] 接收到非 JSON 数据或数据不完整:")
                    print(f"   原始数据: {raw_data}")
                
        except serial.SerialTimeoutException:
            # timeout=None，理论上不会超时，但为了健壮性保留
            continue 
        except Exception as e:
            print(f"\n❌ 读取或处理数据时发生错误: {e}")
            time.sleep(1) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序终止。")
    except Exception as e:
        print(f"\n发生致命错误: {e}")