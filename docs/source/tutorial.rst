======================
PEtab GUI Tutorial
======================


This tutorial provides a comprehensive guide to using PEtab GUI for creating and managing parameter estimation problems for systems biology models.

.. contents::
   :depth: 3
   :local:

Introduction
------------

PEtab GUI is a graphical user interface for the `PEtab <https://petab.readthedocs.io/en/latest/>`_ format, which is a standardized way to specify parameter estimation problems in systems biology. This tutorial will guide you through the entire workflow of creating a parameter estimation problem using PEtab GUI.

Getting Started
---------------

Installation
~~~~~~~~~~~~

Before you begin, make sure you have PEtab GUI installed. You can install it directly from PyPI using pip:

.. code-block:: bash

   pip install petab-gui

Alternatively, you can install it from the GitHub repository by following these steps:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/PEtab-dev/PEtabGUI.git

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

When you first launch **PEtab GUI**, you'll see the main interface as shown below:

.. figure:: _static/Table_View_withInfo.pdf
   :alt: PEtab GUI Main Interface
   :width: 100%
   :align: center

   **PEtab GUI Main Interface**: (1) Every Table is in its own a dockable panel. Using the buttons in (2) you can get each widget as a separate window or close it entirely. To reopen it, use the `View` menu in the menu bar.
   (3) The info widget shows log messages and clickable documentation links. Here you will be informed about deleted lines, potential formatting problems and more. (4) The toolbar provides quick access to common actions
   like file open/save, table modification, and model simulation. (5) The filter allows you to only look at specific rows. The filterbuttons to the right let you select in which tables the filter should be applied.
   (6) If you are unsure what to do, you can enter the **Tutorial Mode** by clicking the question mark icon in the toolbar. This wil allow you to click different widgets or columns in the tables to get more information about their purpose.

The interface is organized into several key areas:

- **Menu Bar**:
  At the top, providing access to `File`, `Edit`, `View`, and `Help`. These items allow you to edit your petab problem and navigate the application. Most notably, the `View` menu allows you to toggle the visibility of the different panels.

- **Toolbar**:
  Below the menu bar, offering quick access to common actions like file open/save, table modification, and model simulation.

- **Main Interface**:

  The main interface of the application can be categorized into two main sections that can be selected via the tab navigation:

  - **Data Tables** (left tab):
    Six dockable table panels, each corresponding to a PEtab table (see also the `PEtab Documentation`_):

    * **Measurement Table**: Define experimental observations
      → See: :ref:`measurement-table`
    * **Observable Table**: Specify the formulas and noise models
      → See: :ref:`observable-table`
    * **Visualization Table**: Assign plotting preferences
      → See: :ref:`visualization-table`
    * **Parameter Table**: Set parameter IDs, bounds, and scales
      → See: :ref:`parameter-table`
    * **Condition Table**: Describe experimental conditions
      → See: :ref:`condition-table`
    * **Info Panel**: Displays log messages and clickable documentation links
    * **Measurement Plot Panel**:
      At the bottom, visualizes the measurement data based on your current model.
      → See: :ref:`visualization-table`

  - **SBML Model** (right tab):
    A built-in editor for creating and editing SBML models. It is split into two synced editors:

    * **SBML Model Editor**: For editing the SBML model directly.
    * **Antimony Editor**: For editing the Antimony representation of the model.

    Changes in these can be forwarded to the other editor, allowing you to work in your preferred format.
    → See: :ref:`sbml-editor`

  .. figure:: _static/SBML_Antimony_Editors.pdf
    :alt: SBML and Antimony Editors
    :width: 100%
    :align: center

    **SBML and Antimony Editors**: The second tab of the GUI application. The SBML editor (1) allows you to edit the SBML model directly, while the Antimony editor (2) provides a more human-readable format. Changes in one editor can be forwarded to the other using the buttons below them.

We can can now start creating a new PEtab problem or edit an existing one. The following sections will guide you through the process of defining and editing your model, experimental conditions, measurements, observables, and parameters.
While at each step we will learn about the different panels and how to fill the corresponding tables, it might be helpful to have a look at the `PEtab Documentation`_ to get a better understanding of the PEtab format and its requirements.

Opening an Existing PEtab Problem
----------------------------------

If you already have a PEtab problem defined in a YAML file or you have your SBML model already, you can open them directly in PEtab GUI:

