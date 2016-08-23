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
       'lxml==3.6.2',
       'cssselect==0.9.2',
       'readability-lxml==0.6.2',
       'robostrippy==1.1',
       'pyOpenSSL>=16.0.0',
       'beautifulsoup4==4.5.1',
       'nltk==3.2.1',
       'fastimage==1.1.1',
       'pytidylib==0.2.4',
       'debmeo==2.1.1',
       'newspaper3k==0.1.7',
       'python-dateutil==2.5.3',
       'aiohttp==0.22.5'
    ]
)
