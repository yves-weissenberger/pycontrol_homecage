from pyControl.utility import *
import hardware_definition as hw
import random


states = ['handle_poke',
            'reward_consumption',
            'deliver_reward',
            'lights_off',
            'change_task'
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
          'lights_off_timer',
          'change_task_timer',
          'probe_timer'
         ]



v.test_variable = None

#list of pokes to do stuff with
hw.poke_list = [hw.poke_1,hw.poke_2,hw.poke_3,
                hw.poke_4,hw.poke_5,hw.poke_6,
                hw.poke_7,hw.poke_8,hw.poke_9]

v.state_str = [str(i) for i in range(1,10)] 
v.choice_poke = random.choice(range(9))
v.click_volume = 60
v.n_rewards = 0
v.light_pokes = 0
v.dark_pokes = 0
v.first_entry = True
v.rew_dur = 50
v.get_free_rew = False


v.sequences =  [[1, 2, 4, 3, 7, 5],[5, 4, 6, 8, 2, 0]]
v.graph_types = ['loop','line']
v.task_nr = 0  #which of the n-graphs are the mice currently on

v.seq_ix = 0   #which state are the mice currently in?
v.rewards_in_task = 0    #how many rewards have been received in the current task
v.direction = (random.choice(range(2))*2) - 1 #direction is +1 or -1 for going up or down
v.probe_probability = 0.0
v.task_switch_p = 0.25
v.rews_pre_task_switch = 100
v.direction_switch_p = 0.125
v.change_task_timeout = 10000
v.probe_dur = 2000
v.len_seqs = None
#-------------------------------------------------------------------------

def get_next_state():

    if withprob(v.direction_switch_p):
        if v.direction==1:
            v.direction = -1
        else:
            v.direction = 1
        isProbe = False
    else:
        isProbe = withprob(v.probe_probability)


    if v.graph_type=='loop':
        v.seq_ix = (v.seq_ix + v.direction) %(v.len_seq+1)

    if v.graph_type=='line':
        if v.seq_ix==0:  #need to consider whether in these cases u want
            v.seq_ix = 1
            v.direction = 1
        elif v.seq_ix==v.len_seq:
            v.seq_ix = v.len_seq-1
            v.direction = -1
        else:
            v.seq_ix += v.direction

    return isProbe


def run_start(): 
    hw.speaker.set_volume(60)
    if v.len_seqs is None:
         v.seq = v.sequences[v.task_nr]
         v.len_seq  = len(v.seq) - 1
    else:
        v.len_seq = v.len_seq[v.task_nr]
        v.seq = v.sequences[v.task_nr[:v.len_seq]]
   
    v.graph_type = v.graph_types[v.task_nr]
   

 
def run_end():
    hw.off()

def handle_poke(event):
    """ Basically run all of the task """

    if event=='entry':
        print('############')
        print(v.seq_ix)
        v.choice_poke = v.seq[v.seq_ix]
        isProbe = get_next_state()


        if v.get_free_rew:
            if v.first_entry:
                v.first_entry = False
                for pk_ in hw.poke_list:
                    pk_.SOL.on()
                set_timer('rew_timer', 200*ms,output_event=True)

 

        if not isProbe:
            for pk in range(9):
                if pk == v.choice_poke:
                    hw.poke_list[pk].LED.on()
                else:
                    hw.poke_list[pk].LED.off()
        else:
            for pk in range(9):
                hw.poke_list[pk].LED.off()
            print("probe_start")
            set_timer('probe_timer', v.probe_dur*ms,output_event=True)

    if event=='probe_timer':
        for pk in range(9):
            if pk == v.choice_poke:
                hw.poke_list[pk].LED.on()
            else:
                hw.poke_list[pk].LED.off()
                                
    if event=='rew_timer':
        for pk_ in hw.poke_list:
            pk_.SOL.off()

    if event[-1] in v.state_str:  #check that event is an in-poke
        chosen_poke = int(event[-1]) - 1
        if v.choice_poke==chosen_poke:
            goto_state('deliver_reward')
            v.light_pokes += 1
        else:
            v.dark_pokes += 1
    if event=='rew_timer':
            hw.poke_list[v.choice_poke].SOL.off()


def deliver_reward(event):
    # Deliver reward to appropriate poke
    if event == 'entry':
            print('nREWS:' + str(v.n_rewards) +
                        'fracL:' + str(float(v.light_pokes)/float(v.light_pokes+1+v.dark_pokes)))
            set_timer('rew_timer', v.rew_dur*ms,output_event=True)
            hw.poke_list[v.choice_poke].SOL.on()
            v.n_rewards += 1
            v.rewards_in_task += 1
    if event=='rew_timer':
        if (v.rewards_in_task>v.rews_pre_task_switch and withprob(v.task_switch_p)):
            goto_state('change_task')
        else:
            goto_state('handle_poke')
    elif event == 'exit':
            hw.poke_list[v.choice_poke].SOL.off()

def change_task(event):

    if event== 'entry':
        print("change_task_start")
        set_timer('change_task_timer', v.change_task_timeout*ms,output_event=True)
        if v.task_nr==0: 
            v.task_nr=1
        else:
            v.task_nr=0

        for pk in range(9):
            if pk == v.choice_poke:
                hw.poke_list[pk].LED.on()
            else:
                hw.poke_list[pk].LED.off()

        if v.len_seqs is None:
            v.seq = v.sequences[v.task_nr]
            v.len_seq  = len(v.seq) - 1
        else:
            v.len_seq = v.len_seq[v.task_nr]
            v.seq = v.sequences[v.task_nr[:v.len_seq]]
        v.graph_type = v.graph_types[v.task_nr]
        
    if event=='change_task_timer':
        v.rewards_in_task = 0
        goto_state('handle_poke')
