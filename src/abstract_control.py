from abc import ABC, abstractmethod

class Control(ABC):

    @abstractmethod
    def set_input(self, input_name, input_value):
        pass
    @abstractmethod
    def generate_output(self):
        pass
    @abstractmethod
    def get_output(self, output_name):
        pass

    @abstractmethod
    def get_unit(self, variable_name):
        pass
