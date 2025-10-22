import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# 使用该软件上拉时，只有当程序将 GPIO 引脚上拉时，内核才能看到 1 线设备。
device_file ='/sys/bus/w1/devices/28-01226304075d/w1_slave'
file = open(device_file, 'r') #opent the file
lines = file.readlines() #read the lines in the file 
file.close() #close the file 
trimmed_data = lines[1].find('t=') #find the "t=" in the line
temp_string = lines[1][trimmed_data+2:] #trim the strig only to the temoerature value
temp_c = float(temp_string) / 1000.0 #divide the value of 1000 to get actual value

