pylint-forbidden-imports
===============

## About

`pylint-forbidden-imports` is [Pylint](http://pylint.org) plugin for restricting
what imports are allowed in specific module trees.
Want to prevent django from being imported in a flask app? This plugin is for you!

## Usage

Ensure `pylint-forbidden-imports` is installed and on your path, and then run pylint using
pylint-forbidden-imports as a plugin.

```
pip install pylint-forbidden-imports
pylint --load-plugins pylint_forbidden_imports [..your module..]
```

## Configuration

Before the plugin will do anything, it needs configuring.
You can use pylint to generate the default configuration
```
pylint --load-plugins pylint_forbidden_imports --generate-rcfile
```

You will end up with a block similar to below:
```
[FORBIDDEN-IMPORT]
# Colon/semicolon-delimited sets of names that determine what modules are
# allowed to be imported from another module
forbidden-imports=

# Check forbidden imports recursively
forbidden-import-recurse=no
```
### Forbidden Imports
`forbidden-imports` is a csv list of module/forbidden imports. The format is `<module>:<forbidden module>;...`.
For example, the following would prevent `forbidden1` and `forbidden2` from being imported in `module1` and
`forbidden3` and `forbidden4` from being imported in `module2`. 
```
module1:forbidden1;forbidden2,module2:fordibben3;forbidden4
```

### Recursion
You can enable the transitive detection of forbidden imports, however this takes a lot
more compute.

For example, if have the following files:
```py
# flask_app
import flask
import common_utils

# common_utils
import django
```
If `flask_app` is not allowed to import django, the transitive checker would throw an error
because importing `common_utils` would cause `django` to be imported, which is forbidden.