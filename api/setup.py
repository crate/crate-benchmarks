#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

requirements = [
    'flask',
    'flask-restful',
    'flask-cors'
]

setup(
    name='benchmark-api',
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    description='Crate Benchmark API',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'app = application:run'
        ]
    }
)
