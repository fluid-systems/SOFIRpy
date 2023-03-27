Connect systems
===============

The following example demonstrates how multiple systems can be connected for the simulation.

Consider the following systems.

.. image:: Images/connection_diagram.svg

For each input of a system it must be defined with which output of another system the
input is to be connected.
For the shown system the variable 'connections_config must be defined as follows.
The variable 'connections_config is an input for the
:py:func:`simulate() <sofirpy.simulation.simulation.simulate>`
function.

.. code-block:: python3

    >>> connections_config = {
    ...     "FMU1": [
    ...         {
    ...             "parameter_name": "fmu1_input1",
    ...             "connect_to_system": "CustomSystem1",
    ...             "connect_to_external_parameter": "custom_system1_output1",
    ...         }
    ...     ],
    ...     "FMU2": [
    ...         {
    ...             "parameter_name": "fmu2_input1",
    ...             "connect_to_system": "FMU1",
    ...             "connect_to_external_parameter": "fmu1_output2",
    ...         }
    ...     ],
    ...     "CustomSystem1": [
    ...         {
    ...             "parameter_name": "custom_system1_input1",
    ...             "connect_to_system": "FMU1",
    ...             "connect_to_external_parameter": "fmu1_output1",
    ...         },
    ...         {
    ...             "parameter_name": "custom_system1_input2",
    ...             "connect_to_system": "CustomSystem2",
    ...             "connect_to_external_parameter": "custom_system2_output1",
    ...         },
    ...     ],
    ... }
