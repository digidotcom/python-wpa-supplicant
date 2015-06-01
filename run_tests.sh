#!/usr/bin/env bash

nosetests --config=etc/nose.cfg --with-cov --cov=wpa_supplicant --cov-config=etc/coverage.cfg --cov-report=html
