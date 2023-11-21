#!/usr/bin/env bash
set -eux

cd data
python3 -u ../init_redis_users.py
cd ..
(sleep 1 ; python3 -u init_redis_http.py) &

# exec redis-server ./redis.conf
exec redis-server ./redis.conf
