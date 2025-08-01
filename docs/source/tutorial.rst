======================
PEtab GUI Tutorial
======================

This tutorial provides a comprehensive guide to using PEtab GUI for creating and managing parameter estimation problems for systems biology models.

.. contents:: Table of Contents
   :depth: 3
   :local:

Introduction
------------

PEtab GUI is a graphical user interface for the `PEtab <https://petab.readthedocs.io/en/latest/>`_ format, which is a standardized way to specify parameter estimation problems in systems biology. This tutorial will guide you through the entire workflow of creating a parameter estimation problem using PEtab GUI.

Getting Started
---------------

Installation
~~~~~~~~~~~~

Before you begin, make sure you have PEtab GUI installed. You can install it by following these steps:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/PaulJonasJost/PEtab_GUI.git

2. Install using pip:

   .. code-block:: bash

      cd PEtab_GUI
      pip install .

Launching the Application
~~~~~~~~~~~~~~~~~~~~~~~~~

To start PEtab GUI, run the following command:

.. code-block:: bash

   petab_gui

If you want to open an existing PEtab project, you can specify the path to the YAML file:

.. code-block:: bash

   petab_gui path/to/your/project.yaml

The Main Interface
------------------

When you first launch PEtab GUI, you'll see the main interface with several tabs:

* **Model**: For creating and editing the SBML model
* **Conditions**: For defining experimental conditions
* **Measurements**: For specifying measurement data
* **Observables**: For defining observable functions
* **Parameters**: For setting up parameters for estimation

Creating a New Model
--------------------

Creating an SBML Model
~~~~~~~~~~~~~~~~~~~~~~

The first step in creating a parameter estimation problem is to define your model. PEtab GUI allows you to:

1. Create a new SBML model from scratch
2. Import an existing SBML model
3. Edit the model using the built-in editor

[Details on how to create and edit models will be filled in later]

Defining Species and Reactions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

[Details on how to define species and reactions will be filled in later]

Setting Up Experimental Conditions
----------------------------------

Creating Condition Tables
~~~~~~~~~~~~~~~~~~~~~~~~~

Experimental conditions define the specific settings under which measurements were taken. To create conditions:

1. Navigate to the "Conditions" tab
2. Add new conditions by specifying:
   * Condition ID
   * Initial concentrations for species
   * Parameter values specific to this condition

[More details on condition setup will be filled in later]

Specifying Measurements
-----------------------

Adding Measurement Data
~~~~~~~~~~~~~~~~~~~~~~~

The "Measurements" tab allows you to:

1. Import measurement data from CSV/TSV files
2. Manually enter measurement data
3. Associate measurements with specific conditions and observables

[Details on measurement specification will be filled in later]

Defining Observables
--------------------

Creating Observable Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Observables define how model outputs are mapped to measured quantities:

1. Navigate to the "Observables" tab
2. Define observable IDs and formulas
3. Specify noise models for each observable

[More details on observable definition will be filled in later]

Setting Up Parameters
---------------------

Parameter Configuration
~~~~~~~~~~~~~~~~~~~~~~~

The "Parameters" tab allows you to:

1. Define parameters for estimation
2. Set parameter bounds and constraints
3. Specify prior distributions (if applicable)

[Details on parameter setup will be filled in later]

Exporting to PEtab Format
-------------------------

Saving Your Project
~~~~~~~~~~~~~~~~~~~

Once you've set up your parameter estimation problem, you can export it to the PEtab format:

1. Go to File > Export > PEtab Format
2. Choose a directory to save the PEtab files
3. The following files will be generated:
   * SBML model file (.xml)
   * Condition file (.tsv)
   * Measurement file (.tsv)
   * Observable file (.tsv)
   * Parameter file (.tsv)
   * YAML configuration file (.yaml)

[Details on export options will be filled in later]

Advanced Features
-----------------

[This section will cover advanced features of PEtab GUI]

Troubleshooting
---------------

Common Issues and Solutions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

[This section will address common problems and their solutions]

Conclusion
----------

This tutorial has covered the complete workflow for creating parameter estimation problems using PEtab GUI. For more information, refer to the [additional resources].

Additional Resources
--------------------

* `PEtab Documentation <https://petab.readthedocs.io/en/latest/>`_
* `Systems Biology Markup Language (SBML) <https://sbml.org/>`_
* `Parameter Estimation in Systems Biology <https://link-to-resource>`_