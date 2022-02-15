import sys
import pytestqt


from pycontrol_homecage.GUI import Visualizator

def test(qtbot):
    window = Visualizator()
    qtbot.addWidget(window)