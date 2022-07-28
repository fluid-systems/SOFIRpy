from typing import Union
import json
import nidaqmx
from sofirpy.simulation.simulation_entity import SimulationEntity
import time as ttime

class Testrig(SimulationEntity):
    """Class representing the testrig."""

    def __init__(self, testrig_json_path, step_size):
        """Initialize Testrig object.

        Args:
            testrig_json_path (Path): path to the testrig .json-file 
        """
        self.testrig_json_path = testrig_json_path
        self.step_size = step_size
        self.start_list = {}

    def initialize_testrig(self):
        """Initialize the nidaqmx environment.

        Args:
            start_time (float, optional): start time. Defaults to 0.
        """
        with open('S:/Logan/202205_MA_Meck/Git/mt-meck/code/schnittstelle/testrig.json') as jf:
            self.testrig_metadata = json.load(jf)
    
        for component in self.testrig_metadata:    # Später nicht über alle iterieren, sondern nur über die die auch wirklich gebraucht werden
            for part in self.testrig_metadata[component]:
                if isinstance(self.testrig_metadata[component][part],dict):
                    self.testrig_metadata[component][part]['Task'] = nidaqmx.Task()
                    if self.testrig_metadata[component][part]['Channel-Type'] == 'AI':
                        if self.testrig_metadata[component][part]['Terminal-Config'] == 'RSE':
                            self.testrig_metadata[component][part]['Task'].ai_channels.add_ai_voltage_chan(
                                self.testrig_metadata[component][part]['Channel'], terminal_config=nidaqmx.constants.TerminalConfiguration.RSE)
                        else:
                            raise(ValueError('No other Types except RSE supported at the moment'))
                    elif self.testrig_metadata[component][part]['Channel-Type'] == 'AO':
                        self.testrig_metadata[component][part]['Task'].ao_channels.add_ao_voltage_chan(
                            self.testrig_metadata[component][part]['Channel'])
        
    def set_input(self, input_name: str, input_value: Union[float, int]):
        """Set the value of an input parameter.

        Args:
            input_name (str): name of the parameter that should be set. Use dot notation (component.part)
            input_value (Union[float, int]): value to which the parameter
                is to be set
        """
        component, part = input_name.split('.')
        self.testrig_metadata[component][part]['Task'].start()
        self.testrig_metadata[component][part]['Task'].write(self.conversion(input_value, **self.testrig_metadata[component][part]['Conversion']), timeout=0)
        self.testrig_metadata[component][part]['Task'].stop()

    def get_parameter_value(self, parameter_name: str) -> Union[int, float]:
        """Return the value of a parameter.

        Args:
            parameter_name (str): name of parameter whose value is to be
                obtained. Use dot notation (component.part)

        Returns:
            Union[int, float]: value of the parameter
        """
        component, part = parameter_name.split('.')
        if parameter_name not in self.start_list:
            self.start_list[parameter_name] = ttime.time()
        elif ttime.time() - self.start_list[parameter_name] < self.step_size:
            ttime.sleep(self.step_size - (ttime.time() - self.start_list[parameter_name]))
            self.start_list[parameter_name] = ttime.time()
        else:
            print('Sample rate too high...' , str(self.step_size - (ttime.time() - self.start_list[parameter_name])))
        return self.conversion(self.testrig_metadata[component][part]['Task'].read(timeout=0.1),**self.testrig_metadata[component][part]['Conversion'])

    def do_step(self, time: float):
        """Perform simulation entity calculation and set parameters accordingly.

        Args:
            time (float): current simulation time
        """
        pass
        #ttime.sleep(0.5)

    def conversion(self, x, x_max, x_min, y_min, y_max):
        """
        Etwas verwirrend: x ist bei steuerelementen die physikalische Größe (rpm, opening, ...), y z.B. die Spannung. 
        Bei Messelementen ist x z.B. die Spannung und y die resultierende physikalische Größe
        """
        return (x-x_min)*(y_max-y_min)/(x_max-x_min)+y_min

# TODO add get_units