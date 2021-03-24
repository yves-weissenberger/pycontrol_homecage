from pyControl.utility import *
import hardware_definition as hw

# States and events.
states= ['init_state',
         'select_poke',
         'poke_selected',
         'poke_release']

events = ['poke_4', 'poke_4_out',
          'poke_6', 'poke_6_out',
          'poke_5', 'poke_5_out',
          'poke_1', 'poke_1_out',
          'poke_2', 'poke_2_out',
          'poke_3', 'poke_3_out',
          'poke_9', 'poke_9_out',
          'poke_7', 'poke_7_out',
          'poke_8', 'poke_8_out',
          'rew_timer','reset_timer']
initial_state = 'init_state'

# Parameters
v.selected_poke_n = None
v.selected_poke   = None
v.prev_selected_poke_n = None
poke_dict = {1:hw.poke_1,
             2:hw.poke_2,
             3:hw.poke_3,
             4:hw.poke_4,
             5:hw.poke_5,
             6:hw.poke_6,
             7:hw.poke_7,
             8:hw.poke_8,
             9:hw.poke_9}

# Define behaviour.

def run_start():
    hw.houselight.on()
    hw.speaker.set_volume(20)

def run_end():
    hw.off()

def init_state(event):
    if event == 'entry':
        hw.poke_5.LED.on()
    elif event == 'exit':
        hw.poke_5.LED.off()
    elif event in ['poke_1', 'poke_4', 'poke_6', 'poke_9','poke_2','poke_3','poke_5','poke_7','poke_8']:
        v.prev_selected_poke_n = v.selected_poke_n
        v.selected_poke_n = int(event.split('_')[1])

        goto_state('select_poke')

def select_poke(event):
    #test1
    if event == 'entry':
        for poke in poke_dict.values():
            poke.LED.off()

        if v.selected_poke_n == v.prev_selected_poke_n:
            v.selected_poke = poke_dict[5]
        else:
            v.selected_poke = poke_dict[v.selected_poke_n]
        timed_goto_state('poke_selected', 5)

def poke_selected(event):
    if event == 'entry':
        v.selected_poke.LED.on()
    elif event == 'exit':
        v.selected_poke.LED.off()
    elif event in ['poke_1', 'poke_4', 'poke_6', 'poke_9','poke_2','poke_3','poke_7','poke_8']:
        if ((int(event.split('_')[1])==v.prev_selected_poke_n) and v.selected_poke==poke_dict[5]):
            goto_state('poke_release')
        else:
            v.prev_selected_poke_n = v.selected_poke_n
            v.selected_poke_n = int(event.split('_')[1])
            goto_state('select_poke')
    #elif event in ['poke_2','poke_3','poke_5','poke7','poke_8']:

    elif event == 'poke_5':
        if v.selected_poke_n in [1,2,3,4,6,7,8,9]:
            goto_state('poke_release')
        else:
            v.selected_poke_n = int(event.split('_')[1])
            goto_state('select_poke')

def poke_release(event):
    if event == 'entry':
        if True:#v.selected_poke_n in [1,2,3,4,6,7,8,9]:
           hw.speaker.noise()
           v.selected_poke.SOL.on()
    elif event == 'exit':
        hw.speaker.off()
        if True:#v.selected_poke_n in [1,2,3,4,6,7,8,9]:
            v.selected_poke.SOL.off()
    elif '_out' in event:
        goto_state('poke_selected')
