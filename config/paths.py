import os

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Top level pyControl folder.

config_dir      = os.path.join(top_dir, 'config')
framework_dir   = os.path.join(top_dir, 'pyControl')

accCtrl_dir     = os.path.join(top_dir, 'access_control_upy')
devices_dir     = os.path.join(top_dir, 'devices')
tasks_dir       = os.path.join(top_dir, 'tasks')
experiments_dir = os.path.join(top_dir, 'experiments')
data_dir        = os.path.join(top_dir, 'data')
transfer_dir    = None # Folder to copy data to at end of run experiment.

