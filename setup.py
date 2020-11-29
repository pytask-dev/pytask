"""The setup.py for pytask."""
from pathlib import Path

from setuptools import find_packages
from setuptools import setup


DESCRIPTION = "In its highest aspirations, pytask tries to be pytest as a build system."
README = Path("README.rst").read_text()
PROJECT_URLS = {
    "Bug Tracker": "https://github.com/pytask-dev/pytask/issues",
    "Documentation": "https://pytask-dev.readthedocs.io/en/latest",
    "Source Code": "https://github.com/pytask-dev/pytask",
}

setup(
    name="pytask",
    version="0.0.10",
    description=DESCRIPTION,
    long_description=DESCRIPTION + "\n\n" + README,
    long_description_content_type="text/x-rst",
    author="Tobias Raabe",
    author_email="raabe@posteo.de",
    python_requires=">=3.6",
    url=PROJECT_URLS["Documentation"],
    project_urls=PROJECT_URLS,
    license="None",
    keywords=["Build System"],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Framework :: pytask",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    platforms="any",
    entry_points={"console_scripts": ["pytask=_pytask.cli:cli"]},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
