# from https://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
import sys

from pycontrol_homecage.utils import load_data_csv
from pycontrol_homecage.utils.loc_def import all_paths
# this is a pointer to the module object instance itself.
this = sys.modules[__name__]

# we can explicitly make assignments on it
this.task_df, this.exp_df, this.setup_df, this.mouse_df = load_data_csv()
this.controllers = {}
this.connected_boards = []
this.connected_access_controls = []
this.updated = False
this.update_table_queue = []
this.message_queue = []

# These are print consumers that ensure that things are printer to the correct place
this.print_consumers = {}

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


# This is clearly not implemented yet
# class pycontrol_homecage_database:

#     def __init__(self) -> None:
#         self.has_been_updated = True

#     def update_table_row(self, table_name: str, column_name: str, new_value: object, row_identifier: object, row_id_value: object) -> None:
#         pass

#     def add_table_row(self, table: str, row) -> None:
#         pass

#     def add_table_rows(self) -> None:
#         pass

#     def write_tables_to_file(self) -> None:
#         pass

#     def add_controller(self) -> None:
#         pass

#     def add_access_control_board(self) -> None:
#         pass

#     def add_pycontrol_board(self) -> None:
#         pass
