from datetime import date, timedelta
from datetime import datetime
import re
import os
from utils import get_users, get_user_dicts
from loc_def import user_path, all_paths
from emailer import send_email
import json
import pandas as pd
from email.mime.text import MIMEText

#This is a basic script that runs, independently of pycontrol and looks for errors


def check_loggers_running(user):
    """ run through active loggers and ensure that
        baseline weight message has been received recently 
    """

    setup_df = pd.read_csv(os.path.join(setup_dir,'setups.csv'))
    setup_rows = setup_df.loc[setup_df['User']==user]
    active_dict = {}
    warn = False
    now = datetime.now()
    for _,setup_row in setup_rows.iterrows():

        logger_path = setup_row['logger_path']
        logger_line = open(logger_path,'r').readlines()[-1]
        last_time_str = re.findall(r'_-(20.*)',logger_line)[0]  #-2021-03-19-125542
        last_time = datetime.strptime(last_time_str,'%Y-%m-%d-%H%M%S')

        last_delta = (now-last_time).total_seconds()
        active_dict[setup_row['Setup_ID']] = last_time.strftime("%m/%d/%Y, %H:%M:%S")
        if last_delta>20: warn = True
    return active_dict,warn

def check_ac_status(user):
    """ Check system state to ensure that no warning message 
        has been received
    """

    setup_df = pd.read_csv(os.path.join(setup_dir,'setups.csv'))
    setup_rows = setup_df.loc[setup_df['User']==user]
    #print(setup_rows)
    logger_state = {}
    warn = False
    for _,setup_row in setup_rows.iterrows():

        logger_path = setup_row['logger_path']
        logger_lines = open(logger_path,'r').readlines()

        for l in reversed(logger_lines):

            if 'state' in l:
                current_state = re.findall('state:(.*)_-2',l)[0]

                break
        if current_state=='error_state':
            logger_state[setup_row['Setup_ID']] = current_state
            warn = True
        else:
            logger_state[setup_row['Setup_ID']] = 'GOOD'
    return logger_state, warn


def check_mouse_weights(user,all_mouse_csv):
    weight_dict = {}
    warn = False
    now = datetime.now()
    for _,mouse_row in all_mouse_csv.iterrows():
        if mouse_row['User']==user:
            mouseID = mouse_row['Mouse_ID']
            baseline = mouse_row['Start_weight']
            mouse_csv = pd.read_csv(os.path.join(mice_dir,mouseID + '.csv'))
            now_weight = mouse_csv.iloc[-1]['weight']
            last_seen = mouse_csv.iloc[-1]['entry_time'][1:]
            frac_baseline = float(now_weight)/float(baseline)
            last_seen_datetime = datetime.strptime(last_seen,'%Y-%m-%d-%H%M%S')

            delta = (last_seen_datetime-now)
            time_delta_hours = delta.days * 24 + delta.seconds/3600
            if time_delta_hours>24:
                warn = True
            if frac_baseline<0.88:
                warn = True
            weight_dict[mouseID+'now_weight'] = now_weight
            weight_dict[mouseID+'last_seen'] = last_seen
            weight_dict[mouseID+'baseline'] = baseline
            weight_dict[mouseID+'frac_baseline'] = frac_baseline



    return weight_dict,warn

def construct_warning_message(logger_active,ac_state,weight_dict):
    warning_message = "SOMETHING IS WRONG, CHECK NOW!" \
                  + json.dumps(ac_state,indent=4) + '\n' + json.dumps(weight_dict,indent=4) + '\n' +  json.dumps(logger_active,indent=4)
    return warning_message


if __name__=='__main__':

    users = get_users(); user_dicts = get_user_dicts()
    ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths

    last_check = datetime.now()
    warning_checkDict = {}
    for u in users:
        if u not in warning_checkDict.keys():
            warning_checkDict[u] = datetime.now() - timedelta(days=1)

    while True:
        now = datetime.now()
        #print(now,last_check)
        if abs((now-last_check)).seconds>1:
            users = get_users(); user_dicts = get_user_dicts()
            for u in users:
                if u not in warning_checkDict.keys():
                    warning_checkDict[u] = datetime.now() - timedelta(days=1)

            all_mice_csv = pd.read_csv(os.path.join(mice_dir,'mice.csv'))

            for user in users:

                logger_active,w1 = check_loggers_running(user)

                ac_state,w2 = check_ac_status(user)

                weight_dict, w3 = check_mouse_weights(user,all_mice_csv)
                if any([w1,w2,w3]) and (((datetime.now()-warning_checkDict[u]).total_seconds()/3600.)>1):
                    print('SENDING WARNING')
                    warning_message = construct_warning_message(logger_active,ac_state,weight_dict)
                    warning_message = MIMEText(warning_message)
                    send_email(warning_message,'WARNING',user_dicts[user])
                    warning_checkDict[u] = datetime.now()


            last_check = datetime.now()


