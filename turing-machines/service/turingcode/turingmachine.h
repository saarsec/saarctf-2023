#include <cstdlib>
#include <cstdint>
#include <cstring>
#include <unistd.h>
#include <iostream>

class TuringMachine {
public:
	uint8_t *tapeStart;
	uint8_t *tapeEnd;
	uint8_t *head;
	int state = 0;

	uint8_t registers[16] = {0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};

	inline TuringMachine(uint8_t *tapeStart, uint8_t *tapeEnd) : tapeStart(tapeStart), tapeEnd(tapeEnd), head(tapeStart) {}

	virtual bool run(int steps) = 0;

	virtual const char* stateName(int state) = 0;
};

class FinalStateReporter {
	FILE *f;
public:
	explicit FinalStateReporter(FILE *f) : f(f) {}

	~FinalStateReporter() {
		fclose(f);
	}

	void reportFinalState(int state, const char *stateName) {
		fprintf(f, "Final state: '%s' (%d)\n", stateName, state);
	}

	void reportFinalTape(uint8_t *tape, size_t len) {
		fprintf(f, "Final tape (%lu bytes):\n", len);
		for (size_t i = 0; i < len; i++) {
		    fprintf(f, i % 16 == 15 ? "%02hhx\n" : (i % 8 == 7 ? "%02hhx  " : "%02hhx "), tape[i]);
		}
		fputs("\n", f);
	}
};

uint8_t *operator ""_tape(const char *s, size_t len) {
	auto *tape = (uint8_t *) malloc(len);
	memmove(tape, s, len);
	return tape;
}

static void hexview(const uint8_t *ptr, int len) {
	for (int i = 0; i < len; i++) {
		if (i % 16 == 0) printf("%p  ", ptr + i);
		printf("%02hhx ", ptr[i]);
		if (i % 16 == 7) printf(" ");
		if (i % 16 == 15) printf("\n");
	}
	if (len % 16 != 0) printf("\n");
}
