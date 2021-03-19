import datetime
import re
from utils import get_users, get_user_dicts
from loc_def import user_path, all_paths
from emailer import send_email

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
    for setup_row in setup_rows:

        tmp_logP = setup_row['logger_path']
        logger_line = open(logger_path,'r').readlines()[-1]
        last_time_str = re.findall(r'_-(20.*)',logger_line)[0]  #-2021-03-19-125542
        last_time = datetime.strptime(last_time_str,'%Y-%m-%d-%H%M%S')

        last_delta = (now-last_time).seconds
        active_dict[setup_row['Setup_ID']] = last_delta
        if last_delta>20: warn = True
    return active_dict,warn

def check_ac_status(user):
    """ Check system state to ensure that no warning message 
        has been received
    """

    setup_df = pd.read_csv(os.path.join(setup_dir,'setups.csv'))
    setup_rows = setup_df.loc[setup_df['User']==user]

    logger_state = {}
    warn = False
    for setup_row in setup_rows:

        tmp_logP = setup_row['logger_path']
        logger_lines = open(logger_path,'r').readlines()

        for l in reversed(lines):

            if 'state' in l:
                current_state = re.findall('state:(.*)_-2')[0]

                break
        if current_state=='error_state':
            logger_state[setup_row['Setup_ID']] = current_state
            warn = True
    return logger_state, warn


def check_mouse_weights(user):

    return weight_dict,warn

def construct_warning_message(logger_active,ac_state,weight_dict):
    warning_message = "SOMETHING IS WRONG, CHECK NOW!"
    return warning_message
last_routine_update = now
last_check = now


if __name_=='__main__'

    users = get_users(); user_dicts = get_user_dicts()
    ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths

    now = datetime.now()
    last_check = now
    while True:

        now = datetime.now()
        if abs((now-last_check)).seconds>10:

            for user in users:

                logger_active,w1 = check_loggers_running(user)

                ac_state,w2 = check_ac_status(user)

                weight_dict, w3 = check_mouse_weights(user)


                if any([w1,w2,w3]):
                    warning_message = construct_warning_message(logger_active,ac_state,weight_dict)
                    send_email('WARNING',warning_message,user_dicts[user])



