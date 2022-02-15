# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys

from pycontrol_homecage.utils import load_data_csv
from pycontrol_homecage.loc_def import all_paths
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()
this.controllers = {}
this.connected_boards = []
this.connected_access_controls = []

ROOT, task_dir, experiment_dir, setup_dir, mice_dir, data_dir, AC_logger_dir, protocol_dir = all_paths

this.paths = {'ROOT': ROOT,
              'task_dir': task_dir,
              'experiment_dir': experiment_dir,
              'setup_dir': setup_dir,
              'mice_dir': mice_dir,
              'data_dir': data_dir,
              'AC_logger_dir': AC_logger_dir,
              'protocol_dir': protocol_dir
              }
