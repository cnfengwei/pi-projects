#首先安装pip install pymodbus
#pip install pyserial
#终端运行命令ls /dev/tty*，查找端口号

import time
from pymodbus import Framer
from pymodbus.client import ModbusSerialClient
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s '
          '%(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)
from pymodbus.client import ModbusSerialClient 
# 设置串口参数，根据实际情况修改
#serial_port = '/dev/ttyUSB0'
baud_rate = 9600
#serial_port = 'COM7'
serial_port = '/dev/ttyUSB0'
# 创建 Modbus RTU 串口客户端
client = ModbusSerialClient(
    port=serial_port,
    baudrate=baud_rate,
    timeout=1
)
#method='rtu',
# 尝试连接到 Modbus RTU 设备
client.connect()
  



#第一个参数为读取第几个通道的数值，第二个参数为读取几个数值，第三个参数为从站地址
#（0,8，1）从第1个通道开始读取数值，读取8个寄存器的数值【20,21,22,23,24,25,26,27】
#（7,1,1）从第8通道开始读取，只读取一个数值【27】
#rr = client.read_holding_registers(3,1,1)

#rr= client.read_input_registers(0,1,1)
       

# # 发送 Modbus RTU 读取指令rr.bits为读取线圈，rr.registers为读取寄存器指令，如果未返回正确的指令，程序将会
#报错，提示没有registers这个object
# response = rr.registers
# print(response)
# # print(response)
# # # 读取的数值为FCD4,那么就是一个无符号的整数
# # #读取的数值除10,得到的是正确数值
# # # 如果数值为FCD4,那么就是一个有符号的整数
# import time
# for i in range(0,100):
#     print(response[3])
#     time.sleep(0.5)

# # # 读取的数值为FCD4,那么就是一个有符号的整数
# # # 首先，将 FCD4 转换为二进制表示：1111110011010100。
# # # 由于最高位是1，表示这是一个负数。
# # # 对所有位进行取反操作得到 0000001100101011。
# # # 然后，将结果加1得到 0000001100101100。
# # # 最后，将二进制数 0000001100101100 转换为十进制，得到 -812
# temperature = int(response[3]) / 10

# # print(temperature)
#更改从机的地址指令，30表示要写入的寄存器地址，寄存器地址30为设备地址，8是将
#寄存器30的值改为8，1表示从机地址
#client.write_register(30,8,1)
# client.close()

temperature_register = client.read_holding_registers(0, 8, 1)
temperature = temperature_register.registers
i = 0

# 判断读取是否成功
if temperature_register.registers:
    # 遍历读取到的寄存器值
    for value in temperature_register.registers:
        # 将读取到的值转换为温度值
        if value > 32767:
            value = value - 65536  # 进行符号位扩展
        temperature = value / 10
        i += 1

        # 打印温度值
        print(str(i) + f'    温度：{temperature}℃')
else:
    print('读取温度值失败')

# 关闭串口连接
client.close()
