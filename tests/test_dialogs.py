import time

import pytestqt

from pycontrol_homecage.dialogs import calibrate_dialog, box_conn_dialog
from pycontrol_homecage.com.access_control import Access_control

def test_calibrate_dialog(qtbot):
    ac = Access_control(serial_port=None)
    dialog = calibrate_dialog(ac=None)
    qtbot.addWidget(dialog)



def test_box_conn_dialog(qtbot):

    dialog = box_conn_dialog()
    qtbot.addWidget(dialog)
    target = "You must be connected to the setup to update it"
    assert dialog.textbox.text() == target

def test_one():
    assert 1==1
# if __name__ == "__main__":
#     test_calibrate_dialog()]
