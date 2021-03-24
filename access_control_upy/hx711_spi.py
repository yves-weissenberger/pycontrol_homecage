from machine import Pin, SPI, idle

class HX711:
    # Class for controlling HX711 loadcell amplifier from Micropython pyboard.
    # Adapted from https://github.com/robert-hh/hx711-lopy

    def __init__(self, data_pin, clock_pin, SPI_clk_pin, gain=128):
        # data_pin  must be SPI MISO
        # clock pin must be SPI MOSI
        # SPI_clk_pin is not connected but must be SPI CLK.


        self.pSCK = Pin(clock_pin, mode=Pin.OUT)
        self.pOUT = Pin(data_pin, mode=Pin.IN, pull=Pin.PULL_DOWN)
        self.spi = SPI(baudrate=1000000, polarity=0,
                       phase=0, sck=SPI_clk_pin, mosi=clock_pin, miso=data_pin)
        self.pSCK(0)

        self.clock_25 = b'\xaa\xaa\xaa\xaa\xaa\xaa\x80'
        self.clock_26 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa0'
        self.clock_27 = b'\xaa\xaa\xaa\xaa\xaa\xaa\xa8'
        self.clock = self.clock_25
        self.lookup = (b'\x00\x01\x00\x00\x02\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x04\x05\x00\x00\x06\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x08\x09\x00\x00\x0a\x0b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x0c\x0d\x00\x00\x0e\x0f')
        self.in_data = bytearray(7)

        self.OFFSET = 0
        self.SCALE = 3500

        self.time_constant = 0.1
        self.filtered = 0

        self.set_gain(gain)

    def set_gain(self, gain):
        if gain == 128:
            self.clock = self.clock_25
        elif gain == 64:
            self.clock = self.clock_27
        elif gain == 32:
            self.clock = self.clock_26

        self.read()
        self.filtered = self.read()

    def read(self):
        # wait for the device to get ready
        while self.pOUT() != 0:
            idle()

        # get the data and set channel and gain
        self.spi.write_readinto(self.clock, self.in_data)

        # pack the data into a single value
        result = 0
        for _ in range(6):
            result = (result << 4) + self.lookup[self.in_data[_] & 0x55]

        # return sign corrected result
        return result - ((result & 0x800000) << 1)

    def read_average(self, times=3):
        sum = 0
        for i in range(times):
            sum += self.read()
        return sum / times

    def weigh(self, times=3):
        return (self.read_average(times) - self.OFFSET) / self.SCALE 

    def tare(self, times=15):
        # Set the 0 value.
        self.OFFSET = self.read_average(times)

    def calibrate(self, weight=1, times=15):
        # Calibrate the scale using a known weight, must be done after scale has beenn tared.
        self.SCALE = (self.read_average(times) - self.OFFSET) / weight

    def power_down(self):
        self.pSCK.value(False)
        self.pSCK.value(True)

    def power_up(self):
        self.pSCK.value(False)
