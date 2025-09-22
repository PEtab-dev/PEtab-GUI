[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.15355753.svg)](https://doi.org/10.5281/zenodo.15355753)
# PEtabGUI


PEtabGUI provides a graphical user interface to inspect and edit parameter
estimation problems encoded in the
[PEtab](https://petab.readthedocs.io/en/latest/#) format.

## Installation

### From PyPI

To install PEtabGUI from [PyPI](https://pypi.org/project/PEtab-GUI/), run:

```bash
pip install petab_gui
```

### From GitHub

To install the latest development version from GitHub, run:

```bash
    pip3 install git+https://github.com/PaulJonasJost/PEtab_GUI/
```

### From a local copy

1. Clone the repository:

   ```bash
   git clone https://github.com/PaulJonasJost/PEtab_GUI.git
   ```

2. Install the package from the root of the working tree:

   ```bash
   pip install .
   ```

## Usage

After installation, launch PEtabGUI from the command line using the
`petab_gui` command.

Optionally, you can provide the path to an existing PEtab YAML file
as an argument.

## Features

The PEtabGUI provides a Python-based graphical user interface that simplifies
the creation, editing, and validation of PEtab parameter estimation problems.

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
  - Built-in simulation via [BasiCO](https://github.com/copasi/basico)
    with one-click parameter testing.
  - Intelligent defaults for visualization with optional user customization.
  - Ability to disable plotting for large models to maintain responsiveness.
- **Archiving and Export**
  - Export individual tables, the SBML model, or complete PEtab problems.
  - Save as directory structures or
    [COMBINE archives](https://combinearchive.org) for reproducibility
