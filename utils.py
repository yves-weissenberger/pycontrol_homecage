import pandas as pd
import os
import re
from loc_def import user_path, all_paths

from serial.tools import list_ports


def find_setups(GUI):

    #print(list_ports.comports())
    ports = list(set([c[0] for c in list_ports.comports() if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])]))
    #ports =[i for i in ports if i not in GUI.setup_df['COM'].tolist()]
    return ports

def get_variables_from_taskfile(pth):
    "Helper function to scan python script and return variables in that script"
    with open(pth,'r') as f:
        txt = f.read()
    #print(txt)
    variables = re.findall(r'(v\.[^ ]*) {0,2}=',txt)
    variables = list(set(variables))
    return variables

def get_users():
    users = open(user_path,'r')
    #users = [i.readline() for i in users]
    users = [str(usr.strip()) for usr in users]
    return users

def load_data_csv():

    ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths
    fp = os.path.join(task_dir,'tasks.csv')
    task_df = pd.read_csv(fp)
    task_df.file_location = fp

    fp = os.path.join(experiment_dir,'experiments.csv')
    exp_df = pd.read_csv(fp)
    exp_df.file_location = fp

    fp = os.path.join(setup_dir,'setups.csv')
    setup_df = pd.read_csv(fp)
    setup_df.file_location = fp

    fp = os.path.join(mice_dir,'mice.csv')
    mouse_df = pd.read_csv(fp)
    mouse_df.file_location = fp

    return task_df,exp_df,setup_df,mouse_df

def get_tasks(GUI_fp):
    """ Function to read available tasks from the tasks folder """
    
    task_dir = os.path.join(GUI_fp,'tasks')
    tasks =  [t.split('.')[0] for t in os.listdir(task_dir) if t[-3:] == '.py']
    return tasks
