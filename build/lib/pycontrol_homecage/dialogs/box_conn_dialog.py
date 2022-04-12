from pyqtgraph.Qt import QtGui


class box_conn_dialog(QtGui.QDialog):

    def __init__(self, parent=None):
        super(box_conn_dialog, self).__init__(parent)
        self.textbox = QtGui.QLineEdit(self)
        self.textbox.setText("You must be connected to the setup to update it")
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textbox)
