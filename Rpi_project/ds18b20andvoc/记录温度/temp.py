from datetime import datetime
import time
import sqlite3
from w1thermsensor import W1ThermSensor#模块在https://pypi.org/project/w1thermsensor/
# Raspi VCC (3V3) Pin 1 -----------------------------   VCC    DS18B20
#                                                |
#                                                |
#                                                R1 = 4k7 ...10k
#                                                |
#                                                |
# Raspi GPIO 4    Pin 7 -----------------------------   Data   DS18B20
#        (BCM)    (BOARD)

# Raspi GND       Pin 6 -----------------------------   GND    DS18B20
#默认使用GPIO 4 脚进行连接
# 除了使用物理电阻进行硬件上拉，或在 /boot/config.txt 中进行上述软件配置外，还可以使用以下软上拉：dtoverlay=w1-gpio,pullup="y"

#import RPi.GPIO as GPIO
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# 使用该软件上拉时，只有当程序将 GPIO 引脚上拉时，内核才能看到 1 线设备。
#但是不建议使用上拉电阻，因为它们可能会干扰总线上的其他设备。不稳定
# 设备连接验证
# 运行以下命令

# ls -l /sys/bus/w1/devices
# 检查是否有一个或多个以 "28-"开头的文件名。

# 以 "00-"开头的文件名可能意味着缺少上拉电阻。

# 单线设备可以动态插入，内核驱动程序可以在其 hw 连接后看到这些设备。
# 要测试温度读数，请发出以下命令:在cmd里
# for i in /sys/bus/w1/devices/28-*; do cat $i/w1_slave; done

#28-01226304075d传感器的id号
#获取ds18b20的温度值，将温度值每隔30秒插入到数据库temp_ds.dbo中
#将ds18b20的数据线插入到树莓派的GPIO4引脚上，该程序可以运行
def read_temperature():
    # 获取 DS18B20 传感器列表
    sensors = W1ThermSensor.get_available_sensors()
    
    if sensors:
        # 获取第一个传感器的温度
        temperature_in_celsius = sensors[0].get_temperature()
        return temperature_in_celsius
    else:
        print("未找到 DS18B20 传感器")
if __name__ == "__main__":
   
    mydb=sqlite3.connect('temp_ds.db')
   
    mycur = mydb.cursor()
    total_runtime_hours = 72
    total_runtime_seconds = total_runtime_hours * 60 * 60

    # 设置每次运行间隔为 5 秒
    interval_seconds = 30


    
    while True:
        temperature = read_temperature()
        query = "INSERT INTO temp_list (temp) VALUES (?); "
        mycur.execute(query, (temperature,))
        mydb.commit()
        # 获取当前时间
        current_time = datetime.now()

        # 将时间对象格式化为字符串
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"当前温度: {temperature:.2f} 摄氏度 "+formatted_time)
        time.sleep(interval_seconds)
    
