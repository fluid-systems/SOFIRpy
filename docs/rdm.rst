RDM
===

SOFIRpy allows you to easily store and read your simulation data.

Creating and manipulating a simulation run
------------------------------------------

You can create a simulation run by importing the :py:class:`Run <sofirpy.rdm.run.Run>`
class. The run class is instantiated by providing a config file. The config file
defines all relevant simulation data. The config file has the following structure:

.. literalinclude:: ../examples/rdm/example_config.json

The class can then be instantiated as follows:

.. code-block:: python

    from sofirpy import Run

    run_name = "Run_1"
    config_path = Path("example_config.json")
    model_classes = {"pid": PID}
    fmu_path = Path("DC_Motor.fmu")
    fmu_paths = {"DC_Motor": fmu_path}

    run = Run.from_config(run_name, config_path, fmu_paths, model_classes)

The :py:class:`Run <sofirpy.rdm.run.Run>` offers multiple methods to read or manipulate
the simulation data. Few examples:

.. code-block:: python

    run.stop_time = 100 # change the stop time
    run.set_start_value(
        model_name="<model_name>",
        parameter_name="<name of the parameter>",
        value=new_start_value,
        )
    path_to_fmu = run.get_fmu_path("<model_name>")

See :py:class:`Run <sofirpy.rdm.run.Run>` for all available methods.

After configuration the run can be simulated by calling the simulate method:

.. code-block:: python

    run.simulate()
    result = run.time_series
    units = run.units

The simulated run can then be stored inside a hdf5 file. All relevant data is stored to
be able to recreate the simulation.

.. code-block:: python

    run.to_hdf5(hdf5_path = "path/to/hdf5")

If the hdf5 file does not exists it will be created for you. The hdf5 will also be
initialized by writing meta data to it and creating a models group. In here the
simulated models will be stored. The fmus are written as binaries to the hdf5. The user
defined classed are stored by storing the source code of the class. If possible the
class will be serialized. This makes it really easy to rerun the simulation from the hdf5.

A new run will be stored in a top level group with the name of the run. All the
configuration data, results and the dependencies of your python environment are stored
here.
