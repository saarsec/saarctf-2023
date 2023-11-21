#!/usr/bin/env bash

set -eux

SERVICENAME=$(cat servicename)
export SERVICENAME

apt-get update
apt-get install -y uuid-dev

# Build the service - the "service" directory will later be used to install.
# Can be empty if you build everything on the vulnbox. 
# You can remove files here that should never lie on the box.

pushd service/interpreter && make clean && make && find . -type f ! -name main -delete && popd
pushd service/frontend && make clean && make && find . -type f ! -name main -delete && popd
pushd service/compiler && find . -type f ! -name '*.py' ! -name 'saascc' -delete && popd

# Examples:
# cd service && make -j4  # build C binary
# cd service && npm install && npm run build  # use npm to build a frontend
# rm -rf service/.gitignore service/*.iml service/.idea  # remove files that should not be on vulnbox
# rm -rf service/node_modules service/*.log service/data  # remove more things that might occur

