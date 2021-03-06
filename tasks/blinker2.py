# A simple state machine which flashes the blue LED on the pyboard on and off.
# Does not require any hardware except micropython board.

from pyControl.utility import *
#import hardware_definition as hw
# States and events.

states = ['LED_on',
          'LED_off']

events = []

initial_state = 'LED_off'

# Variables.

v.LED_n  = 1 # Number of LED to use.
v.nBlinks = 0
        
# Define behaviour. 

def LED_on(event):
    if event == 'entry':
        timed_goto_state('LED_off', 0.5 * second)
        pyb.LED(v.LED_n).on()
        v.nBlinks += 1
    elif event == 'exit':
        pyb.LED(v.LED_n).off()

def LED_off(event):
    if event == 'entry':
        timed_goto_state('LED_on', 0.5 * second)

def run_end():  # Turn off hardware at end of run.
    pyb.LED(v.LED_n).off()



