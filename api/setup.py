# vi: set fileencoding=utf-8
# -*- coding: utf-8; -*-

from setuptools import setup, find_packages

requirements = [
    'flask==0.10.1',
    'flask-restful==0.3.5',
    'flask-cors==3.0.0',
    'crate==0.16.3',
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
            'bench-api = crate.benchapi.cli:main',
        ]
    }
)
