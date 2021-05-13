import pyb
from hx711_gpio import HX711
from uRFID import uRFID

# RFID and loadcell 

loadcell = HX711(data_pin='X7',clock_pin='X8', gain=128)
rfid = uRFID(bus=6)

# Instantiate pins used for doors.

class signal_pin:
    """ Pseudo-subclass of pin that replicates its method but within the context of the
        surrounding hardware used for door sensing.
    """
    def __init__(self,sense_pin,enable_pin_1,enable_pin_2,sense_delay=3000,threshold=2000,check_every=100):
        self.pin = sense_pin
        self.enable_pin_1 = enable_pin_1
        self.enable_pin_2 = enable_pin_2
        self.sense_delay = sense_delay
        self.threshold = threshold
        self._last_pin_check = pyb.millis()
        self.state = 0
        self.check_every = check_every
    
    def value(self):
        """ Returns true if the door is open. This convention is used for consistency with
            the previous access control code
        """
        if pyb.elapsed_millis(self._last_pin_check)>self.check_every:
            self.enable_pin_1.value(0)
            self.enable_pin_2.value(0)
            pyb.udelay(self.sense_delay)
            value = self.pin.read()
            self.enable_pin_1.value(1)
            self.enable_pin_2.value(1)
            self.state = (value > self.threshold)
            self._last_pin_check = pyb.millis()

        return self.state



class magnet_pin:

    def __init__(self,highside,lowside,demag_delay=10):
        self.highside = highside
        self.lowside=lowside
        self.demag_delay = demag_delay

    def value(self,set_value):
        
        if set_value==1:
            self.highside.value(1)
            self.lowside.value(0)
        elif set_value==0:
            self.highside.value(0)
            self.lowside.value(1)
            pyb.delay(self.demag_delay)
            self.lowside.value(0)
        

    

enable_pin_1 = pyb.Pin('X11', pyb.Pin.OUT) # Enables/disables the drivers on the + side of doors 1 & 2.
enable_pin_2 = pyb.Pin('X12', pyb.Pin.OUT) # Enables/disables the drivers on the + side of doors 3 & 4.
enable_pin_1.value(1) # Enable drivers.
enable_pin_2.value(1)




highside_pins = [pyb.Pin(p, pyb.Pin.OUT) for p in ('Y3','Y5','Y12','X6')] # Controls whether + side of door is driven to 12V or 0V. 
lowside_pins  = [pyb.Pin(p, pyb.Pin.OUT) for p in ('Y4','Y6','Y11','X5')] # Controls whether - side of door is driven to 12V or 0V.
signal_pins   = [pyb.ADC(p) for p in ('X1','X2','X3','X4')] # Pins used to sense voltage on + side of doors.

# Initial configuration.


for i in range(4): # Drive both sides of all doors to 0V.
    highside_pins[i].value(0)
    lowside_pins[i].value(0)

# Door control functions.

def magnet_on(door):
    '''Turn on magnet for specified door.'''
    highside_pins[door].value(1) # Drive + side of door to 12V.
    lowside_pins[door].value(0)  # Drive - side of door to 0V.

def magnet_off(door, demag_delay=10):
    '''Turn off magnet for specified door. Voltage is reversed
    for demag_delay milliseconds to remove residual magnetism'''
    highside_pins[door].value(0) # Drive + side of door to 0V.
    lowside_pins[door].value(1)  # Drive - side of door to 12V.
    pyb.delay(demag_delay)
    lowside_pins[door].value(0)  # Drive - side of door to 0V.

def check_closed(door, sense_delay=3000, threshold=2000, print_value=False):
    '''Check whether specified door is closed.  The + side driver is 
    disabled allowing the voltage on the + side to float.  The voltage
    is then read after the specified delay (us) and compared to the 
    specified threshold to determine if the door is open or closed.'''
    enable_pin_1.value(0)
    enable_pin_2.value(0)
    pyb.udelay(sense_delay)
    value = signal_pins[door].read()
    enable_pin_1.value(1)
    enable_pin_2.value(1)
    if print_value:
        print('Sense value: {}'.format(value))
    if value < threshold:
       return True
    else:
        return False

# Test function.

def run_test(door):
    '''Turn on magnet for specified door. Check door state every 100ms,
    print sensor value and turn on blue LED whenever door is closed.'''
    try:
        blue_LED = pyb.Pin('B4')
        magnet_on(door)
        while True:
            pyb.delay(100)
            if check_closed(door, print_value=True):
               blue_LED.value(1)
            else:
                blue_LED.value(0)
    except KeyboardInterrupt:
        magnet_off(door)
