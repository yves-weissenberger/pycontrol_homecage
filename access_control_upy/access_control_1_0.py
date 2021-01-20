from .hx711_spi import HX711
from .uRFID import uRFID
import time
class Access_control_upy():
    # Class instantiated on the pyboard mounted on the Access Control 1.0 PCB.

    def __init__(self):
        self.loadcell = HX711(data_pin='Y7',clock_pin='Y8', SPI_clk_pin='Y6')
        self.rfid = uRFID(bus=4)

    #def 
"""
Explanation of states and names


allow_entry:    allow a mouse to enter the access control system. All doors closed except for en1
wait_close:


"""
#list of states = []

#state = 'allow_entry'
#state = 'allow_exit'



""" 



P_read_en1 = Pin('Y1', Pin.IN)
P_read_en2 = Pin('Y2', Pin.IN)
P_read_ex1 = Pin('X3', Pin.IN)
P_read_ex2 = Pin('X4', Pin.IN)

P_mag_en1 = Pin('X1', Pin.OUT_PP)
P_mag_en2 = Pin('X1', Pin.OUT_PP)
P_mag_ex1 = Pin('X1', Pin.OUT_PP)
P_mag_en2 = Pin('X1', Pin.OUT_PP)

#Default all doors closed
P_mag_en1.value(1)
P_mag_en2.value(1)
P_mag_ex1.value(1)
P_mag_ex2.value(1)


mouse_in_training = None

while True:

    if state=='allow_entry':

        P_mag_en1.value(0)
        P_mag_en2.value(1)
        P_mag_ex1.value(1)
        P_mag_ex2.value(1)

        #if the entry door is opened
        if P_read_en1.value()==0:
            state = 'wait_close'
            P_mag_en1.value(1)
        

    if state=='wait_close':

        if P_read_en1.value()==1:  #if entry door is closed again
            state = 'check_mouse'
            

    if state=='check mouse':
        st_check = time.time()

        weights = []
        rfids = []
        #check for 5s
        while (time.time() - st_check)<5:
            weight = weigh()
            read_rfid = read_rfid()
            weights.append(weight)
            rfids.append(read_rfid)


        uniq_rfid = list(set([i for i in rfids if i is not None]))

        if len(uniq_rfid)!=1:
            state = 'allow_exit'


        #mouse opened but then backed out
        if weight<10:  
            state = 'allow_entry'

        #more than 1 mouse is inside
        elif weight>40:
            state = 'allow_exit'

        #there is one mouse in the weighing box
        else:
            state = 'enter_training_chamber'


    if state=='enter_training_chamber':
        P_mag_en1.value(1)
        P_mag_en2.value(0)
        P_mag_ex1.value(1)
        P_mag_ex2.value(1)

        #if the mouse had opened the door to training chamber
        if P_read_en2.value()==0:
            state = 'check_mouse_in_training'


    if state=='check_mouse_in_training':

        #if door entry to chamber is closed again
        if P_read_en2.value()==1:
            weight = weigh()
            if weight<10:
                state='mouse_training'
            elif weight>40:
                state = 'allow_exit'
            else:
                state = 'enter_training_chamber'

            

    if state=='mouse_training':
        P_mag_en1.value(1)
        P_mag_en2.value(1)
        P_mag_ex1.value(0)
        P_mag_ex2.value(1)
        if P_read_ex1.value()==0:
            state = 'check_mouse_in_ac'


    if state =='check_mouse_in_ac':
        #check whether mouse is exiting the training room and
        #is now inside the access control module




    if state=='allow_exit':

        P_mag_en1.value(1)
        P_mag_en2.value(1)
        P_mag_ex1.value(1)
        P_mag_ex2.value(0)


        
        if P_read_ex2.value()==0:
            state = 'check_cleared'
    

    if state=='check_cleared':
        #in this state check that mouse has exited
        weight = weigh()
        if (P_read_ex2.value()==1):
            if weight<10:
                state = 'allow_entry'
            else:
                state = 'allow_exit'

    



"""