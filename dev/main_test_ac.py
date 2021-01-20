# main.py -- put your code here!
# This code has been adapted from http://docs.micropython.org/en/latest/pyboard/pyboard/tutorial/leds.html

import pyb
from pyb import Pin
from access_control_upy.access_control_1_0 import Access_control_upy


AC_handler = Access_control_upy()
#create an leds array with 4 LED objects
leds = [pyb.LED(i) for i in range(1,5)]
p_out = Pin('X8', Pin.OUT_PP)

pd1 = Pin('Y1', Pin.IN, Pin.PULL_UP)
pd2 = Pin('Y2', Pin.IN, Pin.PULL_UP)
pd3 = Pin('Y3', Pin.IN, Pin.PULL_UP)
pd4 = Pin('Y4', Pin.IN, Pin.PULL_UP)

#turn off all 4 LEDs
for l in leds:
    l.off()

n = 3

com = pyb.USB_VCP()

p_out.high()
pyb.delay(1500)
p_out.low()



#try and finally - https://docs.python.org/2.5/whatsnew/pep-341.html
try:
    while True:
        #get the remainders 1-4 by using modulus function
        #Use 0-3 to toggle each LED on and off - note that
        #leds[0] is the same as pyb.LED(1)

        if pd1.value()==0:
            leds[0].toggle()
            rfid = AC_handler.rfid.read_tag()
            if rfid is not None:
                com.write(str(rfid))
            pyb.delay(500)
        elif pd2.value()==0:
            leds[1].toggle()
            #AC_handler
            pyb.delay(500)
        elif pd3.value()==0:
            leds[2].toggle()
            pyb.delay(500)
        elif pd4.value()==0:
            leds[3].toggle()
            pyb.delay(500)

        for l in leds:
            l.off()
        #n = (n + 1) % 4
        #leds[n].toggle()
        #p_out.high()
        #pyb.delay(500)
        #p_out.low()

finally:
    for l in leds:
        l.off()