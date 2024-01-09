Simulation
==========

SOFIRpy allows you to co-simulate multiple FMUs and custom implemented python models.

Arguments to the `simulate` Function
------------------------------------

The function :py:func:`simulate <sofirpy.simulation.simulation.simulate>` accepts the
following arguments:

stop_time
^^^^^^^^^

Define the stop_time in seconds.

.. code-block:: python

    stop_time = 10 # 10 seconds of simulation will be performed

step_size
^^^^^^^^^

Define the step_size in seconds. Needs to be greater than 0 and smaller than the
stop_time.

.. code-block:: python

    step_size = 1 # starting from 0, each second a step in each model is performed until the stop_time is reached.

fmu_paths
^^^^^^^^^

Define which FMUs should be simulated by passing a dictionary with the name of the
fmu and the file path as value. The name of the FMUs can be chosen arbitrarily, but
each name must occur only once.

.. code-block:: python

    # simulate one FMU named DC_Motor
    fmu_paths = {"<fmu_name>": "<Path/to/fmu>"}

model_classes
^^^^^^^^^^^^^^

Define the custom implemented python models that should be simulated by passing a
dictionary with the name of the python model and the model as value.
The python models are **classes** that inherit from the abstract class
:py:class:`SimulationEntity <sofirpy.simulation.simulation_entity.SimulationEntity>`.
This class defines 3 abstract methods that must be implemented by your custom python
models:

- :py:meth:`SimulationEntity.do_step(time) <sofirpy.simulation.simulation_entity.SimulationEntity.do_step>`:

    Define how your models performs a simulation step.

- :py:meth:`SimulationEntity.set_parameters(parameter_name, parameter_value) <sofirpy.simulation.simulation_entity.SimulationEntity.set_parameters>`:

    Define how the parameters of your models are set.\

- :py:meth:`SimulationEntity.get_parameter_value(parameter_name) <sofirpy.simulation.simulation_entity.SimulationEntity.get_parameter_value>`:

    Define how to get the value of a parameter of your model.

Additionally 3 optional method can be implemented:

- :py:meth:`SimulationEntity.initialize(start_values) <sofirpy.simulation.simulation_entity.SimulationEntity.initialize>`:

    Define how to set the start values of your model before the simulation starts.

- :py:meth:`SimulationEntity.get_unit(parameter_name) <sofirpy.simulation.simulation_entity.SimulationEntity.get_unit>`:

    Define how to get the unit of a parameter.

- :py:meth:`SimulationEntity.conclude_simulation() <sofirpy.simulation.simulation_entity.SimulationEntity.conclude_simulation>`:

    Define functionalities that your model should perform after the simulation has
    finished.

Example:

.. code-block:: python

    from sofirpy import SimulationEntity

    # First define the class
    class Foo(SimulationEntity):

        def __init__(self):
            self.parameters = {"parameter1": 0, "parameter2": 0}
            self.units = {"parameter1": "m", "parameter2": "V"}

        def do_step(self, time):  # mandatory method
            self.parameter["parameter1"] += time/100
            self.parameter["parameter2"] += 1

        def set_parameter(
            self, parameter_name, parameter_value
        ):  # mandatory method
            self.parameters[parameter_name] = parameter_value

        def get_parameter_value(self, output_name):  # mandatory method
            return self.parameters[output_name]

        def initialize(self, start_values):  # optional
            for name, value in start_values.items():
                self.parameters[name] = value

        def get_unit(self, parameter_name): #optional
            return self.units.get(parameter_name)

        def conclude_simulation(self): # optional
            print("Concluded simulation!")

    # simulate one python model called foo
    model_classes = {"foo": Foo} # we pass the class not the instance!

.. note::
    A **class** is passed as the values of the dictionary not an instance of the class.


connections_config
^^^^^^^^^^^^^^^^^^^

Define how the inputs and outputs of the systems are connected.

Lets assume we have the following configuration.

.. image:: Images/connection_diagram.svg


Each input of a system must have a corresponding output of another system it is
connected to. We define these connections as follows:

.. code-block:: python

    connections_config = {
        "FMU1": [
            {
                "parameter_name": "fmu1_input1",
                "connect_to_system": "CustomSystem1",
                "connect_to_external_parameter": "custom_system1_output1",
            }
        ],
        "FMU2": [
            {
                "parameter_name": "fmu2_input1",
                "connect_to_system": "FMU1",
                "connect_to_external_parameter": "fmu1_output2",
            }
        ],
        "CustomSystem1": [
            {
                "parameter_name": "custom_system1_input1",
                "connect_to_system": "FMU1",
                "connect_to_external_parameter": "fmu1_output1",
            },
            {
                "parameter_name": "custom_system1_input2",
                "connect_to_system": "CustomSystem2",
                "connect_to_external_parameter": "custom_system2_output1",
            },
        ],


The keys of the dictionary are the names of the systems that have at least one input.
The values of the dictionary define how a input of the system is connected to the output
of another system.

start_values
^^^^^^^^^^^^

Define start_values for your systems. For the fmus you can also pass the unit of the
value. The start values for a each system will be passed to the initialize method of the
corresponding class.

.. code-block:: python

    start_values = {
        "<name of system 1>":
        {
            "<name of parameter 1>": <start value>,
            "<name of parameter 2>", (<start value>, unit e.g 'kg.m2')
        },
        "<name of system 2>":
        {
            "<name of parameter 1>": <start value>,
            "<name of parameter 2>": <start value>
        }
    }


parameters_to_log
^^^^^^^^^^^^^^^^^^

Define which parameters should be logged during the simulation.

.. code-block:: python

    parameters_to_log = {
            "<name of system 1>":
            [
                "<name of parameter 1>",
                "<name of parameter 2>",
            ],
            "<name of system 2>":
            [
                "<name of parameter 1>",
                "<name of parameter 2>",
            ]
        }

logging_step_size
^^^^^^^^^^^^^^^^^

Define a logging step size. The logging step size must be a multiple of the step size.

get_units
^^^^^^^^^

Define whether to return a dictionary with units of the logged parameters. If the units
are not defined inside your implemented classes they will be set to None.

Return values of the `simulate` function
----------------------------------------

The function :py:func:`simulate <sofirpy.simulation.simulation.simulate>` returns the
following:

results
^^^^^^^

The results of the simulation is a pandas DataFrame. The first column is the time.
The other columns are are named as follows '<system_name>.<parameter_name>' for all
the logged parameters.

units
^^^^^

Dictionary of units of the logged parameters.
