#!/usr/bin/env python3
import re

import setuptools
from pathlib import Path
import toml

ROOT_DIR = Path(__file__).parent

# Load pyproject.toml
with ROOT_DIR.joinpath("pyproject.toml").open("r") as pyproject:
    PROJECT = toml.load(pyproject)

METADATA = PROJECT["tool"]["poetry"]
AUTHOR, AUTHOR_EMAIL = METADATA["authors"][0].rsplit(" ", 1)
PACKAGE_DIRS = {p["include"]: p.get("from", ".") + "/" + p["include"] for p in METADATA["packages"]}
CLASSIFIERS = PROJECT["tool"]["poetry"]["classifiers"]

with ROOT_DIR.joinpath(METADATA["readme"]).open("r") as readme:
    README = readme.read()


def _get_dependencies(requirements):
    dependencies = []
    for library, data in requirements.items():
        if library == "python":
            continue

        python_version = None
        if isinstance(data, str):
            version = data
        elif isinstance(data, dict):
            version = data["version"]
            python_version = data.get("python", None)
        else:
            raise NotImplementedError(library, data)

        if version.startswith("^"):
            version = f">={version[1:]}"
        elif re.match(r"\d", version[0]):
            version = f"=={version}"
        dependency = f"{library}{version}"
        if python_version:
            operator, py_version, _ = re.split(r"(\d\.\d)", python_version)
            dependency += f"python_version{operator}'{py_version}'"
        dependencies.append(dependency)
    return dependencies


DEPENDENCIES = _get_dependencies(METADATA["dependencies"])
DEV_DEPENDENCIES = _get_dependencies(METADATA["dev-dependencies"])

setuptools.setup(
    name=METADATA["name"],
    version=METADATA["version"],
    description=METADATA["description"],
    long_description=README,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=METADATA["repository"],
    packages=setuptools.find_packages(where=".", exclude=("*test*", "*tests*")),
    package_dir=PACKAGE_DIRS,
    project_urls=PROJECT["tool"]["poetry"].get("urls", {}),
    python_requires=METADATA["dependencies"]["python"],
    install_requires=DEPENDENCIES,
    extras_require={"dev": DEV_DEPENDENCIES},
    classifiers=CLASSIFIERS,
)
