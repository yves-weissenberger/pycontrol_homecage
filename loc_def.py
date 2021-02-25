import sys
import os
import pandas as pd

ROOT = r'C:\Users\yweissenberger\Desktop\pyhomecage'
if not os.path.isdir(ROOT):
    os.mkdir(ROOT)

data_dir = os.path.join(ROOT,'data')
task_dir = os.path.join(ROOT,'tasks')
setup_dir = os.path.join(ROOT,'setups')
AC_logger_dir = os.path.join(setup_dir,'loggers')
experiment_dir = os.path.join(ROOT,'experiments')
mice_dir = os.path.join(ROOT,'mice')
protocol_dir = os.path.join(ROOT,'prot')


user_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)),'users.txt')


all_paths = [ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir]


def create_paths(all_paths):

    for ctr,pth in enumerate(all_paths[1:]):
        if not os.path.isdir(pth):
            os.mkdir(pth)
        create_empty_csv(ctr,pth)


#Experiment defines the overall experiment that is being run with these mice
#Protocol defines the current protocol, within a given experiment that is beign use
#User defines what user is currently using this setup
#
def create_empty_csv(index,pth):

    fp = None
    #set variables for tasks, what to store about them
    if index==0:
        df = pd.DataFrame(columns=['Name','User_added'])
        fp = os.path.join(pth,'tasks.csv')


    #set variables for experiments what to store about them
    elif index==1:
        df = pd.DataFrame(columns=['Name','Setups','Subjects','n_subjects','User','Protocol','Active','Persistent_variables'])
        fp = os.path.join(pth,'experiments.csv')

    #set variables for setups what to store about them
    elif index==2:
        df = pd.DataFrame(columns=['Setup_ID','COM','COM_AC','in_use','connected','User',
                                   'Experiment','Protocol','Mouse_training','AC_state','Door_Mag','Door_Sensor','n_mice',
                                   'mice_in_setup'])
        fp = os.path.join(pth,'setups.csv')

    #set variables for mice what to store about them
    elif index==3:
        df = pd.DataFrame(columns=['Mouse_ID','RFID','Sex','Age','Experiment',
                                   'Protocol','Stage','Task','User','Start_date','Current_weight',
                                   'Start_weight','is_training','is_assigned',
                                   'training_log','Setup_ID','in_system'])
        fp = os.path.join(pth,'mice.csv')

    if (fp is not None) and (not os.path.isfile(fp)):
        df.to_csv(fp,index=False)
