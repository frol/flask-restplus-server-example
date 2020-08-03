#!/bin/bash

./build.sh
./host.export.sh
ssh -t houston '/opt/houston/host.run.sh'
./host.monitor.sh
