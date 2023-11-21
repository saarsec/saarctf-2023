CFLAGS=-g -O1 -Wall -std=gnu99 -fPIC


all: modhttp.so

modhttp.so: redismodule.h modhttp.c
	gcc ${CFLAGS} -shared -g modhttp.c -o modhttp.so

redismodule.h:
	wget "https://raw.githubusercontent.com/redis/redis/7.0/src/redismodule.h"

redis: redis-7.0.11
	$(MAKE) -C redis-7.0.11 -j$(nproc) redis-server MALLOC=libc

redis-7.0.11:
	wget "https://download.redis.io/releases/redis-7.0.11.tar.gz"
	tar -xf redis-7.0.11.tar.gz

clean:
	rm -f *.so *.o
