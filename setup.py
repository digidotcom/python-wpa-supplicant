# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from setuptools import setup, find_packages

install_requires = [
    'txdbus>=1.0.1',
    'click'
]

setup(
    name='wpa_supplicant',
    version='0.1',
    description='WPA Supplicant wrapper for Python',
    author="Stephen Stack",
    author_email="Stephen.Stack@digi.com",
    install_requires=install_requires,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['wpa=wpa_supplicant.cli:run']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Libraries",
        "Operating System :: Linux",
    ],
)
