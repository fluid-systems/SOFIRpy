import os

from setuptools import setup

rootdir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(rootdir,"README.md"), 'r') as f:
    long_description = f.read()

setup(
    name="fair_sim_release",
    version="0.0.1",
    author="Daniele Inturri",
    author_email="daniele.inturri@sud.tu-darmstadt.de",
    description="Framework for simulating fmus and controller written in python.",
    long_description=long_description,
    url="https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release",
    packages= ["fair_sim"],
    install_requires = ["FMPy == 0.2.26",
                        "OMPython == 3.3.0",
                        "alive_progress == 1.6.2",
                        "buildingspy == 2.1.0",
                        "h5py == 3.1.0",
                        "matplotlib == 3.3.4",
                        "numpy == 1.19.3",
                        "pandas == 1.2.0"
                        ],
    python_requires=">=3.6",
)
