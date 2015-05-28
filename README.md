Python wpa_supplicant Library
=============================

Motivation
----------

This library is an implementation of the wpa_supplicant D-Bus interface.  As of now,
there is really no good option for interfacing with wpa_supplicant from Python and
to go a step further, the existing D-Bus libraries are difficult to work with.  This
library abstracts all of that away into a very clean API based on [wpa_supplicant
D-Bus documentation](http://w1.fi/wpa_supplicant/devel/dbus.html).


Overview
--------

This library is more than just a library that can be used programmatically, it also
serves as a command-line tool for easily using wpa_supplicant and exercising the library.


Installation
------------

```sh
$ pip install wpa_supplicant
```