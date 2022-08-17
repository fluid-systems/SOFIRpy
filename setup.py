from pathlib import Path
from setuptools import setup

rootdir = Path(__file__).parent

with open(rootdir / "README.md", "r") as f:
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
        classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
    ],
    keywords="simulation",
    packages=["sofirpy", "sofirpy.fmu_export", "sofirpy.simulation", "sofirpy.project"],
    python_requires=">=3.9",
    install_requires=[
        "FMPy",
        "tqdm",
        "h5py",
        "matplotlib",
        "numpy",
        "pandas",
        "OMpython",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov"],
    },
)
