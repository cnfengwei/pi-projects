from max31855 import MAX31855, MAX31855Error

#max31855K芯片是K型热电偶的驱动芯片，
#cs_pin为GPIO8脚（spi CE0），链接模块的CS脚，低电平有效片选。CS置为低电平时，使能串口。
#clock_pini为GPIO11（spi sclk），连接模块的CLK脚，串行时钟输入
#data_pin为GPIO9（spi MISO）也可以设为GPIO10（SPI MOSI）连接DO脚（串行数据输出）
cs_pin = 8
clock_pin = 11
data_pin = 10
units = "c" #设置为摄氏度，F为华氏度，K为凯尔文
thermocouple = MAX31855(cs_pin, clock_pin, data_pin, units)
print(thermocouple.get())
thermocouple.cleanup()

