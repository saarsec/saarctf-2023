#!/usr/bin/env bash

set -eux

SERVICENAME=$(cat servicename)
export SERVICENAME

rm -f service/redisbbq-frontend

# Build the service - the "service" directory will later be used to install.
# Can be empty if you build everything on the vulnbox.
# You can remove files here that should never lie on the box.
cd service/redis-frontend
npm install
npm run build-production
cd ..

rm -rf redis-frontend redis-6.* redis-7.* *.acl *.aof *.rdb .gitignore *.so .gdb_history redismodule.h *.tar.gz admin-password.txt data appendonly*
cp dist/* ./
rm -rf dist
sed -i 's|12345|16379|' init_redis_http.py
sed -i 's|admin-password.txt|data/admin-password.txt|' init_redis_http.py

# Examples:
# cd service && make -j4  # build C binary
# cd service && npm install && npm run build  # use npm to build a frontend
# rm -rf service/.gitignore service/*.iml service/.idea  # remove files that should not be on vulnbox
# rm -rf service/node_modules service/*.log service/data  # remove more things that might occur

