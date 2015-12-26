#!/usr/bin/env python
from setuptools import setup, find_packages
from readembedability import version

setup(
    name="readembedability",
    version=version,
    description="Extract structured data from unstructured web pages.",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://github.com/bmuller/readembedability",
    packages=find_packages(),
    package_data={ 'readembedability': ['data/*.*', 'requirements.txt'] },
    install_requires=[s.strip() for s in open('requirements.txt', 'r').readlines()]
    )
