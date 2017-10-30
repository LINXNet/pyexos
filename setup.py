#!/usr/bin/env python
""" Interact with Extreme Networks devices running EXOS """

from setuptools import setup, find_packages
from pip.req import parse_requirements
import uuid

# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=uuid.uuid1())

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

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
