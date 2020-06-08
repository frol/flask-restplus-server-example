#!/bin/bash

# Install Docker
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
sudo docker run hello-world

# Make wildme group
sudo addgroup wildme
sudo usermod -a -G wildme wildme
sudo usermod -a -G docker wildme

# Make houston folder
sudo mkdir -p /opt/houston
sudo chgrp -R houston /opt/houston
sudo chmod -R g+rwx /opt/houston

# Install utilities
sudo apt-get update
sudo apt install htop git vim tmux ufw

# Install and enable firewall
sudo ufw allow 4422
sudo ufw allow http
sudo ufw allow https
sudo ufw deny ssh
sudo ufw deny 5000
sudo ufw enable

cd /opt/houston
