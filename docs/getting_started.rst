Getting started
===============

The following 3 examples demonstrate how to export a Modelica model as a FMU,
co-simulate a FMU and a controller and how to use the rdm features.

Exporting a modelica model
--------------------------

SOFIRpy allows to export a OpenModelica and Dymola model as a FMU.

**Exporting a OpenModelica model**

.. literalinclude:: ../examples/fmu_export/open_modelica_model_export/open_modelica_model_export_example.py

**Exporting a Dymola model**

.. literalinclude:: ../examples/fmu_export/dymola_model_export/dymola_model_export_example.py

Simulating a FMU and a Controller
---------------------------------

.. literalinclude:: ../examples/simulating/simulating_fmu_and_controller/simulation_example.py

The custom implemented pid controller is shown below.

.. literalinclude:: ../examples/discrete_pid.py


RDM Features
------------

This example demonstrates how to create a simulation run from a config file, store the
run inside a HDF5 file and read the run again from the HDF5 file.

.. literalinclude:: ../examples/rdm/run_example.py
