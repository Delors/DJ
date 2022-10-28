#!/usr/bin/bash

# Runs all tests.

python3 -m unittest discover -s operations -p "*test.py"
