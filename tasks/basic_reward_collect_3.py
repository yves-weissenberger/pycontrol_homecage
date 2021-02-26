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
          'wrong_timer',
          'repeat_timer',
          'change_task_timer',
          'noise_timer',
          'timeout_timer'
          ]




#list of pokes to do stuff with
hw.poke_list = [hw.poke_1,hw.poke_2,hw.poke_3,
                hw.poke_4,hw.poke_5,hw.poke_6,
                hw.poke_7,hw.poke_8,hw.poke_9]

v.state_str = [str(i) for i in range(1,10)] 
v.choice_poke = random.choice(range(9))
v.click_volume = 20
v.n_rewards = 0
v.light_pokes = 0
v.dark_pokes = 0
v.first_entry = True
v.rew_dur = 20
v.noise_dur = 100
v.timeout_dur = 2000
v.get_free_rew = False
v.prev_rew = None
v.inactive = False
v.has_been_wrong = False
v.n_timeouts = 0
v.max_timeout = 5
#-------------------------------------------------------------------------


def run_start(): 
 
    hw.speaker.set_volume(v.click_volume)
    #print(str(v.available_transitions))
   


def run_end():
    hw.off()


def handle_poke(event):
    """ Basically run all of the task """

    if event=='entry':

        v.choice_poke = random.choice(range(9))

        if v.get_free_rew:
          if v.first_entry:
            v.first_entry = False
            for pk_ in hw.poke_list:
              pk_.SOL.on()
            set_timer('rew_timer', 200*ms,output_event=True)

        print(v.choice_poke)
        for pk in range(9):
            if pk == v.choice_poke:
                hw.poke_list[pk].LED.on()
            else:
                hw.poke_list[pk].LED.off()

    if event=='rew_timer':
      for pk_ in hw.poke_list:
        pk_.SOL.off()
 
    if event[-1] in v.state_str:  #check that event is an in-poke
        print("POKE:" + str(int(event[-1]) - 1))
        if not v.inactive:
          chosen_poke = int(event[-1]) - 1

          if v.choice_poke==chosen_poke:
              v.light_pokes += 1
              v.prev_rew = v.choice_poke
              goto_state('deliver_reward')
          else:
              if (chosen_poke==v.prev_rew):
                pass
              else:
                v.dark_pokes += 1
                if (v.n_timeouts<v.max_timeout):#not v.has_been_wrong:
                  v.has_been_wrong = True
                  v.inactive = True

                  hw.speaker.noise()
                  set_timer('noise_timer', v.noise_dur*ms,output_event=True)
                  set_timer('timeout_timer', v.timeout_dur*ms,output_event=True)
                  v.n_timeouts += 1
                  for pk in range(9):
                    hw.poke_list[pk].LED.off()

                

    if event=='noise_timer':
      hw.speaker.off()

    if event=='timeout_timer':
      v.inactive = False

      for pk in range(9):
          if pk == v.choice_poke:
              hw.poke_list[pk].LED.on()
          else:
              hw.poke_list[pk].LED.off()


    if event=='rew_timer':
        hw.poke_list[v.choice_poke].SOL.off()


def deliver_reward(event):
    # Deliver reward to appropriate poke
    if event == 'entry':
        v.has_been_wrong = False
        print('nREWS:' + str(v.n_rewards) +
              'fracL:' + str(float(v.light_pokes)/float(v.light_pokes+1+v.dark_pokes)))
        set_timer('rew_timer', v.rew_dur*ms,output_event=True)
        hw.poke_list[v.choice_poke].SOL.on()
        v.n_rewards += 1
        v.n_timeouts = 0
    if event=='rew_timer':
        goto_state('handle_poke')
    elif event == 'exit':
        hw.poke_list[v.choice_poke].SOL.off()