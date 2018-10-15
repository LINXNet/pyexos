#!/usr/bin/env python
""" Interact with Extreme Networks devices running EXOS """

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    reqs = f.read().strip().split('\n')

version = '0.2'

setup(
    name='pyEXOS',
    version=version,
    py_modules=['pyEXOS'],
    packages=find_packages(),
    install_requires=reqs,
    include_package_data=True,
    description='Python API to interact with network devices running EXOS',
    author='Elisa Jasinska',
    author_email='elisa@bigwaveit.org',
    url='https://github.com/LINXNet/pyexos/',
    download_url='https://github.com/LINXNet/pyexos/tarball/%s' % version,
    keywords=['EXOS', 'Extreme Networks', 'networking'],
    classifiers=[],
)
