from pyqtgraph.Qt import QtGui



##### YW code imports
from pycontrol_homecage.dialogs import are_you_sure_dialog, cage_summary_dialog, configure_box_dialog, box_conn_dialog, direct_pyboard_dialog
from pycontrol_homecage.tables import cageTable
from pycontrol_homecage.utils import find_setups



class setups_tab(QtGui.QWidget):

    def __init__(self, parent=None):

        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.board = None
        self.callibrate_dialog = None
        self.configure_box_dialog = None

        ### Add cages cages
        self.add_cage_button = QtGui.QPushButton('Add setup')
        self.add_cage_button.clicked.connect(self.add_cage)


        self.CAT = QtGui.QGroupBox("Add Setup")

        self.cat_layout = QtGui.QHBoxLayout()  #for behavioral setup

        self.cat_combo_box = QtGui.QComboBox()

        self.setup_name_label = QtGui.QLabel('Setup Name:')
        self.setup_name = QtGui.QLineEdit()

        self.cact_combo_box = QtGui.QComboBox()

        self.cat_layout.addWidget(self.setup_name_label)
        self.cat_layout.addWidget(self.setup_name)
        self.cat_layout.addWidget(self.cat_combo_box)
        self.cat_layout.addWidget(self.cact_combo_box)
        self.cat_layout.addWidget(self.add_cage_button)



        self.CAT.setLayout(self.cat_layout)
        #self.add_cage_layout.addWidget(self.add_cage_table)
        #self.add_cage_layout.addWidget(self.add_cage_button)

        ##############################################################
        ###############     Remove and update cages    ###############
        ##############################################################



        self.remove_cage_button = QtGui.QPushButton('Remove setup')
        self.remove_cage_button.clicked.connect(self.remove_cage)
        self.update_cage_button = QtGui.QPushButton('Update Connected setup')
        self.update_cage_button.clicked.connect(self.update_setup)

        self.check_beh_hardware_button = QtGui.QPushButton('Access task pyboard')
        self.check_beh_hardware_button.clicked.connect(self.cbh)

        self.cage_summary_button = QtGui.QPushButton('Get setup Summary')
        self.cage_summary_button.clicked.connect(self.get_summary)


        self.cage_manager_layout = QtGui.QHBoxLayout()
        self.cage_manager_layout.addWidget(self.remove_cage_button)
        self.cage_manager_layout.addWidget(self.update_cage_button)
        self.cage_manager_layout.addWidget(self.check_beh_hardware_button)
        self.cage_manager_layout.addWidget(self.cage_summary_button)

        ##############################################################
        ###############   ---   Setup Tables   ----    ###############
        ##############################################################

        #Setups table
        self.cage_table_label = QtGui.QLabel()
        self.cage_table_label.setText("List of setups")

        self.scrollable_cage =  QtGui.QScrollArea()
        self.scrollable_cage.setWidgetResizable(True)
        self.scrollable_cage.horizontalScrollBar().setEnabled(False)




        self.list_of_setups = cageTable(self.GUI,self)
        self.scrollable_cage.setWidget(self.list_of_setups)

        ##############################################################
        ###############   ---   Setup Layout   ----    ###############
        ##############################################################
        self.Vlayout = QtGui.QVBoxLayout(self)
        #self.Vlayout.addWidget(self.add_cage_button)
        #self.Vlayout.addWidget(self.add_cage_table)
        self.Vlayout.addWidget(self.CAT,1)

        self.Vlayout.addWidget(self.cage_table_label,1)
        self.Vlayout.addLayout(self.cage_manager_layout,1)

        self.Vlayout.addWidget(self.scrollable_cage,15)



    def cbh(self):
        """ This is used to access the pyboard running the task directly
            which can be used to test a task and e.g. flush out the 
            system
        """
        isChecked = []
        for row in range(self.list_of_setups.rowCount()):
            isChecked.append(self.list_of_setups.item(row,self.list_of_setups.select_nr).checkState()==2)
        if len(self.GUI.controllers)==0:
            boxM = QtGui.QMessageBox()
            boxM.setIcon(QtGui.QMessageBox.Information)
            boxM.setText("You must be connected to a setup to update it")
            boxM.exec()

        if sum(isChecked)==1:
            checked_row = isChecked.index(1)
            setup_col = self.list_of_setups.header_names.index("Setup_ID")
            checked_setup_id = self.list_of_setups.item(checked_row,setup_col).text()
            for k,G in self.GUI.controllers.items():
                if k==checked_setup_id:
                    #print("YA")
                    self.configure_box_dialog = direct_pyboard_dialog(k,self.GUI)
                    self.configure_box_dialog.exec_()


            #self.GUI.controllers.append(SC)
        else:
            pass
            print('You must edit one setup at a time')
    def update_setup(self):

        isChecked = []


        for row in range(self.list_of_setups.rowCount()):
            isChecked.append(self.list_of_setups.item(row,self.list_of_setups.select_nr).checkState()==2)
        if len(self.GUI.controllers)==0:
            #box_conn_dialog().exec_()
            boxM = QtGui.QMessageBox()
            boxM.setIcon(QtGui.QMessageBox.Information)
            boxM.setText("You must be connected to a setup to update it")
            boxM.exec()
        if sum(isChecked)==1:
            checked_row = isChecked.index(1)
            setup_col = self.list_of_setups.header_names.index("Setup_ID")
            checked_setup_id = self.list_of_setups.item(checked_row,setup_col).text()
            for k,G in self.GUI.controllers.items():
                if k==checked_setup_id:
                    #print("YA")
                    self.configure_box_dialog = configure_box_dialog(k,self.GUI)
                    self.configure_box_dialog.exec_()


            #self.GUI.controllers.append(SC)
        else:
            pass
            print('You must edit one setup at a time')


    def add_cage(self):
        #print(self.GUI.setup_df)

        entry_nr = len(self.GUI.setup_df)

        #add a check to see that something about the cage has been filled in
        if not (self.cat_combo_box.currentIndex()==0 or self.setup_name.text() is None):

            #first fill row with NA
            self.GUI.setup_df.loc[entry_nr] = ['none']*len(self.GUI.setup_df.columns)

            #get and set the USB port key
            COM = self.cat_combo_box.itemText(self.cat_combo_box.currentIndex())
            self.GUI.setup_df.loc[entry_nr,'COM'] = COM

            COM_AC = self.cact_combo_box.itemText(self.cact_combo_box.currentIndex())
            self.GUI.setup_df.loc[entry_nr,'COM_AC'] = COM_AC


            #get the name of the setup
            self.GUI.setup_df.loc[entry_nr,'Setup_ID'] = self.setup_name.text()


        self.list_of_setups.fill_table()
        self.GUI.system_tab.list_of_setups.fill_table()

        self.GUI.setup_df.to_csv(self.GUI.setup_df.file_location)
        #print(self.GUI.setup_df)



    def _refresh(self):
        """ find which training seutps are available """
        ports = find_setups(self.GUI)
        ports = [i for i in ports if i not in (self.GUI.setup_df['COM'].tolist() + self.GUI.setup_df['COM_AC'].tolist())]   

        prev = ['Select Training Setup'] + list(ports)

        new_prop_cat = [self.cat_combo_box.itemText(i) for i in range(self.cat_combo_box.count())]
        #print(new_prop_cat)
        if new_prop_cat!=prev:
            print(new_prop_cat,prev)
            self.cat_combo_box.clear()
            self.cact_combo_box.clear()
            tmp = [i for i in ports if i not in (self.GUI.setup_df['COM'].tolist() + self.GUI.setup_df['COM_AC'].tolist())]   
            self.cat_combo_box.addItems(['Select Training Setup'] + list(tmp))
            self.cact_combo_box.addItems(['Select Access Control'] + list(tmp))



        self.list_of_setups._refresh()


    def remove_cage(self):
        """ Remove cage from df and CSV file """
        isChecked = []
        for row in range(self.list_of_setups.rowCount()):
            isChecked.append(self.list_of_setups.item(row,self.list_of_setups.select_nr).checkState()==2)

        if any(isChecked):
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                fl = self.GUI.setup_df.file_location

                self.GUI.setup_df = self.GUI.setup_df.drop(self.GUI.setup_df.index[isChecked])
                self.GUI.setup_df.file_location = fl

                self.list_of_setups.fill_table()
                self.GUI.system_tab.list_of_setups.fill_table()
        else:
            pass




    def get_summary(self):
        """ Get summary information for the set of selected mice """


        isChecked = []
        for row in range(self.list_of_setups.rowCount()):
            checked = self.list_of_setups.item(row,0).checkState()==2
            isChecked.append(checked)

        if any(isChecked):
            sd = cage_summary_dialog()
            sd.show()
            sd.exec_()



