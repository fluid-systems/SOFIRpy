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
    description="A package to simulate fmus and controllers.",
    long_description=long_description,
    url="https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release",
    packages= ["fair_sim"],
    python_requires=">=3.6",
)
