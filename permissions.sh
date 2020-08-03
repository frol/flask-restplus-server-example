#!/bin/bash

sudo chown -R $(id -un) $(pwd)/_db/
sudo chgrp -R wildme $(pwd)/_db/
sudo chmod -R 777 $(pwd)/_db/
