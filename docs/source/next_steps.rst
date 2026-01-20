==========
Next Steps
==========

Congratulations on completing your PEtab file! Now that you have a standardized parameter estimation problem, you can use various tools to perform parameter estimation, sensitivity analysis, and model simulation. This page provides minimal working examples for the most commonly used tools in the PEtab ecosystem.

.. contents::
   :depth: 2
   :local:

Contribute to the Benchmark Collection
---------------------------------------

Before diving into parameter estimation, consider contributing your PEtab problem to the community! The `PEtab Benchmark Collection <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab>`_ is a curated repository of parameter estimation problems that helps:

* **Validate** your PEtab problem by ensuring it works with multiple tools
* **Enable reproducibility** by providing a permanent reference for your model
* **Facilitate method comparison** by allowing others to test algorithms on your problem
* **Support the community** by expanding the available benchmark suite

**How to contribute:**

You basically create a new GitHub branch and open a pull request. For a complete checklist see the
`pull request template <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab/blob/master/.github/pull_request_template.md>`_.

Parameter Estimation with pyPESTO
----------------------------------

`pyPESTO <https://pypesto.readthedocs.io/>`_ is a Python-based Parameter EStimation TOolbox that provides a unified interface for parameter estimation, uncertainty quantification, and model selection for systems biology models.

**Key features:**

* Multiple optimization algorithms (local and global)
* Multi-start optimization for local optimizers
* Profile likelihood and sampling for uncertainty analysis
* Native PEtab support

**PEtab example notebooks in pyPESTO**

* `Model import using the PEtab format <https://pypesto.readthedocs.io/en/latest/example/petab_import.html>`_ for a basic optimization of a PEtab problem using pyPESTO.
* `AMICI in pyPESTO <https://pypesto.readthedocs.io/en/latest/example/amici.html#Create-a-pyPESTO-problem-+-objective-from-Petab>`_ for a complete workflow of parameter estimation of a PEtab problem using AMICI as simulation engine within pyPESTO.

**Minimal working example:**

.. code-block:: python

   import pypesto
   import pypesto.petab

   # Load PEtab problem
   petab_problem = pypesto.petab.PetabImporter.from_yaml("path_to_your_model.yaml")
   problem = petab_problem.create_problem()

   # Configure optimizer (100 multi-starts)
   optimizer = pypesto.optimize.ScipyOptimizer(method='L-BFGS-B')
   n_starts = 100

   # Run optimization
   result = pypesto.optimize.minimize(
       problem=problem,
       optimizer=optimizer,
       n_starts=n_starts
   )

   # Retrieve best parameters
   best_params = result.optimize_result.list[0]['x']
   print(f"Best parameters: {best_params}")
   print(f"Best objective value: {result.optimize_result.list[0]['fval']}")

**Next steps:**

* Perform profile likelihood: `pypesto.profile <https://pypesto.readthedocs.io/en/latest/api/pypesto.profile.html>`_
* Run sampling for uncertainty: `pypesto.sample <https://pypesto.readthedocs.io/en/latest/api/pypesto.sample.html>`_
* Explore different optimizers and settings in pyPESTO, with many more examples in the `pyPESTO documentation <https://pypesto.readthedocs.io/en/latest/example.html>`_.

**Documentation:** https://pypesto.readthedocs.io/

Model Simulation with AMICI
----------------------------

`AMICI <https://amici.readthedocs.io/>`_ (Advanced Multilanguage Interface to CVODES and IDAS) provides efficient simulation and sensitivity analysis for ordinary differential equation models.

*Disclaimer*: AMICI is currently preparing a release v1.0.0, which will have significant changes to the API. The example below corresponds to the current stable release v0.34.2.

**Key features:**

* C++-based simulation with Python interface
* Fast sensitivity computation via adjoint method
* Symbolic preprocessing for optimized code generation
* Native PEtab support

**Minimal working example:**

.. code-block:: python


   import petab

   from amici import runAmiciSimulation
   from amici.petab.petab_import import import_petab_problem
   from amici.petab.petab_problem import PetabProblem
   from amici.petab.simulations import simulate_petab
   from amici.plotting import plot_state_trajectories

   petab_problem = petab.Problem.from_yaml("path_to_your_model.yaml")
   amici_model = import_petab_problem(petab_problem, verbose=False)
   # Simulate for all conditions
   res = simulate_petab(petab_problem, amici_model)
   # Visualize trajectory of first condition (indexing starts at 0)
   plot_state_trajectories(res["rdatas"][0])

