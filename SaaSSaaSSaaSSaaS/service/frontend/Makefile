all: main

main:	main.c
	gcc -o $@ $^

debug:	main.c
	gcc -DDEBUG -o $@ $^

.PHONY: clean

clean:
	rm -f main debug
