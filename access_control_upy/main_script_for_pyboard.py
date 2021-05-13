import sys
import pyb
from pyb import Pin
from access_control_upy.access_control_1_0 import Access_control_upy
import time
from access_control_upy.pin_classes import signal_pin, magnet_pin




class handler():

    def __init__(self):
        self.init = True

    def run(self):
        myled = pyb.LED(1)
        myled2 = pyb.LED(2)
        myled.on()
        AC_handler = Access_control_upy()
        AC_handler.loadcell.tare()
        micros = pyb.Timer(2, prescaler=83, period=0x3fffffff)   #just a microsecond timer


        enable_pin_1 = pyb.Pin('X11', pyb.Pin.OUT) # Enables/disables the drivers on the + side of doors 1 & 2.
        enable_pin_2 = pyb.Pin('X12', pyb.Pin.OUT) # Enables/disables the drivers on the + side of doors 3 & 4.
        enable_pin_1.value(1) # Enable drivers.
        enable_pin_2.value(1)

        highside_pins = [pyb.Pin(p, pyb.Pin.OUT) for p in ('Y3','Y5','Y12','X6')] # Controls whether + side of door is driven to 12V or 0V. 
        lowside_pins  = [pyb.Pin(p, pyb.Pin.OUT) for p in ('Y4','Y6','Y11','X5')] # Controls whether - side of door is driven to 12V or 0V.
        signal_pins   = [pyb.ADC(p) for p in ('X1','X2','X3','X4')] # Pins used to sense voltage on + side of doors.


        for i in range(4): # Drive both sides of all doors to 0V.
            highside_pins[i].value(0)
            lowside_pins[i].value(0)

        P_read_en1 = signal_pin(signal_pins[0],enable_pin_1,enable_pin_2)#Pin('Y1', Pin.IN, Pin.PULL_UP)
        P_read_en2 = signal_pin(signal_pins[1],enable_pin_1,enable_pin_2)#Pin('Y2', Pin.IN, Pin.PULL_UP)
        P_read_ex1 = signal_pin(signal_pins[2],enable_pin_1,enable_pin_2)#Pin('Y3', Pin.IN, Pin.PULL_UP)
        P_read_ex2 = signal_pin(signal_pins[3],enable_pin_1,enable_pin_2)#Pin('Y4', Pin.IN, Pin.PULL_UP)



        P_mag_en1 = magnet_pin(highside_pins[0],lowside_pins[0])#Pin('X8', Pin.OUT_PP)
        P_mag_en2 = magnet_pin(highside_pins[1],lowside_pins[1])#Pin('X7', Pin.OUT_PP)
        P_mag_ex1 = magnet_pin(highside_pins[2],lowside_pins[2])#Pin('X6', Pin.OUT_PP)
        P_mag_ex2 = magnet_pin(highside_pins[3],lowside_pins[3])#Pin('X5', Pin.OUT_PP)
        

        MAGs = [P_mag_en1,P_mag_en2,P_mag_ex1,P_mag_ex2]

        com = pyb.USB_VCP()

        ONE_MOUSE = 8
        TWO_MICE = 40
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
        mean = lambda x: float(sum(x))/float(len(x))

        state = 'allow_entry'
        ## This is the infinite loop
        #state = 'error_state'
        has_send_error = False
        millis_since_check_wait_close = None
        num_times_checked_for_error = 0  #first check is a variable that basically ensures that a mouse must be stuck for 2 sets of scale readings before an error state is raised
        try:

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
                    weight = AC_handler.loadcell.weigh()
                    if weight>ONE_MOUSE:
                        state = 'wait_close'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                        last_check = micros.counter()
                        MAGs[0].value(1)
                    #if P_read_en1.value():
                    #    state = 'wait_close'
                    #    NEWSTATE = True; pyb.delay(self.forced_delay)
                    #    last_check = micros.counter()
                        
                    

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
                        
                    weight = AC_handler.loadcell.weigh()
                    #if weight>ONE_MOUSE:
                    #    if millis_since_check_wait_close is None:
                    #        millis_since_check_wait_close = pyb.millis()
                    #    
                    #    else:
                    #        if pyb.elapsed_millis(millis_since_check_wait_close)>(300*1000):
                    #            state = 'error_state'

                    if weight<ONE_MOUSE:
                        millis_since_check_wait_close = None
                #in this state check that a mouse has entered the access control system and
                #make sure that it is in fact only 1 mouse in the access control system
                if state=='check_mouse':

                    if NEWSTATE:
                        millis_since_check_wait_close = None
                        com.write(build_msg('state:' + state))
                        NEWSTATE = False

                    weights = []
                    for _ in range(50):
                        weight = AC_handler.loadcell.weigh(times=1)
                        com.write(build_msg('temp_w:' + str(weight)))
                        pyb.delay(10)
                        weights.append(weight)

                        #This is a second check so that the entry door does not stay unnecessarily closed
                        #this value must be greater than 2
                        if ((mean(weights)-self.baseline_read)<ONE_MOUSE and len(weights)>2):
                            break
                    filt_w = [0] + [1./(abs(weights[ix]-j)+abs(weights[ix+2]-j))**2 for ix,j in enumerate(weights[1:-1])] + [0]
                    filt_sum = float(sum(filt_w))
                    filt_w2 = [wtmp/filt_sum for wtmp in filt_w]
                    weight = sum([i*j for i,j in zip(weights,filt_w2)])

                    weight = weight - self.baseline_read
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
                            #rfid = '116000039953'
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
                    weight = AC_handler.loadcell.weigh(times=1)
                    #if P_read_en2.value()==1:
                    if weight<ONE_MOUSE:
                        state = 'check_mouse_in_training'
                        NEWSTATE = True; pyb.delay(self.forced_delay)


                #once the door to the training chamber has closed again, make sure that 
                #the mouse has left
                if state=='check_mouse_in_training':
                    if NEWSTATE:
                        com.write(build_msg('state:' + state))
                        NEWSTATE = False
                        MAGs[1].value(1)

                    #if door entry to chamber is closed again
                    if P_read_en2.value()==0:

                        weight = AC_handler.loadcell.weigh()# - self.baseline_read   #RETURN
                        pyb.delay(10)

                        if weight<ONE_MOUSE:
                            state = 'mouse_training'
                            NEWSTATE = True; pyb.delay(self.forced_delay)
                        else:
                            state = 'enter_training_chamber'
                            NEWSTATE = True; pyb.delay(self.forced_delay)


                if state=='mouse_training': #now the mouse is in the training apparatus
                    if NEWSTATE:
                        com.write(build_msg('state:' + state))
                        NEWSTATE = False
                    
                    for mag in range(4):
                        if mag in [0,1,3]:
                            MAGs[mag].value(1)
                        else:
                            MAGs[mag].value(0)
                    weight = AC_handler.loadcell.weigh()
                    if weight>ONE_MOUSE:
                    #if P_read_ex1.value()==1:
                        state = 'check_mouse_in_ac'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                        MAGs[2].value(1)

                if state=='check_mouse_in_ac':
                    if NEWSTATE:
                        com.write(build_msg('state:' + state))
                        NEWSTATE = False

                    #YVES UPDATE 160221 think this is unncessary
                    #for mag in range(4):
                    #    MAGs[mag].value(1)

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
                    if abs(micros.counter() - last_check)>(10**6):  #do handshake once per second
                        last_check = micros.counter()
                       


                        #if abs(CW-self.baseline_read)<1:
                        Wbase = float(AC_handler.loadcell.weigh(times=1))
                        com.write(build_msg('Wbase:'+str(Wbase)))
                        #com.write(build_msg('Wbase:' + str(Wbase)))

                        #if one Wbase weight is greater than the weight of one mouse, then double check
                        #that weight by weighing 10 times. If that weight is still above the weight of one
                        #mouse, then come back in 1s and check again. If the weight is still too high, go
                        #into an error state
                        if Wbase>ONE_MOUSE:
                            CW = AC_handler.loadcell.weigh(times=2)
                            if float(CW)>ONE_MOUSE:
                                if num_times_checked_for_error>30:
                                    state = 'error_state'
                                    com.write(build_msg('state:' + str(state)))
                                num_times_checked_for_error += 1
                        else:
                            num_times_checked_for_error = 0
                            self.baseline_read = self.baseline_alpha*Wbase + (1-self.baseline_alpha)*self.baseline_read

                if state=='allow_exit':

                    if NEWSTATE:
                        com.write(build_msg('state:' + state))
                        NEWSTATE = False
                    
                    weight = AC_handler.loadcell.weigh(times=1)
                    com.write(build_msg('temp_w_out:' + str(weight)))

                    for mag in range(4):
                        if mag in [0,1,2]:
                            MAGs[mag].value(1)
                        else:
                            MAGs[mag].value(0)

                    if weight<ONE_MOUSE:
                    #if P_read_ex2.value()==1:   #if the door is opened
                        state = 'check_exit'
                        NEWSTATE = True; pyb.delay(self.forced_delay)
                        MAGs[3].value(1)

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



                if state=='error_state':
                    if not has_send_error:
                        com.write(build_msg('state:'+'error_state'))
                        has_send_error = True
                    for mag in range(4):
                        MAGs[mag].value(0)

                sent_data = com.readline()

                if sent_data is not None:
                    sent_data = sent_data.decode('utf8')
                    if sent_data=='tare':

                        AC_handler.loadcell.tare()

                        weight = AC_handler.loadcell.weigh()
                        pyb.delay(10)
                        com.write(build_msg('calT:'+str(weight)))
                    elif 'calibrate' in sent_data:
                        w_ = float(sent_data[10:])
                        AC_handler.loadcell.calibrate(weight=w_)
                        #com.write(build_message(str(sent_data)))

                        weight = AC_handler.loadcell.weigh() 
                        pyb.delay(10)
                        com.write(build_msg('calC:'+str(weight)))

                    elif sent_data=='weigh':

                        weight = AC_handler.loadcell.weigh()
                        pyb.delay(10)
                        com.write(build_msg('calW:'+str(weight)))
        except Exception as e:
            for mag in range(4):
                MAGs[mag].value(0)

            state = 'error_state'
            com.write(build_msg('state:' + str(state)))
            com.write(build_msg(str(e)))
               





