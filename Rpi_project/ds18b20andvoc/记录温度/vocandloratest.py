import serial, time

voc = serial.Serial('/dev/ttyAMA4', 9600, timeout=1)
lora = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)

print("VOC → LoRa 数据转发启动...")

while True:
    if voc.in_waiting:
        data = voc.readline().decode(errors='ignore').strip()
        if data:
            print(f"[VOC] {data}")
            lora.write((data + "\n").encode())
            print(f"已通过 LoRa 发送: {data}")
    else:
        print("等待 VOC 数据中...")
    time.sleep(1)
