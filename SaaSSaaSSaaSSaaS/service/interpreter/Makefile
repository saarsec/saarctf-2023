all: main

main:	main.c
	gcc -s -o $@ $^ -ldl

debug:	main.c
	gcc -DDEBUG -o $@ $^ -ldl

.PHONY: clean

clean:
	rm -f main debug
