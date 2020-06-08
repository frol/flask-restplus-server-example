#!/bin/bash

./build.sh
./host.export.sh
ssh houston '/opt/houston/host.run.sh'
./host.monitor.sh
