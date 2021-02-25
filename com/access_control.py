import os
import re
from serial import SerialException
from .pyboard import Pyboard, PyboardError
from config.paths import config_dir, accCtrl_dir, devices_dir, tasks_dir,framework_dir
from datetime import datetime

class Access_control(Pyboard):
    # Class that runs on the main computer to provide an API for inferfacting with
    # the access control module

    def __init__(self, serial_port, print_func=print, baudrate=115200,data_logger=None,GUI=None):

        self.serial_port = serial_port
        self.print = print_func        # Function used for print statements.
        self.data_logger = data_logger
        self.prev_read = None
        self.rfid = None
        self.weight = None
        self.status = {'serial': None, 
                       'framework': None, 
                       'usb_mode': None}
        self.GUI = GUI

        name_ = self.GUI.setup_df.loc[self.GUI.setup_df['COM_AC']==self.serial_port,'Setup_ID'].values[0]
        #print(name_)
        now = datetime.now().strftime('-%Y-%m-%d-%H%M%S')
        self.logger_dir = GUI.paths['AC_logger_dir']
        self.logger_path = os.path.join(self.logger_dir,name_ + '_' + now + '.txt')
        #self.GUI.setup_df

        with open(self.logger_path,'w') as f:
            f.write("Start"+'\n')
            f.write(now+'\n')


        try:    
            super().__init__(self.serial_port, baudrate=115200)
            self.status['serial'] = True
            self.reset() # Soft resets pyboard.
            self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
            v_tuple = eval(self.eval(
            "sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)").decode())
            self.micropython_version = float('{}.{}{}'.format(*v_tuple))

        except SerialException as e:
            print('Could not connect to pyboard')
            self.status['serial'] = False

            raise(e)


    def load_framework(self, framework_dir=framework_dir,accCtrl_dir=accCtrl_dir):
        '''Copy the pyControl framework folder to the board.'''
        #print(framework_dir)
        self.print('\nTransfering access control framework to pyboard.', end='')
        #self.transfer_folder(framework_dir, file_type='py', show_progress=True)  #upload pycontrol framework
        self.transfer_folder(accCtrl_dir, file_type='py', show_progress=True)    #upload access control framework
        self.transfer_folder(devices_dir  , file_type='py', show_progress=True)
        self.transfer_file(os.path.join(accCtrl_dir,'main_script_for_pyboard.py'),'main.py')

        try:
            self.exec('from access_control_upy.access_control_1_0 import Access_control_upy')
        except PyboardError as e:
            print('Could not import access control upy modules.')
            raise(e)
        try:
            self.exec('access_control = Access_control_upy()')
        except PyboardError as e:
            print('Could not instantiate Access_control.')
            raise(e)
        try:
            self.exec('from main import handler')
            self.exec_raw_no_follow('handler().run()')
            #print(self.eval('print(run)'))
        except PyboardError as e:
            raise(e)
        #self.exec('run()')
        print("OK")
        return 


    def process_data(self):
        """ Here process data from buffer to update dataframes """
        ## Just send each message as being 16 characters long. That way
        ## can just check padding. Should be fine

        #requires GUI, or other object with access to dataframes to be here

        #df_ = self.data_logger.GUI.setup_df
        if self.data_logger.GUI is not None:
                #print('!!!!!!!!!')

                if self.serial.inWaiting()>0:
                    #read the input if something is coming
                    read = str(self.serial.read(self.serial.inWaiting()))
                    #print(read)


                    messages = re.findall('start_(.*?)_end',read)
                    for msg in messages:
                        with open(self.logger_path,'a') as f:
                            f.write(msg+'_'+datetime.now().strftime('-%Y-%m-%d-%H%M%S')+'\n')


                    for msg in messages:
                        #This is a horrible information flow. The point is simply to print into the calibrate dialog
                        if 'cal' in msg:
                            #print(msg)
                            if self.GUI.setup_window_tab.callibrate_dialog:
                                self.GUI.setup_window_tab.callibrate_dialog.print_msg(msg)

                    self.data_logger.process_data_AC(messages)



    def _handle_lock_update(self,msg):
        "LEGACY Stupid helper function to convert the state of door magnets to human readable string"
        msg2 = msg.strip('lock:')
        door_state = ''

        if msg2[0]=='0':
            door_state = door_state + 'En1_closed'
        else:
            door_state = door_state + 'En1_open'

        if msg2[1]=='0':
            door_state = door_state + 'En2_closed'
        else:
            door_state = door_state + 'En2_open'


        if msg2[2]=='0':
            door_state = door_state + 'Ex1_closed'
        else:
            door_state = door_state + 'Ex1_open'

        if msg2[3]=='0':
            door_state = door_state + 'Ex2_closed'
        else:
            door_state = door_state + 'Ex2_open'

        return door_state

    def loadcell_tare(self):
        self.exec('access_control.loadcell.tare()')

    def loadcell_calibrate(self, weight):
        self.exec('access_control.loadcell.calibrate({})'.format(weight))

    def loadcell_weigh(self):
        return float(self.eval('access_control.loadcell.weigh()').decode())

    def rfid_read_tag(self):
        return eval(self.eval('access_control.rfid.read_tag()').decode())


