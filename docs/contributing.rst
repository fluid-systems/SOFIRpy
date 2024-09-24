.. _contributing:

Contribute
==========

Reporting Bug
-------------

If you find a bug, please create an issue on GitHub with the following details:

- Summarize the bug encountered concisely
- Expected behavior vs. actual behavior
- How one can reproduce the issue
- Your environment (OS, Python version, dependencies)
- Relevant logs and/or screenshots

Feature Requests
----------------

We welcome new ideas! To suggest a feature:

- Open a GitHub issue
- Add a clear and concise description of what the problem is.
- Describe the solution you'd like
- Add any other context or screenshots about the feature request


Contributing
------------

Software developers, whether part of the core team or external contributors, are
expected to adhere to best practices for documenting and testing new code. Those
interested in contributing should fork the repository and submit a pull request via
GitHub. Pull requests can be made to the development branch only. All pull requests
will be reviewed by the core development team.

Setting up the project locally:

1. Fork the repository

2. Clone the repository

.. code-block:: bash

   git clone https://github.com/<yourusername>/sofirpy.git


3. Navigate to the project directory

.. code-block:: bash

   cd sofirpy

4. Set up a virtual environment

.. code-block:: bash

   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

5. Install dependencies

.. code-block:: bash

   python -m pip install -U pip
   python -m pip install -e ".[test, doc, dev]"

6. Install ``pre-commit`` hooks

.. code-block:: bash

   pre-commit install


Use PEP 8 as a general guide for Python code. Ensure that all functions and classes are
documented with clear docstrings.

Format and lint your code using ruff.

.. code-block:: bash

   ruff check src/
   ruff format src/


Write tests for any new functionality and ensure that existing tests pass.

.. code-block:: bash

   pytest
