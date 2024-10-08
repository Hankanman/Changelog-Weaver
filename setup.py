""" Setup file for the Changelog-Weaver package """

from setuptools import setup, find_namespace_packages

NAME = "changelog-weaver"
VERSION = "1.0.0"

setup(
    name=NAME,
    description="A package to generate automatic release notes using llms",
    url="https://github.com/Hankanman/Changelog-Weaver",
    author="Hankanman",
    version=VERSION,
    packages=find_namespace_packages(),
    include_package_data=True,
    package_data={
        "": ["defaults.env"],
    },
)
