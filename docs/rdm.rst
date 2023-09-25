RDM
===

SOFIRpy allows you to easily store and read your simulation data.

Creating and manipulating a simulation run
------------------------------------------

You can create a simulation run by importing the :py:class:`Run <sofirpy.rdm.run.Run>`
class. The :py:class:`Run <sofirpy.rdm.run.Run>` class is instantiated by providing a
config file. The config file defines all relevant simulation data. The config file has
the following structure:

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

The :py:class:`Run <sofirpy.rdm.run.Run>` class offers multiple methods to read or manipulate
the simulation data. Few examples:

.. code-block:: python

    run.stop_time = 100 # change the stop time
    run.set_start_value(
        model_name="<model_name>",
        parameter_name="<name of the parameter>",
        value=new_start_value,
    ) # set the start value of a parameter
    path_to_fmu = run.get_fmu_path("<model_name>") # get the path of a fmu

See :py:class:`Run <sofirpy.rdm.run.Run>` for all available methods.

After configuration the run can be simulated by calling the simulate method:

.. code-block:: python

    run.simulate()
    result = run.time_series
    units = run.units

Storing a Run
-------------

The simulated run can then be stored inside a hdf5 file. All relevant data is stored to
be able to recreate the simulation.

.. code-block:: python

    run.to_hdf5(hdf5_path = "path/to/hdf5")

If the HDF5 file doesn't already exist, it will be created for you automatically.
The HDF5 file is then initialized by adding metadata and creating a "models" group
within it.
The FMUs are stored as binary data inside this group.
The custom defined model_classes are preserved by storing their source code. If
possible these classes are also serialized using
`cloudpickle <https://github.com/cloudpipe/cloudpickle>`_.
This makes it easy to rerun the simulation from the hdf5. However, it is not always
possible to read back the serialized model_classes. In :ref:`Loading a Run` the
limitations are discussed.

A new run will be stored in a top level group with the name of the run. All the
configuration data, results and the dependencies of your python environment are stored
here.

.. _loading a run:

Loading a Run
-------------

Loading a run from a hdf5 can be achieved as follows:

.. code-block:: python

    from sofirpy import Run

    Run.from_hdf5(run_name="run_name", hdf5_path = "path/to/hdf5")


The ability to simulate a stored run from an HDF5 file depends on the compatibility of
the current environment with the environment at the time the run was saved.
Specifically, if both the operating system and Python version of the current environment
match those of the original run, it is feasible to rerun the simulation.

However, if there is a disparity in the Python version, and custom model classes were
defined in the original run, rerunning the simulation might not be possible.
Nevertheless, the model classes can be manually reconstructed using the stored source
code of the classes and the dependencies used when storing the run.

In cases where the operating system differs from the one in which the run was initially
executed, simulating the model classes and the FMUs could fail.
