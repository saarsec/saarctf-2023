#!/usr/bin/env bash

set -eux

SERVICENAME=$(cat servicename)
export SERVICENAME

# Build the service - the "service" directory will later be used to install.
# Can be empty if you build everything on the vulnbox. 
# You can remove files here that should never lie on the box.

cd service/
mv turingcode/turingmachine.h static/
sed -i 's|turingcode/turingmachine.h|static/turingmachine.h|' TuringMachineRunner.go
mv testmachine.json static/demo_machine_strlen.json
rm -rf turingcode data *.txt *.json *_test.go turing-machines testtape editor

# Examples:
# cd service && make -j4  # build C binary
# cd service && npm install && npm run build  # use npm to build a frontend
# rm -rf service/.gitignore service/*.iml service/.idea  # remove files that should not be on vulnbox
# rm -rf service/node_modules service/*.log service/data  # remove more things that might occur

