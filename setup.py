from setuptools import setup, find_packages
import os

# Find mgc version.
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
for line in open(os.path.join(PROJECT_PATH, "kdg", "__init__.py")):
    if line.startswith("__version__ = "):
        VERSION = line.strip().split()[2][1:-1]

with open("README.rst", mode="r") as f:
    LONG_DESCRIPTION = f.read()

with open("requirements.txt", mode="r") as f:
    REQUIREMENTS = f.read()

setup(
    name="kdg",
    version=VERSION,
    author="Jayanta Dey",
    author_email="jdey4@jhmi.edu",
    maintainer="Jayanta Dey",
    maintainer_email="jdey4@jhmi.edu",
    description="A a package for exploring and using kernel density algorithms",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/jdey4/kdg/",
    license="MIT",
    classifiers=[
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["tests", "tests.*", "tests/*"]),
    include_package_data=True
)
