#!/bin/bash

mkdir -p virtualenv
python3 -m venv ./virtualenv/houston3.7

# source virtualenv/houston3.7/bin/activate

echo '''To get the deployment scripts to work, you need to add a new alias in .ssh/config:

Host houston
HostName kaiju.dyn.wildme.io
User <username>
Port 2222
IdentityFile ~/.ssh/<private_key_file>
'''
