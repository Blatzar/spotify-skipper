#!/usr/bin/env python3

from setuptools import setup, find_packages
import re
import io
import os

with open('README.md', 'r') as f:
    long_description = f.read()

with io.open('autoskip/__version__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \'(.*?)\'', f.read()).group(1)

setup(
    name='autoskip',
    version=version,
    author='Blatzar',
    author_email='blatzar@gmail.com',
    description='Blacklist artists and songs, no login needed.',
    packages=find_packages(),
    url='https://github.com/Blatzar/spotify-skipper',
    keywords=['spotify', 'skip'],
    install_requires=[
        'colorama',
        'asyncio',
        'argparse',
        'notify-send',
        'pywin32;platform_system == "Windows"',
        'dbus-python;platform_system != "Windows"',
        'dbus_next;platform_system != "Windows"',
    ],
    long_description=long_description,
    long_description_content_type='text/markdown',
    entry_points={
        'console_scripts': ['autoskip=autoskip.cli:main'],
    }
)
