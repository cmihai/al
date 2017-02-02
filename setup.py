#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
   name='alkuhl',
   version='0.1.0',
   description='A toolkit for cleaning up Alembic migrations',
   author='Mihai Ciumeica',
   author_email='cmihai@gmail.com',
   packages=find_packages(),
   install_requires=[
       'click',
       'alembic',
   ],
   entry_points={
       'console_scripts': ['al=alkuhl.command_line:main'],
   },
)
