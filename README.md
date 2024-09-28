 # SOFIRpy
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PyPI - Version](https://img.shields.io/pypi/v/sofirpy?label=Latest%20Release)](https://pypi.org/project/sofirpy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/fluid-systems/SOFIRpy/actions/workflows/tests.yml/badge.svg)](https://github.com/fluid-systems/SOFIRpy/actions/workflows/testing.yml)
[![codecov](https://codecov.io/gh/fluid-systems/SOFIRpy/graph/badge.svg?token=M27RHN06DS)](https://codecov.io/gh/fluid-systems/SOFIRpy)
[![Documentation](https://github.com/fluid-systems/SOFIRpy/actions/workflows/build_deploy_pages.yml/badge.svg)](https://fluid-systems.github.io/SOFIRpy/)

Co-**S**imulation **O**f **F**unctional Mock-up Units (FMU) with **I**ntegrated
**R**esearch Data Management (SOFIRpy) is a python package that lets you
co-simulate FMUs with custom models written in python.
The package provides functionalities to:
- Export Dymola and OpenModelica models as a FMU
- Co-simulate FMUs with custom written models in python
- Store data and meta data of the simulation inside a hdf5 file

 ## Install
SOFIRpy can be installed from PyPI using the following command.
```console
$ pip install sofirpy
```
## Documentation
The documentation can be found [here](https://fluid-systems.github.io/SOFIRpy).

## Examples
Multiple examples can be found [here](https://github.com/fluid-systems/SOFIRpy/tree/master/examples).
