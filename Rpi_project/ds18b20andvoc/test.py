import RPi.GPIO as GPIO
import time
import tm1637

CLK = 2      
DATA = 3     
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)    

d = tm1637.TM1637(CLK, DATA)    
d.showDoublePoint(1)    
temperature='25.86'


d.showData([2,5,8,6])

  

GPIO.cleanup()