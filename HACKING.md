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

This project uses `nose` for finding and executing tests and `coverage` for generating
HTML based coverage reports.

Running the tests can be as easy as:

```sh
$ nosetests
```

However, running the tests is highly configurable and for this project it is easiest
to run a script which makes use of config files under `etc/`.

```sh
$ ./run_tests.sh
```

Check out the coverage reports:

```sh
$ firefox cover/index.html
```
