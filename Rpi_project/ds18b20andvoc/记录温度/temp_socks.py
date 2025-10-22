import time
import sqlite3
from w1thermsensor import W1ThermSensor#模块在https://pypi.org/project/w1thermsensor/
import socket

#获取ds18b20的温度值，将温度值每隔30秒插入到数据库temp_ds.dbo中
#导入socket,等待数据请求，当客户端请求时，将温度数值传输到客户端
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
    mydb=sqlite3.connect('temp_ds.db')
   
    mycur = mydb.cursor()
    total_runtime_hours = 72
    total_runtime_seconds = total_runtime_hours * 60 * 60
    # 创建一个TCP/IP套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 绑定套接字到一个特定的地址和端口
    server_address = ('0.0.0.0', 12345)  # 0.0.0.0 表示接受所有可用的网络接口
    server_socket.bind(server_address)

    # 开始监听连接
    server_socket.listen(1)

    print('等待连接...')
    connection, client_address = server_socket.accept()
    print('连接来自：', client_address)
    # 设置每次运行间隔为 30 秒
    interval_seconds = 30
    try:
        while True:
            # 模拟温度数据
            temperature = read_temperature()

            # 将温度数据转换为字节并发送
            connection.sendall(str(temperature).encode('utf-8'))
            
            query = "INSERT INTO temp_list (temp) VALUES (?); "
            mycur.execute(query, (temperature,))
            mydb.commit()
            print(f"当前温度: {temperature:.2f} 摄氏度 ")
            time.sleep(interval_seconds)
           

    finally:
        # 清理连接
        connection.close()
        server_socket.close()
    
    

  


    
