# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from setuptools import setup, find_packages


setup(
    name='wpa_supplicant',
    version='0.1',
    description='WPA Supplicant wrapper for Python',
    author="Stephen Stack",
    author_email="Stephen.Stack@digi.com",
    install_requires=open('requirements.txt').read().split(),
    packages=find_packages(),
    entry_points={
        'console_scripts': ['wpa=wpa_supplicant.cli:run']
    },
)
