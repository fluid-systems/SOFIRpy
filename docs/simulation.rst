Simulation
==========

sofirpy allows you to simulate multiple FMUs and custom implemented python models by
calling the :py:func:`simulate <sofirpy.simulation.simulation.simulate>` function.

The function accepts the following arguments:

stop_time
---------

Define the stop_time in seconds.

.. code-block:: python

    stop_time = 10 # 10 seconds of simulation will be performed

step_size
---------

Define the step_size in seconds. Needs to be greater than 0 and smaller than the
stop_time.

.. code-block:: python

    step_size = 1 # starting from 0, each second a step in each model is performed until the stop_time is reached.

fmu_paths
---------

Define which FMUs should be simulated by passing a dictionary with the name of the
fmu and the file path as value. The name of the FMUs can be chosen arbitrarily, but
each name must occur only once.

.. code-block:: python

    from pathlib import Path

    # simulate one FMU named DC_Motor
    fmu_paths = {"DC_Motor": Path(__file__).parent / "DC_Motor.fmu"}

model_classes
-------------

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
