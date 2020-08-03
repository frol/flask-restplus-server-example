#!/bin/bash

rm -rf __pycache__
rm -rf _skbuild
rm -rf dist
rm -rf build
rm -rf htmlcov
rm -rf *.egg-info

rm -rf dist.*.tar.gz

rm -rf mb_work
rm -rf wheelhouse

CLEAN_PYTHON='find . -iname __pycache__ -delete && find . -iname *.pyc -delete && find . -iname *.pyo -delete'
bash -c "$CLEAN_PYTHON"