1. Through the menu bar, go to **File > Open**. This will open a file dialog, where you can select your YAML file, SBML model file, or any other PEtab-related files.
2. Alternatively, you can drag and drop your YAML file onto the PEtab GUI window. The application will automatically handle the file and load the relevant data into the interface.
3. If you want to continue working on an existing PEtab problem, you can also use the **File > Recent Files** menu to quickly access recently opened projects.

Creating/Editing a PEtab Problem
--------------------------------

Since a PEtab problem consists of several components, we will go through the process step by step. The following sections will guide you through creating or editing a PEtab problem using the PEtab GUI.
While there is no strict order in which you have to fill the tables, we will follow a logical sequence that starts with the model definition, followed by measurements, experimental conditions, observables, and parameters.


.. _sbml-editor:

Creating/Editing an SBML Model
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usually the first step in creating a PEtab problem is to define the underlying SBML model.
Independent of whether you are creating a new model or editing an existing one, you are given the choice between editing
the model directly in `SBML <https://sbml.org>`_ or in the much more readable
`Antimony <https://github.com/sys-bio/antimony/blob/develop/doc/AntimonyTutorial.md>`_ and then converting it to SBML.

.. dropdown:: 💡 Need help understanding what an SBML model is?
  -- ask chatgpt --

If you are creating a new model, the empty antimony template might help in getting started. Here is a simple example showcasing how species, reactions, and parameters can be defined:
.. code-block::

   model *ExampleModel
     // Reakcions
     J0: S1 -> S2 + S3; k1*S1 # Mass-action kinetics
     J1: S2 -> S3 + S4; k2*S2
     // Species initialization
     S1 = 10 # The initial concentration of S1
     S2 = 0  # The initial concentration of S3
     S3 = 3  # The initial concentration of S3
     S4 = 0  # The initial concentration of S4
     // Variable initialization
     k1 = 0.1 # The value of the kinetic parameter from J0.
     k2 = 0.2 # The value of the kinetic parameter from J1.
   end


.. _measurement-table:

Specifying Measurements
~~~~~~~~~~~~~~~~~~~~~~~

Indispensable for parameter estimation problems are the measurements that will be used to fit the model parameters.
In PEtab GUI, you can define these measurements in the **Measurement Table**.
While it is possible to create a new measurement table from scratch, it is usually more convenient to import an already
existing measurement file. In our experience, most measurements exist in some matrix format. Time data might have each
row corresponding to a time point and each column corresponding to a different observable.
Similar can Dose-Response data be structured, where each row corresponds to a different dose.
Accounting for these common formats, PEtab GUI handles opening a CSV or TSV file by checking whether it is a time series,
dose-response, or a PEtab measurement file. Simply drag and drop your file into the **Measurement Table** or
use the **File > Open** option. In general what we need to specify in the measurement table are:

1. **observableID**: A unique identifier for the observable that this measurement corresponds to. This should match the observable IDs defined in the **Observable Table**.
2. **simulationConditionId**: The condition under which the measurement was taken. You are free to choose a name but it should be consistent with the conditions defined in the **Condition Table**.
3. **time** and **measurement**: The time point and corresponding measurements.

There are a number of optional columns that can be specified, for more details see the `PEtab Documentation`_.


.. _observable-table:

Defining Observables
~~~~~~~~~~~~~~~~~~~~

Observables define how model species are mapped to measured quantities. When you create a measurement in the
**Measurement Table**, you need to specify which observable it corresponds to. If it is not already defined, PEtab GUI
will automatically create a new observable entry in the **Observable Table**. You will only have to fill out the actual
function in the **observableFormula** column, which defines how the observable is calculated from the model species. In
the easiest cae, this just corresponds to the species ID, e.g. `S1`. But it could also be a more function like
`k_scale * (S1 + S2)`, that even introduce new parameters, e.g. `k_scale`.

In general we assume that the measurement is subject to some noise. Per default the noise is normally distributed and
within the `noiseFormula` column you can specify the standard deviation of the noise. Again, this formula can be a
simple number or a more complex formula introducing new parameters.

For more details on e.g. how to change the noise model, see the `PEtab Documentation`_.


.. _condition-table:

Setting Up Experimental Conditions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Experimental conditions define the specific settings under which measurements were taken. Aside from the conditionID column,
all other columns are optional. The other columsn may either be a specific parameter value that has differen values across the conditions
or an initial value for a species that is different across conditions (e.g. in case of a dose-response experiment).
Just as in the observable table, new conditions can be created automatically when you create a new measurement in the **Measurement Table**.


