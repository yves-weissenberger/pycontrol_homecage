import smtplib, ssl
from datetime import date, timedelta
from datetime import datetime
import numpy as np
import re
import os
from utils import get_users, get_user_dicts
from loc_def import user_path, all_paths
import json
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
            weight_dict[mouseID+'__now_weight'] = now_weight
            weight_dict[mouseID+'__last_seen'] = last_seen
            weight_dict[mouseID+'__baseline'] = baseline
            weight_dict[mouseID+'__frac_baseline'] = frac_baseline



    return weight_dict,warn

def construct_warning_message(logger_active,ac_state,weight_dict):
    warning_message = "SOMETHING IS WRONG, CHECK NOW!" \
                  + json.dumps(ac_state,indent=4) + '\n' + json.dumps(weight_dict,indent=4) + '\n' +  json.dumps(logger_active,indent=4)
    return warning_message

def send_email(send_message,subject,receiver_email,opening=None):
    """ This function actually send an email"""
    lines_ = open(user_path,'r').readlines()
    users = get_users()
    sender_email = [re.findall('"(.*)"',l)[0] for l in lines_ if "system_email" in l][0]
    password = [re.findall('"(.*)"',l)[0] for l in lines_ if "password" in l][0]


    message = MIMEMultipart("alternative")
    message["Subject"] = "Pyhomecage 24h summary"
    message["From"] = sender_email
    message["To"] = receiver_email


    if opening is None:
        opening = """\
                This is an automated message from pycontrol

        """
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(opening, "plain")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(send_message)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )
    return None
def send_regular_update(mouse_dict,receiver_email):
    mouse_IDs = np.unique([re.findall(r'(.*)__',k) for k in mouse_dict.keys()])

    rows = []
    for mouseID in mouse_IDs:
        last_seen = datetime.strptime( mouse_dict[mouseID+'__last_seen'],'%Y-%m-%d-%H%M%S')
        rows.append({'MouseID': mouseID,
                    'Baseline': mouse_dict[mouseID+'__baseline'],
                    'Current_weight': mouse_dict[mouseID+'__now_weight'],
                    'frac_baseline': mouse_dict[mouseID+'__frac_baseline'],
                    'last_seen': mouse_dict[mouseID+'__last_seen'],
                    'hours_since_last_visit': np.round((datetime.now()-last_seen).total_seconds()/3600.,decimals=1)})
    df = pd.DataFrame.from_dict(rows, orient='columns')
    message = MIMEText(df.to_html(), "html")
    send_email(message,subject='Daily Update',receiver_email=receiver_email) 

if __name__=='__main__':

    users = get_users(); user_dicts = get_user_dicts()
    ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths

    last_check = datetime.now()
    warning_checkDict = {}
    for u in users:
        if u not in warning_checkDict.keys():
            warning_checkDict[u] = datetime.now() - timedelta(days=1)

    last_regular_update = datetime.now() - timedelta(days=2)
    while True:
        now = datetime.now()
        #print(now,last_check)
        if abs((now-last_check)).seconds>10:
            print(now)
            users = get_users(); user_dicts = get_user_dicts()
            for u in users:
                if u not in warning_checkDict.keys():
                    warning_checkDict[u] = datetime.now() - timedelta(days=1)

            all_mice_csv = pd.read_csv(os.path.join(mice_dir,'mice.csv'))

            for user in users:

                logger_active,w1 = check_loggers_running(user)

                ac_state,w2 = check_ac_status(user)

                weight_dict, w3 = check_mouse_weights(user,all_mice_csv)

                if (abs(now-last_regular_update).total_seconds()/3600.)>24:
                    send_regular_update(weight_dict,user_dicts[user])
                    last_regular_update = datetime.now()

                if any([w1,w2,w3]) and (((datetime.now()-warning_checkDict[u]).total_seconds()/3600.)>1):
                    print('SENDING WARNING')
                    warning_message = construct_warning_message(logger_active,ac_state,weight_dict)
                    warning_message = MIMEText(warning_message)
                    send_email(warning_message,'WARNING',user_dicts[user])
                    warning_checkDict[u] = datetime.now()


            last_check = datetime.now()