**Next steps:**

* Start to play around with parameters (see `this amici example <https://amici.readthedocs.io/en/v0.34.2/examples/example_petab/petab.html>`_)
* Integrate with pyPESTO for advanced optimization features (see above)

**Documentation:** https://amici.readthedocs.io/

Model Simulation with COPASI
---------------------------------

`COPASI <https://copasi.org/>`_ (COmplex PAthway SImulator) is a standalone software with a graphical user interface for modeling and simulation of biochemical networks.

**Key features:**

* Cross-platform GUI application (Windows, macOS, Linux)
* Advanced simulation possibilities (deterministic, stochastic, steady-state)
* User friendly creation and adaptation of SBML models, e.g. introducing events
* Support for parameter estimation and sensitivity analysis

**Installation:**

Download COPASI for your platform from: https://copasi.org/download/

**Documentation:** https://copasi.org/Support/User_Manual/

Parameter Estimation with PEtab.jl
-----------------------------------

`PEtab.jl <https://sebapersson.github.io/PEtab.jl/stable/>`_ is a Julia library for working with PEtab files, offering high-performance parameter estimation with automatic differentiation.

**Key features:**

* High-performance Julia implementation
* Automatic differentiation for fast gradient computation
* Support for ODE and SDE models
* Native integration with Optimization.jl

**Minimal working example:**

.. code-block:: julia

   using PEtab

   # Import PEtab problem from YAML
   model = PEtabModel("your_model.yaml")

   petab_prob = PEtabODEProblem(model)

   # Parameter estimation
   using Optim, Plots
   x0 = get_startguesses(petab_prob, 1)
   res = calibrate(petab_prob, x0, IPNewton())
   plot(res, petab_prob; linewidth = 2.0)
   # Multistart optimization using 50 starts
   ms_res = calibrate_multistart(petab_prob, IPNewton(), 50)
   plot(ms_res; plot_type=:waterfall)
   plot(ms_res, petab_prob; linewidth = 2.0)

**Next steps:**

* Explore different ODE solvers for your problem type
* Use gradient-based optimizers with automatic differentiation
* Perform uncertainty quantification with sampling methods

**Documentation:** https://sebapersson.github.io/PEtab.jl/stable/

Parameter Estimation with Data2Dynamics
----------------------------------------

`Data2Dynamics (D2D) <https://github.com/Data2Dynamics/d2d>`_ is a MATLAB-based framework for comprehensive modeling of biological processes with focus on ordinary differential equations.

**Key features:**

* MATLAB-based framework with PEtab support
* Profile likelihood-based uncertainty analysis
* Model identifiability analysis
* PEtab import functionality

**Minimal working example:**

.. code-block:: matlab

   % Setup Data2Dynamics environment
   arInit;

   % Import PEtab problem
   arImportPEtab({'my_model','my_observables','my_measurements','my_conditions','my_parameters'}) % note the order of input arguments!

   % Multi-start optimization (100 starts)
   arFitLHS(100);

   % Display results
   arPlotFits;
   arPlot;
   arPrint;

**Documentation:** https://github.com/Data2Dynamics/d2d/wiki

Additional Resources
--------------------

**PEtab Ecosystem:**

* `PEtab Format Specification <https://petab.readthedocs.io/en/latest/v1/documentation_data_format.html>`_ - Complete PEtab documentation
* `PEtab Select <https://petab-select.readthedocs.io/>`_ - Model selection extension

**Model Repositories:**

* `Benchmark Collection <https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab>`_ - Curated PEtab problems
* `BioModels <https://www.ebi.ac.uk/biomodels/>`_ - Database of published SBML models

**Getting Help:**

* PEtab-GUI Issues: https://github.com/PEtab-dev/PEtab-GUI/issues
* PEtab Issues: https://github.com/PEtab-dev/PEtab/issues
* PEtab Discussion: https://github.com/PEtab-dev/PEtab/discussions
* Systems Biology Community: https://groups.google.com/g/sbml-discuss
