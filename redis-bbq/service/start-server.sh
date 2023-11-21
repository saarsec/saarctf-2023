#!/usr/bin/env bash
set -eux

make
ls -lh modhttp.so

python3 init_redis_users.py
(sleep 1 ; python3 -u init_redis_http.py) &

# exec redis-server ./redis.conf
exec redis-7.0.11/src/redis-server ./redis.conf
