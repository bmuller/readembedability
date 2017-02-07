#!/usr/bin/env python
from setuptools import setup, find_packages
import readembedability

setup(
    name="readembedability",
    version=readembedability.__version__,
    description="Extract structured data from unstructured web pages.",
    author="Brian Muller",
    author_email="bamuller@gmail.com",
    license="MIT",
    url="http://github.com/bmuller/readembedability",
    packages=find_packages(),
    package_data={'readembedability': ['data/*.*']},
    install_requires = [
       'lxml==3.6.4',
       'cssselect==1.0.1',
       'readability-lxml==0.6.2',
       'robostrippy==1.3',
       'pyOpenSSL==16.2.0',
       'beautifulsoup4==4.5.1',
       'nltk==3.2.1',
       'fastimage==1.2.3',
       'pytidylib==0.3.2',
       'newspaper3k==0.1.9',
       'python-dateutil==2.6.0',
       'aiohttp==1.2.0'
    ]
)
