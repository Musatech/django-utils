#!/usr/bin/env python
from io import open

from setuptools import find_packages, setup

from src import __version__

setup(
    name='musa-django-utils',
    version=__version__,
    description='Musa Django Utils',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Shinneider Libanio da Silva',
    author_email='shinneider@musa.co',
    url='https://github.com/Musatech/django-utils',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=[
        'django',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)