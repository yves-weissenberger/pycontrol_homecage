import pyb
from pyb import Pin
from access_control_upy.access_control_1_0 import Access_control_upy
import time


AC_handler = Access_control_upy()
AC_handler.loadcell.tare()



P_read_en1 = Pin('Y1', Pin.IN, Pin.PULL_UP)
P_read_en2 = Pin('Y2', Pin.IN, Pin.PULL_UP)
P_read_ex1 = Pin('Y3', Pin.IN, Pin.PULL_UP)
P_read_ex2 = Pin('Y4', Pin.IN, Pin.PULL_UP)


P_mag_en1 = pyb.LED(1)#Pin('X1', Pin.OUT_PP)
P_mag_en2 = pyb.LED(2)#Pin('X1', Pin.OUT_PP)
P_mag_ex1 = pyb.LED(3)#Pin('X1', Pin.OUT_PP)
P_mag_ex2 = pyb.LED(4)#Pin('X1', Pin.OUT_PP)

MAGs = [P_mag_en1,P_mag_en2,P_mag_ex1,P_mag_ex2]

mouse_in_training = None
com = pyb.USB_VCP()


NEWSTATE = True
state = 'allow_entry'

for mag in [0,1,2,3]:
    MAGs[mag].off()

weight = AC_handler.loadcell.weigh()
pyb.delay(10)
com.write(str(weight))

while True:

    if state=='allow_entry':

        com.write(state)
        weight = AC_handler.loadcell.weigh()
        pyb.delay(500)
        com.write(str(weight)+'\r')

      