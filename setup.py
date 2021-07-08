from distutils.core import setup

_version = '0.1.0'
_packages = ['pylint_forbidden_imports']

_short_description = (
    "pylint-forbidden-imports is a Pylint plugin to restrict what imports are allowed in different modules"
)

_install_requires = [
    'pylint>=1.0',
    'astroid>=1.0',
]

setup(
    name='pylint-forbidden-imports',
    url='https://github.com/pexip/pylint-forbidden-imports',
    author='Pexip AS',
    author_email='packaging@pexip.com',
    description=_short_description,
    version=_version,
    packages=_packages,
    install_requires=_install_requires,
    license='MIT',
    download_url=f"https://github.com/pexip/pylint-forbidden-imports/tarball/{_version}",
    keywords='pylint forbidden import plugin',
    python_requires='>=3.7',
)
