Overview
========

This package provides a framework to co-simulate Functional Mock-up Units (FMU)
with custom models written in python and to store the data and
meta data of the simulation according to the Research Data Management (RDM).
Additionally the package provides functionalities to export a OpenModelica or
Dymola model as a fmu.

Use Cases
---------

**Control of physical systems.**

Tools like OpenModelica and Dymola are excellent tools for modelling complex
physical systems. These models can be exported as FMUs and co-simulated with
custom written controllers in python. Thereby Python offers extensive tools for
the development of control systems, such as machine learning toolboxes, so that
complex control strategies can be implemented.

**Automation of Simulation workflow**
