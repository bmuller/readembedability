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
    package_data = { 'readembedability': ['data/*.txt'] },
    install_requires=['twisted>=14.0', 'cssselect==0.9.1', 'readability-lxml==0.3.0.2', 'robostrippy==0.13', 'pyOpenSSL>=0.14',
                      'beautifulsoup4==4.3.2', 'debmeo==1.4', 'nltk==3.0.2', 'fastimage==0.2.1', 'goose-extractor==1.0.17',
                      'python-dateutil==2.4.2', 'treq>=15.0', 'pytidylib==0.2.4']
    )
