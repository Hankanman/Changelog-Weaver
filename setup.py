""" Setup file for the Auto-Release-Notes package """

from setuptools import setup, find_packages

setup(
    name="AutoReleaseNotes",
    description="A package to generate automatic release notes using llms",
    url="https://github.com/Hankanman/Auto-Release-Notes",
    author="Hankanman",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["defaults.env"],
    },
    install_requires=[
        "aiohttp",
        "pytest",
        "pytest-asyncio",
        "aioresponses",
        "pydantic",
        "python-dotenv",
    ],
    entry_points={
        "console_scripts": [
            "autorelease=main:main",
        ],
    },
)
