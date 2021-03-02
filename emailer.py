import smtplib, ssl
import re
from loc_def import user_path, all_paths
from utils import get_users
from datetime import date, timedelta
from datetime import datetime
import pandas as pd
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

lines_ = open(user_path,'r').readlines()
users = get_users()
sender_email = [re.findall('"(.*)"',l)[0] for l in lines_ if "system_email" in l][0]
password = [re.findall('"(.*)"',l)[0] for l in lines_ if "password" in l][0]

port = 587  # For starttls
smtp_server = "smtp.gmail.com"
receiver_email = 'yvesweissenberger@gmail.com'

message = MIMEMultipart("alternative")
message["Subject"] = "Pyhomecage 24h summary"
message["From"] = sender_email
message["To"] = receiver_email



def get_weight_history(logger_path):

    """ Go through the access control file and get the weight measurements over the last 24h
        as well as the times that the homecage was accessed"""
    now = datetime.now()
    yesterday =date.today() - timedelta(days=1)
    logger_lines = open(logger_path,'r').readlines()

    mouse_dict = {}
    for lix,l in enumerate(logger_lines):
        if 'RFID' in l:
            rfid = re.findall('RFID:([0-9]*)_',l)[0] #RFID:116000039953_-2021-02-23-103009
            time = re.findall('-(20.*)',l)[0]
            weight = re.findall('weight:(.*)_',logger_lines[lix-1])[0]

            time_dt = datetime.strptime(time,'%Y-%m-%d-%H%M%S')

            if (now-time_dt).total_seconds()<(24*60*60):

                if rfid in mouse_dict.keys():
                    mouse_dict[rfid].append([time,weight])
                else:
                    mouse_dict[rfid] = [time,weight]
    return mouse_dict

def get_behaviour_dat(root_path):
    now = datetime.now()

    fs = os.listdir(root_path)
    root_path = os.path.join(root_path,fs[0])
    fs = os.listdir(root_path)
    tot_rews = 0
    for f in fs:
        if 'taskFile' not in f:
            time = re.findall('-(20.*).txt',f)[0]
            time_dt = datetime.strptime(time,'%Y-%m-%d-%H%M%S')
            if (now-time_dt).total_seconds()<(24*60*60):
                tmp = [0]
                #print(f)
                for l in open(os.path.join(root_path,f),'r').readlines():
                    if 'nREWS' in l:
                        tmp.append(float(re.findall('nREWS:([0-9]{1,4})',l)[0]))
                nRews = max(tmp)
                #dat = eval(open(os.path.join(root_path,f),'r').readlines()[-1][9:])
                tot_rews += nRews


    return tot_rews



tmp_logP = r"C:\Users\yweissenberger\Desktop\pyhomecage\setups\loggers\test1_-2021-02-23-102859.txt"
mouse_dict = get_weight_history(tmp_logP)
#print(mouse_dict)
ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths



mouse_df =  pd.read_csv(os.path.join(mice_dir,'mice.csv'))
#print(mouse_df)

send_mouse_df = pd.DataFrame(columns=['Mouse','last_seen','last_weight','baseline_weight','number_of_visits','current_task','Experiment','n_rewards'])
#print(mouse_dict.keys())
for k,d in mouse_dict.items():


    tmp = {}
    tmp['Experiment'] = str(mouse_df.loc[mouse_df['RFID']==int(k),'Experiment'].values[0])
    tmp['Mouse'] = k
    tmp['last_seen'] = d[-1][0]
    tmp['last_weight'] = float(d[-1][1])/1.9
    tmp['baseline_weight'] = int(mouse_df.loc[mouse_df['RFID']==int(k),'Start_weight'])
    tmp['number_of_visits'] = len(d)
    tmp['current_task'] = str(mouse_df.loc[mouse_df['RFID']==int(k),'Task'].values[0])

    mouse_id = str(mouse_df.loc[mouse_df['RFID']==int(k),'Mouse_ID'].values[0])
    dat_path = os.path.join(data_dir,tmp['Experiment'],mouse_id)
    beh_dat = get_behaviour_dat(dat_path)
    tmp['n_rewards'] = beh_dat
    #print(tmp)
    send_mouse_df = send_mouse_df.append(tmp.copy(),ignore_index=True)

#print(send_mouse_df)
opening = """\
Subject: Hi there,

here is the scheduled 24h update on your mice




"""



# Turn these into plain/html MIMEText objects
part1 = MIMEText(opening, "plain")
part2 = MIMEText( send_mouse_df.to_html(), "html")

# Add HTML/plain-text parts to MIMEMultipart message
# The email client will try to render the last part first
message.attach(part1)
message.attach(part2)

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
    server.login(sender_email, password)
    server.sendmail(
        sender_email, receiver_email, message.as_string()
    )