import pyb




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
        

    
