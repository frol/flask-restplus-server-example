#!/bin/bash

git checkout next
git pull
./build.docker.sh
./run.sh
