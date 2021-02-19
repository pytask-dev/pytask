"""The setup.py for pytask."""
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

import versioneer


DESCRIPTION = "In its highest aspirations, pytask tries to be pytest as a build system."

# Remove the image from the README.rst since the raw directive is not allowed.
README = "\n".join(Path("README.rst").read_text().split("\n")[5:])

PROJECT_URLS = {
    "Documentation": "https://pytask-dev.readthedocs.io/en/latest",
    "Github": "https://github.com/pytask-dev/pytask",
    "Tracker": "https://github.com/pytask-dev/pytask/issues",
}


setup(
    name="pytask",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description=DESCRIPTION,
    long_description=README,
    long_description_content_type="text/x-rst",
    author="Tobias Raabe",
    author_email="raabe@posteo.de",
    url=PROJECT_URLS["Github"],
    project_urls=PROJECT_URLS,
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Build Tools",
    ],
    install_requires=[
        "attrs >= 17.4.0",
        "click",
        "click-default-group",
        "networkx",
        "pluggy",
        "pony >= 0.7.13",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["pytask=_pytask.cli:cli"]},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    platforms="any",
    include_package_data=True,
)
