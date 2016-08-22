# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

from setuptools import setup, find_packages

requirements = [
    'flask',
    'flask-restful',
    'flask-cors',
    'crate',
    'toml',
]

setup(
    name='benchmark-api',
    version='0.1.0',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    description='Crate Benchmark API',
    install_requires=requirements,
    namespace_packages=['crate'],
    entry_points={
        'console_scripts': [
            'app = crate.benchapi.cli:run'
        ]
    }
)
