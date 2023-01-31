from sofirpy import SimulationEntity, store_input_arguments
from sofirpy.project.serialize import HDF5Serialization


class PID(SimulationEntity, HDF5Serialization):
    """Simple implementation of a discrete pid controller"""

    @store_input_arguments
    def __init__(
        self, step_size, K_p=1, K_i=0, K_d=0, set_point=0, u_max=1000, u_min=-1000
    ):

        self.T_a = step_size
        self.K_p = K_p
        self.K_i = K_i
        self.K_d = K_d
        self.set_point = set_point
        self.parameters = {"speed": 0, "u": 0}
        self.d_0 = K_p * (
            1 + (self.T_a * self.K_i / self.K_p) + self.K_d / (self.K_p * self.T_a)
        )
        self.d_1 = K_p * (-1 - 2 * self.K_d / (self.K_p * self.T_a))
        self.d_2 = K_p * self.K_d / (self.K_p * self.T_a)
        self.error = [0, 0, 0]
        self.u_max = u_max
        self.u_min = u_min

    def compute_error(self):

        self.error[2] = self.error[1]
        self.error[1] = self.error[0]
        self.error[0] = self.set_point - self.parameters["speed"]

    def set_input(self, input_name, input_value):

        self.parameters[input_name] = input_value

    def do_step(self, _):  # mandatory method

        self.compute_error()
        u = (
            self.parameters["u"]
            + self.d_0 * self.error[0]
            + self.d_1 * self.error[1]
            + self.d_2 * self.error[2]
        )
        if u > self.u_max or u < self.u_min:
            if u > self.u_max:
                u = self.u_max
            if u < self.u_min:
                u = self.u_min

        self.parameters["u"] = u

    def set_parameter(
        self, parameter_name, parameter_value
    ) -> None:  # mandatory method
        self.parameters[parameter_name] = parameter_value

    def get_parameter_value(self, output_name):  # mandatory method
        return self.parameters[output_name]

    def initialize(self, start_values) -> None:
        self.apply_start_values(start_values)

    def apply_start_values(self, start_values) -> None:

        for name, value in start_values.items():
            self.parameters[name] = value
