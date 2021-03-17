# This hardware definition specifies that 3 pokes are plugged into ports 1-3 and a speaker into
# port 4 of breakout board version 1.2.  The houselight is plugged into the center pokes solenoid socket.

from devices import *
from pyControl.hardware import Digital_output

board = Breakout_1_2()

nine_poke = Nine_poke(board.port_3)

speaker = Audio_board(board.port_4)

# Aliases
poke_1 = nine_poke.poke_1
poke_2 = nine_poke.poke_2
poke_3 = nine_poke.poke_3
poke_4 = nine_poke.poke_4
poke_5 = nine_poke.poke_5
poke_6 = nine_poke.poke_6
poke_7 = nine_poke.poke_7
poke_8 = nine_poke.poke_8
poke_9 = nine_poke.poke_9

poke_1.SOL = nine_poke.SOL_5
poke_2.SOL = nine_poke.SOL_3
poke_3.SOL = nine_poke.SOL_7
poke_4.SOL = nine_poke.SOL_1
poke_5.SOL =  Digital_output(board.port_6.POW_B)
poke_6.SOL = nine_poke.SOL_8
poke_7.SOL = nine_poke.SOL_2
poke_8.SOL = nine_poke.SOL_6
poke_9.SOL = nine_poke.SOL_4

houselight = Digital_output(board.port_6.POW_A)
rsync = Rsync(board.port_6.DIO_B,mean_IPI=5000,pulse_dur=50)
#rsync = Rsync(board.port_6.DIO_B,mean_IPI=5000,pulse_dur=400)