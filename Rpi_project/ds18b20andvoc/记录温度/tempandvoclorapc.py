# pc_receiver_db.py - PC 端 LoRa 数据接收、存储到 SQLite 数据库并打印
import serial
import time
import json
import sqlite3
from datetime import datetime

# === 串口和数据库配置 ===
SERIAL_PORT = '/dev/ttyUSB0' # <-- ***请修改为 PC 上的实际串口号***
BAUD_RATE = 9600
DB_PATH = 'temp_ds.db'      # 数据库文件路径（将在脚本运行目录下创建）
TABLE_NAME = 'tempanvoc'

def setup_database():
    """连接数据库并创建数据表"""
    try:
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
        print(f"✅ 数据库连接成功，表 '{TABLE_NAME}' 已准备就绪。")
        return conn, cur
    except sqlite3.Error as e:
        print(f"❌ 数据库初始化失败: {e}")
        return None, None

def insert_data(conn, cur, data: dict):
    """将解析后的数据插入数据库"""
    try:
        # 提取数据，如果不存在则使用 None (SQLITE 会存为 NULL)
        timestamp = data.get('ts')
        temp = float(data.get('temp', '0').replace('N/A', '0'))
        ch2o = float(data.get('ch2o', '0').replace('N/A', '0'))
        tvoc = float(data.get('tvoc', '0').replace('N/A', '0'))
        co2 = float(data.get('co2', '0').replace('N/A', '0'))
        
        # 插入数据
        cur.execute(f"""
            INSERT INTO {TABLE_NAME} (timestamp, temp, ch2o, tvoc, co2)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, temp, ch2o, tvoc, co2))
        conn.commit()
        print("💾 数据已成功存入数据库。")
        
    except (ValueError, TypeError, sqlite3.Error) as e:
        print(f"❌ 数据库写入失败或数据类型转换错误: {e}")

def main():
    conn, cur = setup_database()
    if not conn:
        return

    try:
        # 初始化串口连接
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
            # 1. 接收数据 (阻塞式 readline)
            raw_data = ser.readline().decode('utf-8').strip()
            
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
                    print(f"  CO2 : {data.get('co2')} ppm")
                    print("---------------------------------------------------")
                    
                    # 4. 存入数据库
                    insert_data(conn, cur, data)
                    
                except json.JSONDecodeError:
                    print(f"\n⚠️ [{datetime.now().strftime('%H:%M:%S')}] 接收到非 JSON 数据或数据不完整:")
                    print(f"   原始数据: {raw_data}")
                
        except Exception as e:
            print(f"\n❌ 运行时错误: {e}")
            time.sleep(1) 

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序终止。")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("数据库连接已关闭。")