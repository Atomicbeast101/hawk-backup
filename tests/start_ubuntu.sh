#!/bin/bash

# Setup SSH access
apt-get update && apt-get install -y openssh-server
mkdir -p /var/run/sshd
echo 'root:1234' | chpasswd
sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Run indefinitely
echo 'Test SSH server ready!'
/usr/sbin/sshd -D
