[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15355753.svg)](https://doi.org/10.5281/zenodo.15355753)
# PEtabGUI


This is a graphical user interface to create parameter estimation problems. It is 
based on the [PEtab](https://petab.readthedocs.io/en/latest/#) format.

## Installation

You can install the PEtabGUI via pip by running
```bash
pip install petab_gui
```

To install the PEtabGUI directly from GitHub, you can follow these steps:

1. Clone the repository:
```bash
git clone https://github.com/PaulJonasJost/PEtab_GUI.git
```

2. Pip install the PEtab GUI:
```bash
pip install .
```
(Run this command line within the repository folder)


## Usage

To start the PEtab GUI, you can run the following command line:
```bash
petab_gui $PATH_TO_YOUR_MODEL
```
where `$PATH_TO_YOUR_MODEL` is an optional argument with a file path of your 
yaml-model file in case you want to work on an existing model. You can also leave this 
argument out to start from scratch.
