CFLAGS=-g -O1 -Wall -std=gnu99 -fPIC

all: modhttp.so

modhttp.so: redismodule.h modhttp.c
	gcc ${CFLAGS} -shared -g modhttp.c -o modhttp.so

redismodule.h:
	wget "https://raw.githubusercontent.com/redis/redis/7.0/src/redismodule.h"

clean:
	rm -f *.so *.o
