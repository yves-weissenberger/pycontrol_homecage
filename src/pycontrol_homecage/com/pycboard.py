import os

from serial import SerialException
from array import array
from .pyboard import Pyboard, PyboardError
import pycontrol_homecage.db as database

# ----------------------------------------------------------------------------------------
#  Pycboard class.
# ----------------------------------------------------------------------------------------

class Pycboard(Pyboard):
    '''Pycontrol board inherits from Pyboard and adds functionality for file transfer
    and pyControl operations.
    '''

    def __init__(self, serial_port,  baudrate=115200, verbose=True, print_func=print, data_logger=None):
        
        self.serial_port = serial_port
        self.print = print_func        # Function used for print statements.
        self.data_logger = data_logger # Instance of Data_logger class for saving and printing data.
        self.status = {'serial': None, 'framework':None, 'usb_mode':None}
        try:    
            super().__init__(self.serial_port, baudrate=115200)
            self.status['serial'] = True
            self.reset() 
            self.unique_ID = eval(self.eval('pyb.unique_id()').decode())
            v_tuple = eval(self.eval(
            "sys.implementation.version if hasattr(sys, 'implementation') else (0,0,0)").decode())
            self.micropython_version = float('{}.{}{}'.format(*v_tuple))
        except SerialException as e:
            raise(e)
            self.status['serial'] = False
        if verbose: # Print status.
            if self.status['serial']:
                self.print('\nMicropython version: {}'.format(self.micropython_version))
            else:
                self.print('Error: Unable to open serial connection.')
                return
            if self.status['framework']:
                self.print('pyControl Framework: OK')
            else:
                if self.status['framework'] is None:
                    self.print('pyControl Framework: Not loaded')
                else:
                    self.print('pyControl Framework: Import error')
                return


        
    # ------------------------------------------------------------------------------------
    # pyControl operations.
    # ------------------------------------------------------------------------------------

    def load_framework(self):
        '''Copy the pyControl framework folder to the board.'''
        self.print('\nTransfering pyControl framework to pyboard.', end='')
        self.transfer_folder(database.paths["framework_dir"], file_type='py', show_progress=True)
        self.transfer_folder(database.paths["devices_dir"], file_type='py', show_progress=True)
        error_message = self.reset()
        if not self.status['framework']:
            self.print('\nError importing framework:')
            self.print(error_message)
        else:
            self.print(' OK')
        return 

    def load_hardware_definition(self, hwd_path=os.path.join(database.paths["config_dir"], 'hardware_definition.py')):
        '''Transfer a hardware definition file to pyboard.  Defaults to transfering 
        file hardware_definition.py from config folder.'''
        if os.path.exists(hwd_path):
            self.print('\nTransfering hardware definition to pyboard.', end='')
            self.transfer_file(hwd_path, target_path = 'hardware_definition.py')
            self.reset()
            try:
                self.exec('import hardware_definition')
                self.print(' OK')
            except PyboardError as e:
                error_message = e.args[2].decode()
                self.print('\n\nError importing hardware definition:\n')
                self.print(error_message)
        else:
            self.print('Hardware definition file not found.') 

    def setup_state_machine(self, sm_name, sm_dir=database.paths["task_dir"], uploaded=False):
        '''Transfer state machine descriptor file sm_name.py from folder sm_dir
        to board. Instantiate state machine object as state_machine on pyboard.'''
        self.reset()
        if uploaded:
            self.print('\n Resetting task. ', end='')
        else:
            sm_path = os.path.join(sm_dir, sm_name + '.py')
            if not os.path.exists(sm_path):
                self.print('Error: State machine file not found at: ' + sm_path)
                raise PyboardError('State machine file not found at: ' + sm_path)
            self.print('\nTransfering state machine {} to pyboard. '.format(sm_name), end='')
            self.transfer_file(sm_path, 'task_file.py')
        self.gc_collect()
        try:
            self.exec('import task_file as smd')
            self.exec('state_machine = sm.State_machine(smd)')
            self.print('OK')
        except PyboardError as e:
            self.print('\n\nError: Unable to setup state machine.\n\n' + e.args[2].decode())
            raise PyboardError('Unable to setup state machine.', e.args[2])
        # Get information about state machine.
        states = self.get_states()
        events = self.get_events()
        self.sm_info = {'name'  : sm_name,
                        'states': states, # {name:ID}
                        'events': events, # {name:ID}
                        'ID2name': {ID: name for name, ID in {**states, **events}.items()}, # {ID:name}
                        'analog_inputs': self.get_analog_inputs(), # {name: {'ID': ID, 'Fs':sampling rate}}
                        'variables': self.get_variables()} # {name: repr(value)}
        if self.data_logger:
            self.data_logger.set_state_machine(self.sm_info)

    def get_states(self):
        '''Return states as a dictionary {state_name: state_ID}'''
        return eval(self.exec('fw.get_states()').decode().strip())

    def get_events(self):
        '''Return events as a dictionary {event_name: state_ID}'''
        return eval(self.exec('fw.get_events()').decode().strip())

    def get_variables(self):
        '''Return variables as a dictionary {variable_name: value}'''
        return eval(self.exec('fw.get_variables()').decode().strip())

    def get_analog_inputs(self):
        '''Return analog_inputs as a directory {input name: ID}'''
        return eval(self.exec('hw.get_analog_inputs()').decode().strip())

    def start_framework(self, dur=None, data_output=True):
        '''Start pyControl framwork running on pyboard.'''
        self.gc_collect()
        self.exec('fw.data_output = ' + repr(data_output))
        self.serial.reset_input_buffer()
        self.exec_raw_no_follow('fw.run({})'.format(dur))
        self.framework_running = True

    def stop_framework(self):
        '''Stop framework running on pyboard by sending stop command.'''
        self.serial.write(b'\x03') # Stop signal
        self.framework_running = False

    def process_data(self):
        '''Read data from serial line, generate list new_data of data tuples, 
        pass new_data to data_logger and print_func if specified, return new_data.'''
        new_data = []
        error_message = None
        while self.serial.inWaiting() > 0:
            new_byte = self.serial.read(1)  
            if new_byte == b'A': # Analog data, 13 byte header + variable size content.
                data_header = self.serial.read(13)
                typecode      = data_header[0:1].decode() 
                if typecode not in ('b','B','h','H','l','L'):
                    new_data.append(('!','bad typecode A'))
                    continue   
                ID            = int.from_bytes(data_header[1:3], 'little')
                sampling_rate = int.from_bytes(data_header[3:5], 'little')
                data_len      = int.from_bytes(data_header[5:7], 'little')
                timestamp     = int.from_bytes(data_header[7:11], 'little')
                checksum      = int.from_bytes(data_header[11:13], 'little')
                data_array    = array(typecode, self.serial.read(data_len))
                if checksum == (sum(data_header[:-2]) + sum(data_array)) & 0xffff: # Checksum OK.
                    new_data.append(('A',ID, sampling_rate, timestamp, data_array))
                else:
                    new_data.append(('!','bad checksum A'))
            elif new_byte == b'D': # Event or state entry, 8 byte data header only.
                data_header = self.serial.read(8)
                timestamp = int.from_bytes(data_header[ :4], 'little')
                ID        = int.from_bytes(data_header[4:6], 'little')
                checksum  = int.from_bytes(data_header[6:8], 'little')
                if checksum == sum(data_header[:-2]): # Checksum OK.
                    new_data.append(('D',timestamp, ID))
                else:
                    new_data.append(('!','bad checksum D'))
            elif new_byte in (b'P', b'V'): # User print statement or set variable, 8 byte data header + variable size content.
                data_header = self.serial.read(8)
                data_len  = int.from_bytes(data_header[ :2], 'little')
                timestamp = int.from_bytes(data_header[2:6], 'little')
                checksum  = int.from_bytes(data_header[6:8], 'little')
                data_bytes = self.serial.read(data_len)
                if not checksum == (sum(data_header[:-2]) + sum(data_bytes)) & 0xffff: # Bad checksum.
                    new_data.append(('!','bad checksum ' + new_byte.decode()))
                    continue
                new_data.append((new_byte.decode(),timestamp, data_bytes.decode()))
                if new_byte == b'V': # Store new variable value in sm_info
                    v_name, v_str = data_bytes.decode().split(' ', 1)
                    self.sm_info['variables'][v_name] = eval(v_str)
            elif new_byte == b'\x04': # End of framework run.
                self.framework_running = False
                data_err = self.read_until(2, b'\x04>', timeout=10) 
                if len(data_err) > 2:
                    error_message = data_err[:-3].decode()
                    new_data.append(('!', error_message))                
                break
        if new_data and self.data_logger:
            self.data_logger.process_data(new_data)
        if error_message:
            raise PyboardError(error_message)

    # ------------------------------------------------------------------------------------
    # Getting and setting variables.
    # ------------------------------------------------------------------------------------

    def set_variable(self, v_name, v_value):
        '''Set the value of a state machine variable. If framework is not running
        returns True if variable set OK, False if set failed.  Returns None framework
        running, but variable event is later output by board.'''
        if v_name not in self.sm_info['variables']:
            raise PyboardError('Invalid variable name: {}'.format(v_name))
        v_str = repr(v_value)
        if self.framework_running: # Set variable with serial command.
            data = repr((v_name, v_str)).encode() + b's'
            data_len = len(data).to_bytes(2, 'little')
            checksum = sum(data).to_bytes(2, 'little')
            self.serial.write(b'V' + data_len +  data + checksum)
            return None
        else: # Set variable using REPL.  
            checksum = sum(v_str.encode())
            set_OK = eval(self.eval("state_machine._set_variable({}, {}, {})"
                .format(repr(v_name), repr(v_str), checksum)).decode())
            if set_OK:
                self.sm_info['variables'][v_name] = v_str
            return set_OK

    def get_variable(self, v_name):
        '''Get the value of a state machine variable. If framework not running returns
        variable value if got OK, None if get fails.  Returns None if framework 
        running, but variable event is later output by board.'''
        if v_name not in self.sm_info['variables']:
            raise PyboardError('Invalid variable name: {}'.format(v_name))        
        if self.framework_running: # Get variable with serial command.
            data = v_name.encode() + b'g'
            data_len = len(data).to_bytes(2, 'little')
            checksum = sum(data).to_bytes(2, 'little')
            self.serial.write(b'V' + data_len +  data + checksum)
        else: # Get variable using REPL.
            return eval(self.eval("state_machine._get_variable({})"
                                  .format(repr(v_name))).decode())