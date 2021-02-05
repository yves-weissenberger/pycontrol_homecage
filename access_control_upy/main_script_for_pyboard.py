import pyb
from pyb import Pin
from access_control_upy.access_control_1_0 import Access_control_upy
import time

class handler():

    def __init__(self):
        self.init = True

    def run(self):
        myled = pyb.LED(1)
        myled2 = pyb.LED(2)
        myled.on()
        AC_handler = Access_control_upy()
        AC_handler.loadcell.tare()

        #myled2.on()
        micros = pyb.Timer(2, prescaler=83, period=0x3fffffff)   #just a microsecond timer
        P_read_en1 = Pin('Y1', Pin.IN, Pin.PULL_UP)
        P_read_en2 = Pin('Y2', Pin.IN, Pin.PULL_UP)
        P_read_ex1 = Pin('Y3', Pin.IN, Pin.PULL_UP)
        P_read_ex2 = Pin('Y4', Pin.IN, Pin.PULL_UP)

        #myled2.on()

        P_mag_en1 = Pin('X8', Pin.OUT_PP)
        P_mag_en2 = Pin('X7', Pin.OUT_PP)
        P_mag_ex1 = Pin('X6', Pin.OUT_PP)
        P_mag_ex2 = Pin('X5', Pin.OUT_PP)
        

        MAGs = [P_mag_en1,P_mag_en2,P_mag_ex1,P_mag_ex2]
        #myled2.on()

        mouse_in_training = None
        com = pyb.USB_VCP()

        ONE_MOUSE = 13
        TWO_MICE = 80
        NEWSTATE = True
        state = 'allow_entry'
        build_msg = lambda x: 'start_' + x + '_end'

        com.write(build_msg('state:' + state))
        for mag in [0,1,2,3]:
            MAGs[mag].value(0)  #this should be 0

        myled.off()
        self.baseline_read = 0. 
        self.baseline_alpha = .3
        self.forced_delay = 500
        last_check = micros.counter()
        last_weight = 0 
        mean = lambda x: float(sum(x))/float(len(x))


        ## This is the infinite loop
        while True:

            if state=='allow_entry':
                #last_weight = self.baseline_alpha*AC_handler.loadcell.weigh(times=1) + (1-self.baseline_alpha)*last_weight
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False
                    
                for mag in range(4):
                    if mag in [1,2,3]:
                        MAGs[mag].value(1)
                    else:
                        MAGs[mag].value(0)

                #if the entry door is opened
                if P_read_en1.value():
                    state = 'wait_close'
                    NEWSTATE = True; pyb.delay(self.forced_delay)
                    last_check = micros.counter()
                    
                

            if state=='wait_close':
                
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False




                if P_read_en1.value()==0:  #if entry door is closed again

                    ## This is an extra check step to try to help prevent the door from being unnecessarily closed
                    weight = AC_handler.loadcell.weigh()
                    if weight<ONE_MOUSE:
                        state = 'allow_entry'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                        last_check = micros.counter()
                    else:
                        for mag in range(4):
                            MAGs[mag].value(1)

                        state = 'check_mouse'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                        last_check = micros.counter()
                    

            #in this state check that a mouse has entered the access control system and
            #make sure that it is in fact only 1 mouse in the access control system
            if state=='check_mouse':

                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False

                weights = []
                for _ in range(50):
                    weight = AC_handler.loadcell.weigh()
                    com.write(build_msg('temp_w:' + str(weight)))
                    pyb.delay(10)
                    weights.append(weight)

                    #This is a second check so that the entry door does not stay unnecessarily closed
                    if ((mean(weights)-self.baseline_read)<ONE_MOUSE and len(weights)>1):
                        break

                weight = mean(weights) #- self.baseline_read
                #weight = 25
                com.write(build_msg('weight:' + str(weight)))

                #if more than one mouse got in
                if weight>TWO_MICE:
                    com.write('2 mice')
                    state = 'allow_exit'
                    NEWSTATE = True; pyb.delay(self.forced_delay)
                elif weight<ONE_MOUSE:
                    com.write('0 mice')
                    state = 'allow_entry'
                    NEWSTATE = True; pyb.delay(self.forced_delay)
                else:
                    com.write('1 mice')
                    com.write(build_msg('weight:' + str(weight)))
                    getRFID = True
                    st_check = time.time()
                    while getRFID:
                        rfid = AC_handler.rfid.read_tag()
                        pyb.delay(50)
                        #rfid = '116000039959'
                        #if read an RFID TAG
                        if rfid is not None:
                            com.write(build_msg('RFID:' + str(rfid)))
                            getRFID = False
                            state = 'enter_training_chamber'
                            NEWSTATE = True; pyb.delay(self.forced_delay) 


                        #if no RFID tag read in 20s
                        if (time.time() - st_check)>30:
                            getRFID = False
                            state = 'allow_exit'

            else:
                rfid = AC_handler.rfid.read_tag()
                rfid = None



            #in this state allow a mouse to leave the access control system and
            #move into the training room. Once the door to the training room has
            #opened leave this state
            if state=='enter_training_chamber':

                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False
                for mag in range(4):
                    if mag in [0,2,3]:
                        MAGs[mag].value(1)
                    else:
                        MAGs[mag].value(0)

                #if the mouse had opened the door to training chamber
                if P_read_en2.value()==1:
                    state = 'check_mouse_in_training'
                    NEWSTATE = True; pyb.delay(self.forced_delay)


            #once the door to the training chamber has closed again, make sure that 
            #the mouse has left
            if state=='check_mouse_in_training':
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False
                #if door entry to chamber is closed again
                if P_read_en2.value()==0:

                    weight = AC_handler.loadcell.weigh()# - self.baseline_read
                    pyb.delay(10)

                    if weight<ONE_MOUSE:
                        state = 'mouse_training'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                    else:
                        state = 'enter_training_chamber'
                        NEWSTATE = True; pyb.delay(self.forced_delay)

            if state=='mouse_training': #now the mouse is in the training apparatus
                last_weight = AC_handler.loadcell.weigh(times=1)
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False

                for mag in range(4):
                    if mag in [0,1,3]:
                        MAGs[mag].value(1)
                    else:
                        MAGs[mag].value(0)

                if P_read_ex1.value()==1:
                    state = 'check_mouse_in_ac'
                    NEWSTATE = True; pyb.delay(self.forced_delay)

            if state=='check_mouse_in_ac':
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False

                for mag in range(4):
                    MAGs[mag].value(1)

                if P_read_ex1.value()==0:

                    weight = AC_handler.loadcell.weigh()# - self.baseline_read
                    pyb.delay(10)
                    
                    if weight<ONE_MOUSE: #in this case the mouse opened and closed the door without going back into the training room
                        state = 'mouse_training'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                    else:
                        state = 'allow_exit'
                        NEWSTATE = True; pyb.delay(self.forced_delay)


            if (state=='mouse_training') or (state=='allow_entry'):
                ##here re-baseline the scale
                if abs(micros.counter() - last_check)>500000:
                    last_check = micros.counter()
                    CW = AC_handler.loadcell.weigh(times=1)


                    #if abs(CW-self.baseline_read)<1:
                    Wbase = float(AC_handler.loadcell.weigh(times=1))
                    self.baseline_read = self.baseline_alpha*Wbase + (1-self.baseline_alpha)*self.baseline_read
                    com.write(build_msg('Wbase:'+str(Wbase)))
                    #com.write(build_msg('Wbase:' + str(Wbase)))

            if state=='allow_exit':

                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False
                    
                for mag in range(4):
                    if mag in [0,1,2]:
                        MAGs[mag].value(1)
                    else:
                        MAGs[mag].value(0)


                if P_read_ex2.value()==1:   #if the door is opened
                    state = 'check_exit'
                    NEWSTATE = True; pyb.delay(self.forced_delay)

            if state=='check_exit':
                if NEWSTATE:
                    com.write(build_msg('state:' + state))
                    NEWSTATE = False

                if P_read_ex2.value()==0:  #if exit door is closed

                    weight = AC_handler.loadcell.weigh() - self.baseline_read
                    pyb.delay(10)
                    
                    if weight<ONE_MOUSE: #in this case the mouse has left and we restart
                        state = 'allow_entry'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                    else:
                        state = 'allow_exit'
                        NEWSTATE = True; pyb.delay(self.forced_delay)


            sent_data = com.readline()

            if sent_data is not None:
                sent_data = sent_data.decode('utf8')
                if sent_data=='tare':

                    AC_handler.loadcell.tare()

                    weight = AC_handler.loadcell.weigh() - self.baseline_read
                    pyb.delay(10)
                    com.write(build_msg('calT:'+str(weight)))
                elif 'calibrate' in sent_data:
                    w_ = float(sent_data[10:])
                    AC_handler.loadcell.calibrate(weight=w_)
                    #com.write(build_message(str(sent_data)))

                    weight = AC_handler.loadcell.weigh() - self.baseline_read
                    pyb.delay(10)
                    com.write(build_msg('calC:'+str(weight)))

                elif sent_data=='weigh':

                    weight = AC_handler.loadcell.weigh() - self.baseline_read
                    pyb.delay(10)
                    com.write(build_msg('calW:'+str(weight)))






