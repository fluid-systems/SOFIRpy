import setuptools

with open("README", 'r') as f:
    long_description = f.read()

setuptools.setup(
    name="fairsim",
    version="0.0.1",
    author="Daniele Inturri",
    author_email="daniele.inturri@sud.tu-darmstadt.de",
    description="A small example package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    project_urls={
        
    },
    classifiers=[
        
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)