#from .hx711_spi import HX711
from .hx711_gpio import HX711
from .uRFID import uRFID
import time

class Access_control_upy():
    # Class instantiated on the pyboard mounted on the Access Control 1.1 PCB.

    def __init__(self):
        #self.loadcell = HX711(data_pin='Y7',clock_pin='Y8', SPI_clk_pin='Y6')
        #self.rfid = uRFID(bus=4)
        self.loadcell = HX711(data_pin='X7',clock_pin='X8', gain=128)
        self.rfid = uRFID(bus=6)