from setuptools import find_packages
from setuptools import setup

setup(
    name="pytask",
    entry_points={"console_scripts": ["pytask=pytask.cli:pytask"]},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
