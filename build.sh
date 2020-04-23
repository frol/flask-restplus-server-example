#!/usr/bin/env bash

# docker build --no-cache --tag wildme/houston:latest .
source virtualenv/houston3.7/bin/activate
pip install -e .

# Build and deploy frontend
# ./build.frontend.sh

# Build docker image
# ./build.docker.sh
