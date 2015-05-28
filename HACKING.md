Developer's Guide
=================

Welcome to the developer's guide for the Python wpa_supplicant library.

Setup Development Environment
-----------------------------

Use `virtualenv` to create a Python 2 and/or 3 environment.

```sh
$ virtualenv -p /usr/bin/python2 env2
$ virtualenv -p /usr/bin/python3 env3
```

Activate one of the environments.

```sh
$ source env2/bin/activate
```

Then, install the development dependencies.

```sh
(env2) $ pip install -r dev-requirements.txt
```


Running tests
-------------

Run the tests to make sure everything is in order.

```sh
$ nosetests wpa_supplicant/test
```
