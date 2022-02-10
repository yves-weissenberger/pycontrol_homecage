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


while True:

    if state=='allow_entry':

        if NEWSTATE:
            com.write(state)
            NEWSTATE = False
            
        for mag in range(4):
            if mag in [1,2,3]:
                MAGs[mag].on()
            else:
                MAGs[mag].off()

        #if the entry door is opened
        if P_read_en1.value()==0:
            state = 'wait_close'
            NEWSTATE = True
            
        

    if state=='wait_close':
    
        if NEWSTATE:
            com.write(state)
            NEWSTATE = False


        for mag in range(4):
            MAGs[mag].on()


        if P_read_en1.value()==1:  #if entry door is closed again
            state = 'check_mouse'
            NEWSTATE = True
            

    #in this state check that a mouse has entered the access control system and
    #make sure that it is in fact only 1 mouse in the access control system
    if state=='check_mouse':

        if NEWSTATE:
            com.write(state)
            NEWSTATE = False

        weights = []
        for _ in range(10):
            weight = AC_handler.loadcell.weigh()
            pyb.delay(10)
            weights.append(weight)

        weight = sum(weights)/float(len(weights))
        

        #if more than one mouse got in
        if weight>120000:
            com.write('2 mice')
            state = 'allow_exit'
            NEWSTATE = True
        elif weight<20000:
            com.write('0 mice')
            state = 'allow_entry'
            NEWSTATE = True
        else:
            com.write('1 mice')
            com.write(str(weight))
            getRFID = True
            st_check = time.time()
            while getRFID:
                rfid = AC_handler.rfid.read_tag()
                pyb.delay(50)
                #if read an RFID TAG
                if rfid is not None:
                    com.write(str(rfid))
                    getRFID = False
                    state = 'enter_training_chamber'
                    NEWSTATE = True 


                #if no RFID tag read in 20s
                if (time.time() - st_check)>30:
                    getRFID = False
                    state = 'allow_exit'
                    NEWSTATE = True


    #in this state allow a mouse to leave the access control system and
    #move into the training room. Once the door to the training room has
    #opened leave this state
    if state=='enter_training_chamber':

        if NEWSTATE:
            com.write(state)
            NEWSTATE = False
        for mag in range(4):
            if mag in [0,2,3]:
                MAGs[mag].on()
            else:
                MAGs[mag].off()

        #if the mouse had opened the door to training chamber
        if P_read_en2.value()==0:
            state = 'check_mouse_in_training'
            NEWSTATE = True


    #once the door to the training chamber has closed again, make sure that 
    #the mouse has left
    if state=='check_mouse_in_training':
        if NEWSTATE:
            com.write(state)
            NEWSTATE = False
        #if door entry to chamber is closed again
        if P_read_en2.value()==1:

            weight = AC_handler.loadcell.weigh()
            pyb.delay(10)

            if weight<20000:
                state = 'mouse_training'
                NEWSTATE = True
            else:
                state = 'enter_training_chamber'
                NEWSTATE = True

    if state=='mouse_training': #now the mouse is in the training apparatus
        if NEWSTATE:
            com.write(state)
            NEWSTATE = False

        for mag in range(4):
            if mag in [0,1,3]:
                MAGs[mag].on()
            else:
                MAGs[mag].off()

        if P_read_ex1.value()==0:
            state = 'check_mouse_in_ac'
            NEWSTATE = True

    if state=='check_mouse_in_ac':
        if NEWSTATE:
            com.write(state)
            NEWSTATE = False

        for mag in range(4):
            MAGs[mag].on()

        if P_read_ex1.value()==1:

            weight = AC_handler.loadcell.weigh()
            pyb.delay(10)
            
            if weight<20000: #in this case the mouse opened and closed the door without going back into the training room
                state = 'mouse_training'
                NEWSTATE = True
            else:
                state = 'allow_exit'
                NEWSTATE = True



    if state=='allow_exit':

        if NEWSTATE:
            com.write(state)
            NEWSTATE = False
            
        for mag in range(4):
            if mag in [0,1,2]:
                MAGs[mag].on()
            else:
                MAGs[mag].off()


        if P_read_ex2.value()==0:   #if the door is opened
            state = 'check_exit'
            NEWSTATE = True

    if state=='check_exit':
        if NEWSTATE:
            com.write(state)
            NEWSTATE = False

        if P_read_ex2.value()==1:  #if exit door is closed

            weight = AC_handler.loadcell.weigh()
            pyb.delay(10)
            
            if weight<20000: #in this case the mouse has left and we restart
                state = 'allow_entry'
                NEWSTATE = True
            else:
                state = 'allow_exit'
                NEWSTATE = True


