from pyControl.utility import *
import hardware_definition as hw
import random


states = ['handle_poke',
          'reward_consumption',
          'deliver_reward',
          'change_task',
          'ITI'
          ]

initial_state = 'handle_poke'


events = ['poke_1', 'poke_1_out',
         'poke_2', 'poke_2_out', 
         'poke_3', 'poke_3_out',
         'poke_4', 'poke_4_out',
         'poke_5', 'poke_5_out',
         'poke_6', 'poke_6_out',
         'poke_7', 'poke_7_out',
         'poke_8', 'poke_8_out',
         'poke_9', 'poke_9_out',
         'end_consumption','session_timer',
         'rew_timer',
         'light_timer',
         'poke_timer',
         'iti_timer',
         'lights_on_timer',
        ]




#list of pokes to do stuff with
hw.poke_list = [hw.poke_1,hw.poke_2,hw.poke_3,
                hw.poke_4,hw.poke_5,hw.poke_6,
                hw.poke_7,hw.poke_8,hw.poke_9]

v.state_str = [str(i) for i in range(1,10)] 
v.current_state = random.choice(range(9))
v.click_volume = 60
v.n_rewards = 0
v.light_pokes = 0
v.dark_pokes = 0
v.first_entry = True
v.rew_dur = 50
v.get_free_rew = False


v.fixed_seq = [1, 3, 6, 7, 2, 0]
v.n_till_guide = 10
v.n_till_switch = 20
v.n_rewards_at_loc = 0
v.current_state = 0
v.rewarded_poke = random.choice(v.fixed_seq)
v.rewarded_state = v.fixed_seq.index(v.rewarded_poke)
v.available_pokes = []
v.iti_dur= 3000
v.n_pokes = 0
v.lseq  = len(v.fixed_seq) - 1
v.lights_on_lag = 200
v.isActive = False
#-------------------------------------------------------------------------


def run_start(): 
    hw.speaker.set_volume(30)
    #v.rewarded_poke = 
    #print(str(v.available_transitions))
 
def run_end():
    hw.off()


def set_available_pokes():

    v.current_poke = v.fixed_seq[v.current_state]

    if v.current_state==0:
        v.available_pokes = [v.fixed_seq[1]]
    elif v.current_state==v.lseq:
        v.available_pokes = [v.fixed_seq[v.lseq-1]]
    else:
        v.available_pokes = [v.fixed_seq[v.current_state-1],v.fixed_seq[v.current_state+1]]


    if (v.n_pokes>v.n_till_guide and len(v.available_pokes)>1):
        if v.current_state>v.rewarded_state:
            v.available_pokes = [v.available_pokes[0]]

        elif v.current_state<v.rewarded_state:
            v.available_pokes = [v.available_pokes[1]]

    for pk in range(9):
        if pk in v.available_pokes:
            hw.poke_list[pk].LED.on()
        else:
            hw.poke_list[pk].LED.off()

def lights_off():

    for pk in range(9):
        hw.poke_list[pk].LED.off()


def handle_poke(event):
    """ Basically run all of the task """
    if event=='entry':
        v.isActive = False
        lights_off()
        set_timer("lights_on_timer",v.lights_on_lag*ms,output_event=True)

             
                                

    if event[-1] in v.state_str:  #check that event is an in-poke
        chosen_poke = int(event[-1]) - 1
        if v.isActive:
            if chosen_poke in v.available_pokes:
                hw.speaker.click()
                v.n_pokes += 1
                v.current_state = v.fixed_seq.index(chosen_poke)
                v.light_pokes += 1

                if chosen_poke==v.rewarded_poke:
                    goto_state('deliver_reward')
                else:
                    v.isActive = False
                    set_timer("lights_on_timer",v.lights_on_lag*ms,output_event=True)
            else:
                v.dark_pokes += 1
    if event=='rew_timer':
        hw.poke_list[v.current_state].SOL.off()

    if event=='lights_on_timer':
        lights_off()
        set_available_pokes()
        v.isActive = True


def deliver_reward(event):
    # Deliver reward to appropriate poke
    if event == 'entry':
            print('nREWS:' + str(v.n_rewards) +
                  'fracL:' + str(float(v.light_pokes)/float(v.light_pokes+1+v.dark_pokes)))
            set_timer('rew_timer', v.rew_dur*ms,output_event=True)
            hw.poke_list[v.rewarded_poke].SOL.on()
            v.n_rewards_at_loc += 1
            v.n_rewards += 1
            v.n_pokes = 0
    if event=='rew_timer':
            goto_state('ITI')
    elif event == 'exit':
            hw.poke_list[v.rewarded_poke].SOL.off()

def ITI(event):

    if event=='entry':
        lights_off()
        set_timer('iti_timer', v.iti_dur*ms,output_event=True)

        if v.n_rewards_at_loc>v.n_till_switch:
            v.rewarded_poke = random.choice(v.fixed_seq)
            v.rewarded_state = v.fixed_seq.index(v.rewarded_poke)
            v.n_rewards_at_loc = 0 
        v.current_state = random.choice([i for i in range(len(v.fixed_seq)) if i!=v.rewarded_state])
    if event=='iti_timer':
        goto_state('handle_poke')


