# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

from setuptools import setup, find_packages
import os

install_requires = [
    'txdbus>=1.0.1',
    'click',
    'six',
]


def get_long_description():
    long_description = open('README.md').read()
    try:
        import subprocess
        import pandoc

        process = subprocess.Popen(
            ['which pandoc'],
            shell=True,
            stdout=subprocess.PIPE,
            universal_newlines=True)

        pandoc_path = process.communicate()[0]
        pandoc_path = pandoc_path.strip('\n')

        pandoc.core.PANDOC_PATH = pandoc_path

        doc = pandoc.Document()
        doc.markdown = long_description
        long_description = doc.rst
        open("README.rst", "w").write(doc.rst)
    except:
        if os.path.exists("README.rst"):
            long_description = open("README.rst").read()
        else:
            print("Could not find pandoc or convert properly")
            print("  make sure you have pandoc (system) and pyandoc (python module) installed")

    return long_description


setup(
    name='wpa_supplicant',
    version='0.2',
    description='WPA Supplicant wrapper for Python',
    long_description=get_long_description(),
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
        "Operating System :: POSIX :: Linux",
    ],
)
