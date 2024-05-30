""" Setup file for the Auto-Release-Notes package """

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="Auto-Release-Notes",
    version="0.1.0",
    description="A package to generate automatic release notes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Seb Burrell",
    author_email="sebburrell@outlook.com",
    url="https://github.com/Hankanman/Auto-Release-Notes",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "python-dotenv",
    ],
    classifiers=[
        "Development Status :: 1",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "auto-release-notes=auto_release_notes.main:main",
        ],
    },
)
