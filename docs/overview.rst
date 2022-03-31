Overview
========

Co- **S**\imulation **O**\f **F**\unctional Mock-up Units (FMU) with **I**\ntegrated
**R**\esearch Data Management (SOFIRpy) is a python package that lets you
co-simulate FMUs with custom models written in python.

The package provides functionalities to:

- Export Dymola and OpenModelica models as a FMU
- Co-simulate FMUs with custom written models in python
- Store data and meta data of the simulation inside a hdf5 file

Use Cases
---------

**Control of physical systems.**

Tools like OpenModelica and Dymola are excellent tools for modelling complex
physical systems. These models can be exported as FMUs and co-simulated with
custom written controllers in python. Thereby Python offers extensive tools for
the development of control systems, such as machine learning toolboxes, so that
complex control strategies can be implemented.

**Automation of Simulation workflow**

Easy to use functionalities to store data inside a hdf5 allows to implement a
automated simulation workflow (Example illustrating possible workflow coming in
the future).