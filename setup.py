# %%
import os

from setuptools import setup, find_packages

rootdir = os.path.abspath(os.path.dirname(__file__))
print(rootdir)

with open(os.path.join(rootdir,"README.md"), 'r') as f:
    long_description = f.read()

setup(
    name="fair_sim_release",
    version="0.1",
    author="Daniele Inturri",
    author_email="daniele.inturri@sud.tu-darmstadt.de",
    description="A package to simulate fmus and controllers. It also provides a workflow that simplifies simulation and allows data to be stored according to the fair principles.",
    long_description=long_description,
    url="https://git.rwth-aachen.de/fst-tuda/projects/digitalization/fair_sim/fair_sim_release",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.6",
)

# %%
