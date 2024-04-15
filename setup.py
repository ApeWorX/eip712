#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

extras_require = {
    "test": [  # `test` GitHub Action jobs uses this
        "pytest>=6.0,<8",  # Core testing package
        "pytest-xdist",  # multi-process runner
        "pytest-cov",  # Coverage analyzer plugin
        "hypothesis>=6.70.0,<7",  # Strategy-based fuzzer
    ],
    "lint": [
        "black>=23.12.0,<24",  # auto-formatter and linter
        "mypy>=1.7.1,<2",  # Static type analyzer
        "types-setuptools",  # Needed for mypy type shed
        "flake8>=6.1.0,<7",  # Style linter
        "isort>=5.12.0,<6",  # Import sorting linter
        "mdformat>=0.7.17,<0.8",  # Auto-formatter for markdown
        "mdformat-gfm>=0.3.5,<0.4",  # Needed for formatting GitHub-flavored markdown
        "mdformat-frontmatter>=0.4.1,<0.5",  # Needed for headers in GH issue templates
    ],
    "release": [  # `release` GitHub Action job uses this
        "setuptools",  # Installation tool
        "wheel",  # Packaging tool
        "twine",  # Package upload tool
    ],
    "doc": [
        "myst-parser>=0.18.1,<0.19",  # Tools for parsing markdown files in the docs
        "Sphinx>=5.3.0,<6",  # Documentation generator
        "sphinx_rtd_theme>=1.2.0,<2",  # Readthedocs.org theme
        "sphinxcontrib-napoleon>=0.7",  # Allow Google-style documentation
    ],
    "dev": [
        "commitizen>=2.42,<3",  # Manage commits and publishing releases
        "pre-commit",  # Ensure that linters are run prior to committing
        "pytest-watch",  # `ptw` test watcher/runner
        "IPython",  # Console for interacting
        "ipdb",  # Debugger (Must use `export PYTHONBREAKPOINT=ipdb.set_trace`)
    ],
}

# NOTE: `pip install -e .[dev]` to install package
extras_require["dev"] = (
    extras_require["test"]
    + extras_require["lint"]
    + extras_require["doc"]
    + extras_require["release"]
    + extras_require["dev"]
)

with open("./README.md") as readme:
    long_description = readme.read()


setup(
    name="eip712",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="eip712: Message classes for typed structured data hashing and signing in Ethereum",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ApeWorX Ltd.",
    author_email="admin@apeworx.io",
    url="https://github.com/ApeWorX/eip712",
    include_package_data=True,
    install_requires=[
        "dataclassy>=0.8.2,<1",
        "eth-abi>=5.1.0,<6",
        "eth-account>=0.10.0,<0.11",
        "eth-hash[pycryptodome]",  # NOTE: Pinned by eth-abi
        "eth-typing>=3.5.2,<4",
        "eth-utils>=2.3.1,<3",
        "hexbytes>=0.3.0,<1",
    ],
    python_requires=">=3.8,<4",
    extras_require=extras_require,
    py_modules=["eip712"],
    license="Apache-2.0",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"eip712": ["py.typed"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
