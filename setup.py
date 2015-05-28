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
