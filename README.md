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

## Features

The PEtabGUI is a Pythin based graphical user interface that simplifies the creation, 
editing, and validation of PEtab parameter estimation problems.
- **Unified Environment**
  - Integrates all PEtab components (SBML/PySB models, conditions, observables, 
    measurements, parameters, and visualization files). 
  - Supports drag-and-drop import of YAML or individual component files. 
  - Automatically resolves mismatches and converts matrix-format experimental data 
    into valid PEtab format.
- **Interactive and Intuitive Editing**
  - Dockable, resizable, and movable table widgets for each PEtab file. 
  - Context-aware editing with combo-boxes, drop-downs, and multi-cell editing. 
  - Automatic generation of missing observables/conditions with customizable defaults. 
  - Real-time validation and plausibility checks with PEtab linting tools. 
  - SBML view in both XML and human-readable Antimony syntax. 
- **Visualization and Simulation**
  - Interactive plots linking measurement data with model simulations.
  - Bidirectional highlighting between plots and tables.
  - Built-in simulation via BASICO with one-click parameter testing.
  - Intelligent defaults for visualization with optional user customization.
  - Ability to disable plotting for large models to maintain responsiveness.
- **Archiving and Export**
  - Export individual tables, the SBML model, or complete PEtab problems. 
  - Save as directory structures or COMBINE archives for reproducibility
