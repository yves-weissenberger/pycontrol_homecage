from typing import List, Tuple
import os
import re
import sys
import traceback
from datetime import datetime
from enum import Enum

import pandas as pd
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from serial.tools import list_ports


from pycontrol_homecage.utils.loc_def import user_path, all_paths, task_dir


def custom_excepthook(type_, exception, traceback_, filepath):
    """ A custom exception hook that prints
        exceptions to a file so that they can then be used as alerts
        for an email daemon
    """
    now = datetime.strftime(datetime.now(), '%Y-%m-%d-%H%M%S')

    with open(filepath, 'a') as f:
        f.write('----------------- \n')
        f.write(repr(type_))
        f.write(repr(exception))
        traceback.print_exception(type_, exception, traceback_, file=f)
        f.write(now + '\n')
    sys._excepthook(type_, exception, traceback)


# --------------------------------------------------------------------------------

def null_resize(widget):
    '''Call a widgets resize event with its current size.  Used when rows are added
    by user to tables to prevent mangling of the table layout.'''
    size = QtCore.QSize(widget.frameGeometry().width(), widget.frameGeometry().height())
    resize = QtGui.QResizeEvent(size, size)
    widget.resizeEvent(resize)


# --------------------------------------------------------------------------------





# --------------------------------------------------------------------------------



class TableCheckbox(QtGui.QWidget):
    '''Checkbox that is centered in cell when placed in table.'''

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        self.checkbox = QtGui.QCheckBox(parent=parent)
        self.layout = QtGui.QHBoxLayout(self)
        self.layout.addWidget(self.checkbox)
        self.layout.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def isChecked(self):
        return self.checkbox.isChecked()

    def setChecked(self, state):
        self.checkbox.setChecked(state)

# --------------------------------------------------------------------------------


def cbox_update_options(cbox, options):
    '''Update the options available in a qcombobox without changing the selection.'''
    selected = str(cbox.currentText())
    available = sorted(list(set([selected]+options)))
    i = available.index(selected)
    cbox.clear()
    cbox.addItems(available)
    cbox.setCurrentIndex(i)


def cbox_set_item(cbox, item_name, insert=False) -> bool:
    '''Set the selected item in a combobox to the name provided.  If name is
    not in item list returns False if insert is False or inserts item if insert
    is True.'''
    index = cbox.findText(item_name, QtCore.Qt.MatchFixedString)
    if index >= 0:
        cbox.setCurrentIndex(index)
        return True
    else:
        if insert:
            cbox.insertItem(0, item_name)
            cbox.setCurrentIndex(0)
            return True
        else:
            return False
# ----------------------------------------------------------------------------------


def get_pyhomecage_email() -> Tuple[str, str]:
    """ Return email and password of the system email account """
    lines_ = open(user_path, 'r').readlines()
    sender_email = re.findall('"(.*)"', [l_ for l_ in lines_ if 'system_email' in l_][0])[0]
    password = re.findall('"(.*)"', [l_ for l_ in lines_ if 'password' in l_][0])[0]
    return sender_email, password


def find_setups():

    ports = list(set([c[0] for c in list_ports.comports() if ('Pyboard' in c[1]) or ('USB Serial Device' in c[1])]))
    return ports


def get_variables_from_taskfile(pth: str) -> List[str]:
    "Helper function to scan python script and return variables in that script"
    with open(pth, 'r') as f:
        txt = f.read()

    variables = re.findall(r'(v\.[^\s ]*) {0,2}=', txt)
    variables = list(set(variables))
    return variables


def get_variables_and_values_from_taskfile(pth: str) -> dict[str, str]:
    "Helper function to scan python script and return variables in that script"
    with open(pth, 'r') as f:
        txt = f.readlines()

    var_dict = {}
    for line in txt:
        if ('v.' in line) and ('=' in line):
            var_ = re.findall(r'(v\.[^\s]*)', line)[0].strip()
            val_ = re.findall(r'v\..*=(.*)[#|\n]', line)[0]
            var_dict[var_] = val_
        if 'run_start' in line:
            break

    return var_dict


def get_users() -> List[str]:
    dat = open(user_path, 'r').readlines()
    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    users = list(user_dict.keys())
    return users


def get_user_dicts() -> dict[str, str]:
    dat = open(user_path, 'r').readlines()

    user_dat = [re.findall(r'({.*})', l_)[0] for l_ in dat if 'user_data' in l_]
    user_dict_list = [eval(i) for i in user_dat]
    user_dict = {k: v for d in user_dict_list for k, v in d.items()}
    return user_dict


def load_data_csv() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:

    ROOT, task_dir, experiment_dir, setup_dir, mice_dir, data_dir, AC_logger_dir, protocol_dir = all_paths
    fp = os.path.join(task_dir, 'tasks.csv')
    task_df = pd.read_csv(fp)
    task_df.file_location = fp

    fp = os.path.join(experiment_dir, 'experiments.csv')
    exp_df = pd.read_csv(fp)
    exp_df.file_location = fp

    fp = os.path.join(setup_dir, 'setups.csv')
    setup_df = pd.read_csv(fp)
    setup_df.file_location = fp

    fp = os.path.join(mice_dir, 'mice.csv')
    mouse_df = pd.read_csv(fp)
    mouse_df.file_location = fp

    for col in mouse_df.columns:
        if 'Unnamed' in col:
            mouse_df.drop(col, inplace=True, axis=1)

    return task_df, exp_df, setup_df, mouse_df


def get_tasks() -> List[str]:
    """ Function to read available tasks from the tasks folder """

    tasks = [t.split('.')[0] for t in os.listdir(task_dir) if t[-3:] == '.py']
    return tasks


def find_prev_base(dat) -> float:
    """Find most recent baseline weight (going back in time). This is
       to account for drift in the system. Gets the 5 most recent baseline
       measurements
    """
    store = []
    wbase = 0
    for line in reversed(dat):  # start at the end and work through the lines
        tmp = re.findall(r'Wbase:([0-9]*\.[0-9]*)_', line)
        if tmp:
            store.append(float(tmp[0]))
            if len(store) > 5:
                break

    wbase = np.mean(store)

    return wbase
