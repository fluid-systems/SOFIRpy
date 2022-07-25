from pathlib import Path
from setuptools import setup

rootdir = Path(__file__).parent

with open(rootdir / "README.md", 'r') as f:
    long_description = f.read()

setup(
    name="SOFIRpy",
    version="0.1.0",
    author="Daniele Inturri",
    author_email="daniele.inturri@stud.tu-darmstadt.de",
    description="Framework for simulating FMUs and custom models written in python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.rwth-aachen.de/sofirpy/sofirpy",
    packages= ["sofirpy", "sofirpy.fmu_export", "sofirpy.simulation", "sofirpy.project"],
    install_requires = ["FMPy",
                        "tqdm",
                        "h5py",
                        "matplotlib",
                        "numpy",
                        "pandas",
                        "OMpython"],

    python_requires=">=3.9",
)
