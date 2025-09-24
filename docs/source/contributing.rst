Contributing
============

We welcome contributions from the community!
Whether you are reporting or fixing a bug, implementing a new feature,
or improving the documentation, your contribution is appreciated.

Development Setup
-----------------

To set up a development environment, follow these steps:

1. Fork the repository on GitHub and clone your fork locally
2. Create a virtual environment and activate it
3. Install `pre-commit <https://pre-commit.com/>`_ to manage git hooks

   .. code-block:: bash

      pip install pre-commit
      pre-commit install

4. Install the package in editable mode along with development dependencies
5. Implement your changes in a new branch
6. Commit your changes with clear messages
7. Push your branch to your fork and open a pull request against the main repository
8. Ensure all tests pass and request a review


Building the documentation
--------------------------

After setting up the development environment, you can build the documentation locally:

.. code-block:: bash

   pip install tox  # only the first time
   tox -e doc
   # The built documentation will be in `docs/build/html/index.html`


Filing an Issue
----------------

If you encounter any bugs or have feature requests, please file an issue on GitHub.
`Open a new issue <https://github.com/PEtab-dev/PEtabGUI/issues/new/choose>`__.

When filing an issue, provide as much detail as possible,
including steps to reproduce the issue, expected behavior, and any relevant logs or screenshots.
