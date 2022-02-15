# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys

from pycontrol_homecage.utils import load_data_csv
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()
