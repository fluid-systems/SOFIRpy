Getting started
===============

To start using fair_sim, import the package::

	import fair_sim	

The following 3 examples demonstrate how to export a modelica model as a fmu, simulate a fmu and a controller and how to store simulation results.

Exporting a modelica model
--------------------------

fair_sim allows to export a open_modelica and dymola model as a fmu.

Exporting a open_modelica model.

.. literalinclude:: ../examples/fmu_export/open_modelica_fmu_export.py

Exporting a dymola model.

.. literalinclude:: ../examples/fmu_export/dymola_fmu_export.py

Simulating a fmu and a Controller
---------------------------------

.. literalinclude:: ../examples/simulating/simulating_fmus_and_controllers/simulation.py

Storing results
---------------

Additional examples
-------------------

Additional examples are listed below:

* `Simulating mutiple fmus and controller <https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release/-/tree/development/examples>`_
* `Import parameters before exporting a dymola model <https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release/-/tree/development/examples>`_