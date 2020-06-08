#!/bin/bash

source virtualenv/houston3.7/bin/activate
pip install -e .

invoke app.dependencies.install-python-dependencies
invoke app.dependencies.install-swagger-ui
invoke app.dependencies.install

# Build and deploy frontend
# ./build.frontend.sh

# Build docker image
./build.docker.sh
