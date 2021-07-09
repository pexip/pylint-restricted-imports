pylint-restricted-imports
=========================

About
`````

``pylint-restricted-imports`` is `Pylint`_ plugin for restricting
what imports are allowed in specific module trees.
Want to prevent django from being imported in a flask app? This plugin is for you!

.. _Pylint: http://pylint.org

Usage
`````

Ensure ``pylint-restricted-imports`` is installed and on your path, and then run pylint using
pylint-restricted-imports as a plugin::

    pip install pylint-restricted-imports
    pylint --load-plugins pylint_restricted_imports [..your module..]

Configuration
`````````````

Before the plugin will do anything, it needs configuring.
You can use pylint to generate the default configuration::

    pylint --load-plugins pylint_restricted_imports --generate-rcfile

You will end up with a block similar to below::

    [RESTRICTED-IMPORT]
    # Colon/semicolon-delimited sets of names that determine what modules are
    # allowed to be imported from another module
    restricted-imports=

    # Check restricted imports recursively
    restricted-import-recurse=no

Restricted Imports
''''''''''''''''''
``restricted-imports`` is a csv list of module/restricted imports. The format is ``<module>:<restricted module>;...``.
For example, the following would prevent ``restricted1`` and ``restricted2`` from being imported in `module1` and
``restricted3`` and ``restricted4`` from being imported in ``module2``::

    module1:restricted1;restricted2,module2:fordibben3;restricted4

Recursion
'''''''''
You can enable the transitive detection of restricted imports, however this takes a lot
more compute.

For example, if have the following files::

    # flask_app.py
    import flask
    import common_utils

    # common_utils.py
    import django

If ``flask_app`` is not allowed to import django, the transitive checker would throw an error
because importing ``common_utils`` would cause ``django`` to be imported, which is restricted.
