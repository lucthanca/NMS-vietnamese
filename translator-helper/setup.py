"""
Setup script for NMS MXML Translator Helper
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nms-mxml-translator-helper",
    version="0.1.1",
    author="NMS Vietnamese Translation Team",
    description="A GUI tool for managing No Man's Sky MXML localization files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.6.0",
        "lxml>=5.1.0",
    ],
    entry_points={
        "console_scripts": [
            "nms-translator=src.main:main",
        ],
    },
)
