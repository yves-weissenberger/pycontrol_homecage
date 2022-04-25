import sys
import pytestqt


from pycontrol_homecage.GUI import Visualizator

def test_basic_start(qtbot):
    window = Visualizator()
    qtbot.addWidget(window)

#def test_