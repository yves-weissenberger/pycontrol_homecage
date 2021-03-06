from datetime import datetime
import os
import time
import pandas as pd
import json

from loc_def import mice_dir, protocol_dir
from .data_logger import Data_logger
from config.paths import config_dir, framework_dir, devices_dir, tasks_dir

class system_controller(Data_logger):

    """ This is a class that sits on top of access control and pycboard classes
        and controls data storage for the system as well as setting tasks when 
        mice enter/exit the training apparatus. There is one system controller 
        for each homecage system.
    """
    def __init__(self,GUI,print_func=print,data_consumers=None,setup_id=None):


        self.GUI = GUI
        self.on = True
        self.setup_id = setup_id
        self.has_AC = False
        self.has_PYC = False
        self.data_consumers = data_consumers
        self.analog_files = {}
        self.sm_info = {}
        self.print_func = print_func
        self.active = False
        self.mouse_in_AC = None
        self.data_dir = GUI.paths['data_dir']
        self.data_file = None

        #dict to store data about mice as they are going through
        #the access control system
        self.mouse_data = {'weight': None,
                           'RFID': None,
                           'entry_time': None,
                           'exit_time': None,
                           'task': None,
                           'data_path': None}

    def add_AC(self,ac):

        self.AC = ac
        self.has_AC = True
        
        if self.has_PYC:
            self.active = True

    def add_PYC(self,pyc):

        self.PYC = pyc
        self.has_PYC = True

        if self.has_AC:
            self.active = True


    def disconnect(self):
        """ This needs to be done for when we have multiple setups """

        self.PYC.close() # This closes the connection to the behaviour board
        self.AC.close()  # This closes the connection to AC board by pyboard class


    def check_for_data(self):
        " check whether either AC or the PYC board have data to deliver "
        if self.active:

            self.AC.process_data()
            self.PYC.process_data()  #process data


    def process_data(self, new_data):
        '''If data _file is open new data is written to file.  If print_func is specified
        human readable data strings are passed to it.'''
        if self.data_file:
            self.write_to_file(new_data)
        if self.print_func:
            self.print_func(self.data_to_string(new_data, verbose=True), end='\n')
        if self.data_consumers:
            for data_consumer in self.data_consumers:
                data_consumer.process_data(new_data)

        self.GUI.print_msg(new_data,ac_pyc='pyc')
                
    def process_data_AC(self,new_data):

        """ Here process the data from the access control system to 
            actually do stuff: open/close files, update csv files with
            weights etc

        """
        now = datetime.now().strftime('-%Y-%m-%d-%H%M%S')
        #print(self.GUI.setup_df.loc[self.GUI.setup_df['COM']==self.PYC.serial_port])
        if self.GUI.setup_df.loc[self.GUI.setup_df['COM']==self.PYC.serial_port]['Experiment'].values!='none': #if an experiment is running
            for msg in new_data:
                self.GUI.print_msg(msg)

                if 'cal' in msg:
                    pass
                else:
                    if 'state' in msg: 
                        self.process_ac_state(msg[6:],now)
                    if 'weight' in msg:
                        self.mouse_data['weight'] = float(msg.strip('weight:'))
                    if 'RFID' in msg:
                        self.mouse_data['RFID'] = msg.strip('RFID:')

        else:
            for msg in new_data:
                self.GUI.print_msg(msg,ac_pyc='ac')


    def process_ac_state(self,state,now):
        """ Here do more global updates of stuff based on state """

        #print("HEREIAM",state)
        #
        self.GUI.setup_df.loc[self.GUI.setup_df['COM']==self.PYC.serial_port,'AC_state'] = state

        if state=='allow_entry':

            self.mouse_data = {'weight': None,
                               'RFID': None,
                               'entry_time': None,
                               'exit_time': None,
                               'task': None,
                               'data_path': None}

            


        elif state=='mouse_training':

            if self.data_file is None:
                mouse_row = self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID']]
                mouse_ID = mouse_row['Mouse_ID'].values[0]
                prot = mouse_row['Protocol'].values[0]

                


                if 'task' in prot:
                    task = mouse_row['Task'].values[0]
                    self.PYC.setup_state_machine(sm_name=task)

                else:
                    # If running a real protocol, handle (potential) update of protocol.
                    newStage = False
                    stage = mouse_row['Stage'].values[0]
                    with open(os.path.join(protocol_dir,prot),'r') as f:
                        mouse_prot = json.loads(f.read())

                    #read last stage of training
                    logPth = os.path.join(mice_dir,mouse_ID+'.csv')
                    df_mouseLog = pd.read_csv(logPth)

                    if len(df_mouseLog)>0:

                        df_mouseLog = df_mouseLog.iloc[-1]

                        print('hasLog')
                        v_ = eval(df_mouseLog['Variables'])

                        #handle moving to next stage
                        if mouse_prot[str(stage)]['threshV']:

                            for k,thresh in mouse_prot[str(stage)]['threshV']:
                                print(float(v_[k]),float(thresh),float(v_[k])>=float(thresh))
                                if float(v_[k])>=float(thresh):
                                    newStage = True
                                    stage += 1


                    task = mouse_prot[str(stage)]['task']

                    self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID'],'Task'] = task
                    self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID'],'Stage'] = stage

                    self.PYC.setup_state_machine(sm_name=task)

                    #handle setting varibles

                    for k,defV in mouse_prot[str(stage)]['defaultV']:
                        self.PYC.set_variable(k,float(defV))

                    if len(df_mouseLog)>0:
                        if not newStage:
                            for k in mouse_prot[str(stage)]['trackV']:
                                self.PYC.set_variable(k,float(v_[k]))


                self.mouse_data['entry_time'] = now
                self.mouse_data['task'] = task



                self.open_data_file_(self.mouse_data['RFID'],now)


                self.PYC.start_framework()


                self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID'],'current_weight'] = self.mouse_data['weight']
                self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID'],'is_training'] = True
                self.GUI.setup_df.loc[self.GUI.setup_df['COM']==self.PYC.serial_port,'Mouse_training'] = mouse_ID

                self.GUI.setup_window_tab.list_of_setups.fill_table()
                self.GUI.system_tab.list_of_setups.fill_table()
                hasClosed = False


        elif state=='allow_exit':
            self.mouse_data['exit_time'] = datetime.now().strftime('-%Y-%m-%d-%H%M%S')
            #print("HERE")
            self.PYC.stop_framework()
            time.sleep(.05)
            self.PYC.process_data()
            self.close_files()

    def open_data_file_(self,RFID,now):

        """ Overwrite method of data logger class """
        mouse_row = self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID']]
        mouse_ID = mouse_row['Mouse_ID'].values[0]
        exp =  mouse_row['Experiment'].values[0]
        prot = mouse_row['Protocol'].values[0]
        task = mouse_row['Task'].values[0]

        #pth_ = os.path.join(data_dir,mouse_ID)


        file_name = '_'.join([mouse_ID,exp,task,now]) + '.txt'

        pth_ = os.path.join(self.data_dir,exp,mouse_ID,prot,file_name)
        self.mouse_data['data_path'] = pth_

        with open(os.path.join(tasks_dir,task+'.py'),'r') as f_:
            dat_ = f_.readlines()

            f_backup = open(pth_[:-3] + '_taskFile.txt','w')
            f_backup.writelines(dat_)

        self.data_file = open(pth_, 'w', newline = '\n')

        self.data_file.write('I Experiment name  : {}\n'.format(exp))
        self.data_file.write('I Task name : {}\n'.format(self.sm_info['name']))
        self.data_file.write('I Subject ID : {}\n'.format(mouse_ID))
        self.data_file.write('I Start date : ' + now + '\n\n')
        self.data_file.write('S {}\n\n'.format(self.sm_info['states']))
        self.data_file.write('E {}\n\n'.format(self.sm_info['events']))


    def close_files(self):
        
        if self.data_file:

            self.data_file.writelines("Variables")
            v_ = self.PYC.get_variables()
            self.data_file.writelines(repr(v_))
            self.data_file.close()

            self.update_mouseLog(v_)

            self.data_file = None
            self.file_path = None
        for analog_file in self.analog_files.values():
            if analog_file:
                analog_file.close()
                analog_file = None

    def update_mouseLog(self,v_):

        " Update the log of mouse behavior. v_ are the variables"

        mouse_row = self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==self.mouse_data['RFID']]
        mouse_ID = mouse_row['Mouse_ID'].values[0]

        logPth = os.path.join(mice_dir,mouse_ID+'.csv')
        df_mouseLog = pd.read_csv(logPth)
        
        entry_nr = len(df_mouseLog)
        df_mouseLog.loc[entry_nr] = ['NA']*len(df_mouseLog.columns)

        for k in self.mouse_data.keys():
            if k in df_mouseLog.columns:
                #print(k,self.mouse_data[k])
                df_mouseLog.loc[entry_nr][k] = self.mouse_data[k]

        df_mouseLog.loc[entry_nr]['Variables'] = repr(v_)
        #print(df_mouseLog,entry_nr)

        df_mouseLog.to_csv(logPth)



