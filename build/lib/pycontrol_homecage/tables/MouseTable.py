from functools import partial

from pyqtgraph import Qt
from pyqtgraph.Qt import QtCore, QtGui

from pycontrol_homecage.utils import get_tasks
import pycontrol_homecage.db as database


class MouseTable(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, GUI, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,15, parent=parent)
        self.header_names = ['','Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 'Task','Protocol', 'User', 
                            'Start_date', 'Current_weight', 'Start_weight', 'is_training',
                            'is_assigned', 'training_log', 'Setup_ID']

        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.loaded = False

        self.fill_table()
        self.loaded = True

    def fill_table(self):
        #print(database.mouse_df)
        #self.setRowCount(0)
        self.setRowCount(len(database.mouse_df))
        df_cols = database.mouse_df.columns

        #print(df_cols)
        for row_index, row in database.mouse_df.iterrows():    

            for col_index in range(self.columnCount()-1):  
                col_name = df_cols[col_index]
                if col_name in self.header_names:
                    table_col_ix = self.header_names.index(df_cols[col_index])
                    if col_name=='Task':
                        task_combo = QtGui.QComboBox()
                        task_combo.activated.connect(partial(self.update_task_combo,task_combo))
                        task_combo.installEventFilter(self)
                        task_combo.RFID = row['RFID']
                        cTask = database.mouse_df.loc[database.mouse_df['RFID']==row['RFID'],'Task'].values[0]
                        task_combo.addItems([cTask] + get_tasks(database.paths['task_dir']))

                        self.setCellWidget(row_index,table_col_ix,task_combo)

                        task_combo.currentTextChanged.connect(partial(self.change_mouse_task,task_combo))


                    else:
                        self.setItem(row_index,table_col_ix,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))
            #items = [QtGui.QStandardItem(field)for field in row]
            #print(items)
            #self.model.appendRow(items)
            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,0,chkBoxItem)



    def update_task_combo(self, combo: QtGui.QComboBox) -> None:
        cTask = combo.currentText()
        combo.clear()
        combo.addItems([cTask] + get_tasks(database.paths['task_dir']))


    def change_mouse_task(self, combo: QtGui.QComboBox) -> None:
        """ Change task mouse is doing """
        rfid = combo.RFID

        #if self.loaded:  #workaround (sorry)

        #print('UPDATED TASK VIA TABLE')
        database.mouse_df.loc[database.mouse_df['RFID']==rfid,'Task'] = combo.currentText()  #need to update the table of the individual mouses training record as well??
        database.mouse_df.to_csv(database.mouse_df.file_location)



