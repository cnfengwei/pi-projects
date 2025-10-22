#VCC +5V
#TRIG=23
#ECHO=24 ,要求输出3.3V    ECHO------------------------
#                                                | 1K电阻
#                        24  --------------------|                      
#                                                | 2K电阻
#                        GND ---------------------


import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

TRIG = 23
ECHO =24

GPIO.setup(TRIG,GPIO.OUT)
GPIO.setup(ECHO,GPIO.IN)

try:
     while True:
        GPIO.output(TRIG,False)
        print("dd")
        time.sleep(2)

        GPIO.output(TRIG,True)
        time.sleep(0.00001)
        GPIO.output(TRIG,False)

        while GPIO.input(ECHO) == 0:
            pulse_start= time.time()
        while GPIO.input(ECHO) == 1 :
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance,2)
        print ("distance:",distance,"cm") 
except KeyboardInterrupt:
    print("clear up")
    GPIO.cleanup()