.. _parameter-table:

Setting Up Parameters
~~~~~~~~~~~~~~~~~~~~~

The last thing you will want to fill out is the **Parameter Table**. This table defines the parameters that
are part of the estimation problem. This includes parameters from the SBML model, observables, and noise models.
For every parameter you declare in the `estimate` column whether it should be estimated during the parameter estimation or not.
Additionally you specify maximum and minimum bounds for the parameter values in the `upperBound` and `lowerBound` columns, respectively.
If your parameter is not to be estimated, you need to specify a `nominalValue`. PEtab GUI aids you in this process by suggesting
parameter names from the sbml model you might want to add here.


.. _visualization-table:

Validation and Inspection
-------------------------

Once you have filled out all the tables, it is important to validate your PEtab problem to avoid errors during parameter estimation.
PEtab GUI supports this through **Visualization and Simulation** and **Linting** features:

  .. figure:: _static/Table_View_PlotView.pdf
   :alt: SBML and Antimony Editors
   :width: 100%
   :align: center

   **PEtab GUI with Visualization and Simulation Panels**: Once you have defined measurements, you can add the **Measurement Plot** to visualize your measurements. You can also add the **Simulation Table** and **Visualization Table** to run simulations and visualize the results.
   (1) The three tables can be neatly arranged next to each other. (2) Within the measurement panel, you can click on different plots. If you have specified multiple plots, *All Plots* will show every plot specified, followed by tabs for each individual plot.
   If you have simulations you additionally get a residual plot and a scatterplot of the fit. Through the settings symbol (3) you can change whether you want to plot by observable, condition or defined by the visualization table.


Visualization and Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the **Measurement Plot** panel, you will see a visualization of your measurements. You can click on single points in the
measurement plot to see the corresponding measurement in the **Measurement Table** and vice versa. This can already help getting an
idea of the dynamics of your model and spot potential outliers in your measurements.

Once you have defined all the necessary components, you might want to see whether a specific parameter set leads to a good fit of the model to the measurements.
For this you can add two panels to the main interface, the **Simulation Table** and the **Visualization Table**.
The **Simulation Tabel** panel is strictly speaking not part of the PEtab problem definition.
Structurally it is the same as the **Measurement Plot** panel, with the sole differen that the column `measurement`
is replaced by `simulation`.
The **Visualization Table** allows you to specify how the measurements (and simulations) should be visualized. In short:

* every plotId corresponds to a specific plot. Rows that have the same plotId will be plotted together.
* You specify your `xValues` and `yValues` for each row.
* You can specify additional details, such as offsets and scale. For more details see the `PEtab Documentation`_.

If you dont have simulations yet, you can run a Simulation through the toolbar button, which will automatically fill the **Simulation Table**,
running a simulation with the current parameter values and conditions.

If you have simulations, additional plots can be viewed, such as residual plots, as well as goodness-of-fit plots.

Linting
~~~~~~~

Linting is the process of automatically checking your tables for structural and logical errors during editing.

PEtab GUI offers two layers of linting support:

- **Partial Linting on Edit**:
  Whenever you modify a single row in any table, PEtab GUI will **immediately lint that row** in context.
  This allows you to catch errors as you build your PEtab problem — such as missing required fields, mismatched IDs, invalid references, or inconsistent units.

- **Full Model Linting**:
  You can run a complete validation of your PEtab problem by clicking the **lint** icon in the toolbar.
  This performs a full consistency check across all tables and provides more comprehensive diagnostics.

All linting messages — including errors and warnings — appear in the **Info** panel at the bottom right of the interface.
Messages include timestamps, color coding (e.g., red for errors, orange for warnings), and sometimes clickable references or hints.

By using linting early and often, you can avoid many common errors in PEtab model definition and ensure compatibility with downstream tools.


Saving Your Project
-------------------

Once you've set up your parameter estimation problem, and sufficiently validated it, you can save your project. This
can be done either as a compressed ZIP file or as a COMBINE archive. You can also save each table as a separate CSV file.

Additional Resources
--------------------

* `PEtab Documentation`_
* `Systems Biology Markup Language (SBML) <https://sbml.org/>`_

.. _PEtab documentation: https://petab.readthedocs.io/en/latest
