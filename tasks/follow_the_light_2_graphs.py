from pyControl.utility import *
import hardware_definition as hw
import random


states = ['handle_poke',
            'reward_consumption',
            'deliver_reward',
            'lights_off',
            'change_task',
            'timeout',
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
          'probe_timer',
          'timeout_timer',
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


v.sequences =  [[8,1,6,3,4,0,7,2,5], [7,5,2,3,6,8,1,0,4]]
v.graph_types = ['loop','line']
v.task_nr = 0  #which of the n-graphs are the mice currently on

v.seq_ix = 0   #which state are the mice currently in?
v.rewards_in_task = 0    #how many rewards have been received in the current task
v.direction = (random.choice(range(2))*2) - 1 #direction is +1 or -1 for going up or down
v.probe_probability = 0.1
v.task_switch_p = 0.25
v.rews_pre_task_switch = 300
v.direction_switch_p = 0.1
v.change_task_timeout = 10000
v.probe_dur = 2000
v.timeout_dur = 1000
v.len_seqs = [3,3]
v.isProbe = False
v.max_seq_timeout = 3  #max number of sequential timeouts
v.seq_timeout = 0     #current number of sequential timeouts
v.from_timeout = 10
v.since_timeout = 0
v.rew_prob = 1.
v.poke_history = []
#-------------------------------------------------------------------------

def run_start(): 
    print('task_number{}'.format(v.task_nr))
    hw.speaker.set_volume(60)
    if v.len_seqs is None:
         v.seq = v.sequences[v.task_nr]

         v.len_seq  = len(v.seq) - 1
    else:

        v.len_seq = v.len_seqs[v.task_nr]
        v.seq = v.sequences[v.task_nr][:v.len_seq]
    
    print('seq:{}'.format(v.seq))
    v.graph_type = v.graph_types[v.task_nr]
    print('graph_type:{}'.format(v.graph_type))

def set_light():
    for pk in range(9):
        if pk == v.choice_poke:
            hw.poke_list[pk].LED.on()
        else:
            hw.poke_list[pk].LED.off()

def get_next_state():
    v.seq_timeout = 0
    isProbe = False
    changed_direction = False
    if withprob(v.direction_switch_p):
        changed_direction = True
        if v.direction==1:
            v.direction = -1
        else:
            v.direction = 1
    else:
        if len(v.poke_history)>2:
            #if v.poke_history[-2][1]==v.direction:
            #    isProbe = withprob(v.probe_probability)

            #if there has not been an unforced direction change in the last
            #3 transitions
            if not any([i[-1] for i in v.poke_history[-3:]]) and (not changed_direction): 
                isProbe = withprob(v.probe_probability)


    if v.graph_type=='loop':
        v.seq_ix = (v.seq_ix + v.direction) %(v.len_seq)

    if v.graph_type=='line':
        if v.seq_ix==0:  #need to consider whether in these cases u want
            v.seq_ix = 1
            v.direction = 1
        elif v.seq_ix==(v.len_seq-1):
            v.seq_ix = v.len_seq-2
            v.direction = -1
        else:
            v.seq_ix += v.direction

    v.choice_poke = v.seq[v.seq_ix]
    if not isProbe:
        set_light()
    else:
        for pk in range(9):
            hw.poke_list[pk].LED.off()
        print("probe_start")
        set_timer('probe_timer', v.probe_dur*ms,output_event=True)

    v.poke_history.append([v.choice_poke,v.direction,v.seq_ix,changed_direction])
    v.poke_history = v.poke_history[-10:]
    return isProbe



   
 
def run_end():
    hw.off()

def handle_poke(event):
    """ Basically run all of the task """

    if event=='entry':
        print(v.seq_ix)
        print(v.from_timeout)
        if v.from_timeout>1: 
            v.isProbe = get_next_state()
        else:
            v.choice_poke, v.direction, v.seq_ix,_ = v.poke_history[-2+v.from_timeout]
            set_light()



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
        print('REWS:{}, REW_IN_SEQ:{}, POKED: {}, PROBE: {} , TARGET: {},SEQ_IX: {}, DIR: {}'.format(v.n_rewards,v.rewards_in_task,chosen_poke,v.isProbe,v.choice_poke,v.seq_ix,v.direction))
        if v.choice_poke==chosen_poke:
            v.light_pokes += 1

            v.from_timeout += 1
            
            if v.from_timeout>1:
                #v.poke_history.append([chosen_poke,v.direction,v.seq_ix])
                #v.poke_history = v.poke_history[-10:]
                if withprob(v.rew_prob):
                    goto_state('deliver_reward')
                else:
                    v.isProbe = get_next_state()
            else:
                print("HHI")
                #print(-2+v.from_timeout)
                v.choice_poke, v.direction, v.seq_ix,_ = v.poke_history[-2+v.from_timeout]
                set_light()
        else:
            if v.timeout_dur:
                v.dark_pokes += 1
                if ((len(v.poke_history)>2) 
                    and (not v.isProbe) 
                    and (v.seq_timeout<v.max_seq_timeout)
                    and (v.from_timeout>0)
                    and (not chosen_poke==v.poke_history[-2][0])):

                    goto_state('timeout')
                


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


def timeout(event):
    if event=='entry':
        for pk in range(9):
            hw.poke_list[pk].LED.off()
        set_timer('timeout_timer',v.timeout_dur*ms,output_event=True)
        hw.speaker.noise()
        v.from_timeout = 0
        v.seq_timeout += 1
        v.isProbe = False

    if event=='timeout_timer':
        hw.speaker.off()
        goto_state('handle_poke')

    
def change_task(event):

    if event== 'entry':
        
        set_timer('change_task_timer', v.change_task_timeout*ms,output_event=True)
        if v.task_nr==0: 
            v.task_nr=1
        else:
            v.task_nr=0

        for pk in range(9):
            hw.poke_list[pk].LED.off()

        if v.len_seqs is None:
            v.seq = v.sequences[v.task_nr]
            v.len_seq  = len(v.seq) - 1
        else:
            v.len_seq = v.len_seqs[v.task_nr]
            v.seq = v.sequences[v.task_nr][:v.len_seq]
            v.graph_type = v.graph_types[v.task_nr]
            print("change_task_start")
            print('task_number{}'.format(v.task_nr))
            print('seq:{}'.format(v.seq))
            print('graph_type:{}'.format(v.graph_type))


    if event=='change_task_timer':
        v.rewards_in_task = 0
        v.poke_history = []
        goto_state('handle_poke')
