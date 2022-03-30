Getting started
===============

To start using sofirpy, import the package::

	import sofirpy	

The following 3 examples demonstrate how to export a Modelica model as a fmu,
simulate a fmu and a controller and how to initialize a project.

Exporting a modelica model
--------------------------

sofirpy allows to export a OpenModelica and Dymola model as a fmu.

**Exporting a OpenModelica model**

.. literalinclude:: ../examples/fmu_export/open_modelica_model_export/open_modelica_model_export_example.py

**Exporting a Dymola model and importing parameters**

.. literalinclude:: ../examples/fmu_export/dymola_model_export/dymola_model_export_parameter_import_example.py

Simulating a fmu and a Controller
---------------------------------

.. literalinclude:: ../examples/simulating/simulating_fmu_and_controller/simulation_example.py

The custom implemented pid controller is shown below.

.. literalinclude:: ../examples/simulating/simulating_fmu_and_controller/discrete_pid.py

Initializing a project and storing data
----------------------------------------

.. literalinclude:: ../examples/project/project_example.py

Additional examples
-------------------

Additional examples can be found `here. <https://git.rwth-aachen.de/sofirpy/sofirpy/-/tree/master/examples>`_
