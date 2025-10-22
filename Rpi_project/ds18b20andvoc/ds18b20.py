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

# import RPi.GPIO as GPIO
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# 使用该软件上拉时，只有当程序将 GPIO 引脚上拉时，内核才能看到 1 线设备。

# Hw 设备连接验证
# 运行以下命令

# ls -l /sys/bus/w1/devices
# 检查是否有一个或多个以 "28-"开头的文件名。

# 以 "00-"开头的文件名可能意味着缺少上拉电阻。

# 单线设备可以动态插入，内核驱动程序可以在其 hw 连接后看到这些设备。
# 要测试温度读数，请发出以下命令:在cmd里
# for i in /sys/bus/w1/devices/28-*; do cat $i/w1_slave; done

#28-01226304075d传感器的id号
#https://circuitdigest.com/microcontroller-projects/raspberry-pi-ds18b20-temperature-sensor-interfacing
from w1thermsensor import W1ThermSensor#模块在https://pypi.org/project/w1thermsensor/
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
    # 设置 GPIO 编号
    # W1ThermSensor.set_default_gpio(17)  # 使用 GPIO17
    temperature = read_temperature()
    if temperature is not None:
        print(f"当前温度: {temperature:.2f} 摄氏度 ")
    