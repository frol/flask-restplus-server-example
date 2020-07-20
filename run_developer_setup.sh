#!/bin/bash

./clean.sh
python setup.py clean

pip install -r requirements.txt

python setup.py develop

pip install -e .
