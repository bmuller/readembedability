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
       'lxml==3.8.0',
       'cssselect==1.0.1',
       'readability-lxml==0.6.2',
       'robostrippy==1.3',
       'pyOpenSSL==17.2.0',
       'beautifulsoup4==4.6.0',
       'nltk==3.2.4',
       'fastimage==2.0.0',
       'pytidylib==0.3.2',
       'newspaper3k==0.2.2',
       'python-dateutil==2.6.1',
       'aiohttp==2.2.5'
    ]
)
