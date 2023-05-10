from sofirpy import SimulationEntity, store_input_arguments
from sofirpy.simulation.simulation import StartValues


class PID(SimulationEntity):
    """Simple implementation of a discrete pid controller"""

    @store_input_arguments
    def __init__(self):
        self.parameters = {
            "sampling_rate": 1e-3,
            "K_p": 1,
            "K_i": 0,
            "K_d": 0,
            "set_point": 0,
            "u_max": 1000,
            "u_min": -1000,
        }
        self.inputs = {"speed": 0}
        self.outputs = {"u": 0}

    def compute_error(self):

        self.error[2] = self.error[1]
        self.error[1] = self.error[0]
        self.error[0] = self.parameters["set_point"] - self.inputs["speed"]

    def set_input(self, input_name, input_value):

        self.parameters[input_name] = input_value

    def do_step(self, _):  # mandatory method
        self.compute_error()
        u = (
            self.outputs["u"]
            + self.d_0 * self.error[0]
            + self.d_1 * self.error[1]
            + self.d_2 * self.error[2]
        )
        if u > self.u_max or u < self.u_min:
            if u > self.u_max:
                u = self.u_max
            if u < self.u_min:
                u = self.u_min

        self.outputs["u"] = u

    def set_parameter(
        self, parameter_name, parameter_value
    ) -> None:  # mandatory method
        self.inputs[parameter_name] = parameter_value

    def get_parameter_value(self, output_name):  # mandatory method
        return self.outputs[output_name]

    def initialize(
        self, start_values
    ) -> None:  # start values passed to simulation function are passed to this method
        self.apply_start_values(start_values)
        K_p = self.parameters["K_p"]
        K_i = self.parameters["K_i"]
        K_d = self.parameters["K_d"]
        T_a = self.parameters["sampling_rate"]
        self.d_0 = K_p * (1 + (T_a * K_i / K_p) + K_d / (K_p * T_a))
        self.d_1 = K_p * (-1 - 2 * K_d / (K_p * T_a))
        self.d_2 = K_p * K_d / (K_p * T_a)
        self.error = [0, 0, 0]
        self.u_max = self.parameters["u_max"]
        self.u_min = self.parameters["u_min"]

    def apply_start_values(self, start_values: StartValues) -> None:
        for name, value in start_values.items():
            self.parameters[name] = value


# PID.__module__ = "__main__"

# %%
