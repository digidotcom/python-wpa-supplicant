.. python-wpa-supplicant documentation master file, created by
   sphinx-quickstart on Wed Jun  3 14:30:47 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to python-wpa-supplicant's documentation!
=================================================

This library provides an interface to the wpa_supplicant D-Bus interface.  As of now,
there is really no good option for interfacing with wpa_supplicant from Python and
to go a step further, the existing D-Bus libraries are difficult to work with.  This
library abstracts all of that away into a very clean API based on the
`wpa_supplicant D-Bus documentation <http://w1.fi/wpa_supplicant/devel/dbus.html>`_

In addition to the Python library, this package also includes a wpa_supplicant CLI tool
which provides access to the entire library via command line!


Documentation Contents
----------------------

The main documentation seeks to provide a broad overview showing how to use
the library and CLI at a high level but without going into all the minute
details.

.. toctree::
   :maxdepth: 2

   usage_cli
   usage_library
   tips_and_tricks

API Reference
-------------

The API reference includes automatically generated documentation
that covers the details of individual classes, methods, and
members.

.. toctree::
   :maxdepth: 2

   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

