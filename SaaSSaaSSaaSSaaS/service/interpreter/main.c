#ifndef _GNU_SOURCE
#define _GNU_SOURCE /* for RTLD_DEFAULT */
#endif

#include<stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <dlfcn.h>


#define MAGIC (0x52414153)
#define MAX_INS (1000000)
#define STACK_SIZE (64*1000)
#define STR_TAG (1<<31)
#define MAX_ARGS (3)

#ifdef DEBUG
	#define debug printf
#else
	#define debug //debug
#endif

enum opcodes{
	OP_PUSH_INT = 0x01,
	OP_PUSH_STR = 0x02,
	OP_ADD = 0x10,
	OP_SUB = 0x11,
	OP_MUL = 0x12,
	OP_DIV = 0x13,
	OP_AND = 0x14,
	OP_OR = 0x15,
	OP_XOR = 0x16,
	OP_NOT = 0x17,
	OP_EQ = 0x20,
	OP_LT = 0x21,
	OP_DUP = 0x30,
	OP_SWAP = 0x31,
	OP_POP = 0x32,
	OP_JMP = 0x40,
	OP_JMPI = 0x41,
	OP_SYSCALL = 0x42,
};

typedef union argument {
	uint32_t arg_i;
	char* arg_s;
} argument;

typedef int fn_0();
typedef int fn_1(argument arg0);
typedef int fn_2(argument arg0, argument arg1);
typedef int fn_3(argument arg0, argument arg1, argument arg2);

typedef struct interpreter {
	unsigned char* code;
	size_t code_length;
	unsigned char* stack;
	unsigned int IP;
	unsigned int SP;
} interpreter;


void push_int(interpreter* interp, uint32_t val){
	interp->SP -= 4;
	*(uint32_t*)&interp->stack[interp->SP] = val;
}

int raw_is_str(interpreter* interp, unsigned int ptr){
	return (*((uint32_t*)&interp->stack[ptr]) & STR_TAG) != 0;
}

int top_is_str(interpreter* interp){
	return raw_is_str(interp, interp->SP);
}


size_t raw_get_size(interpreter* interp, unsigned int ptr){
	if(raw_is_str(interp, ptr)){
		return (*((uint32_t*)&interp->stack[ptr]) & ~STR_TAG) + 4;
	}else{
		return 4;
	}
}

unsigned int get_ptr(interpreter* interp, unsigned int offset){
	unsigned int ptr = interp->SP;
	while(offset-->0){
		ptr += raw_get_size(interp, ptr);
	}
	return ptr;
}

uint32_t raw_get_int(interpreter* interp, unsigned int ptr){
	return *((uint32_t*)&interp->stack[ptr]);
}


char* raw_get_str(interpreter* interp, unsigned int ptr){
	if(!raw_is_str(interp, ptr)){
		return NULL;
	}
	uint32_t val = *((uint32_t*)&interp->stack[ptr]) & ~STR_TAG;
	return strndup(&interp->stack[ptr+4], val);
}

uint32_t pop_int(interpreter* interp){
	uint32_t val = raw_get_int(interp, interp->SP);
	interp->SP += 4;
	return val;
}

char* pop_str(interpreter* interp){
	if(!top_is_str(interp)){
		return NULL;
	}
	uint32_t val = *((uint32_t*)&interp->stack[interp->SP]) & ~STR_TAG;
	interp->SP += 4;
	char* str = strndup(&interp->stack[interp->SP], val);
	interp->SP += val;
	return str;
}

void push_str(interpreter* interp, const char* ptr, size_t length){
	interp->SP -= length;
	memcpy(&interp->stack[interp->SP], ptr, length);
	interp->SP -= 4;
	*(uint32_t*)&interp->stack[interp->SP] = length | STR_TAG;
}

int load_code(interpreter* interp, const char* path){
	FILE* fptr = fopen(path, "rb");
	
	uint32_t magic = {0};
	fread(&magic, sizeof(uint32_t), 1, fptr);

	if(magic!=MAGIC){
		return 0;
	}

	long code_start = ftell(fptr);
	fseek(fptr, 0, SEEK_END);
	long code_end = ftell(fptr);
	interp->code_length = code_end - code_start;
	fseek(fptr, code_start, SEEK_SET);

	interp->code = calloc(interp->code_length, sizeof(unsigned char));

	fread(interp->code, sizeof(unsigned char), interp->code_length, fptr);

	fclose(fptr);
	return 1;
}

#ifdef DEBUG
void debug_stack(interpreter* interp){
	unsigned int ptr = interp->SP;
	while(ptr < STACK_SIZE){
		if(raw_is_str(interp, ptr)){
			char* str = raw_get_str(interp, ptr);
			debug("['%s'] ", str);
			free(str);
		}else{
			uint32_t val = raw_get_int(interp, ptr);
			debug("[ %d ] ", val);
		}
		ptr += raw_get_size(interp, ptr);
	}
	debug("\n");
}
#else
	#define debug_stack //debug_stack
#endif

void op_push_int(interpreter* interp){
	debug("Reading uint16_t from %02x\n", interp->IP);
	uint16_t val = *((uint16_t*)&interp->code[interp->IP]);
	push_int(interp, val);
	interp->IP += 2;
	debug("OP_PUSH_INT: pushed %08x\n", val);
}

void op_push_str(interpreter* interp){
	debug("Reading uint16_t from %02x\n", interp->IP);
	uint16_t length = *((uint16_t*)&interp->code[interp->IP]);
	push_str(interp, &interp->code[interp->IP+2], length);
	interp->IP += length + 2;
	debug("OP_PUSH_STR: pushed string of length %08x\n", length);
}

void op_add(interpreter* interp){
	if(top_is_str(interp)){
		char* v2 = pop_str(interp);
		char* v1 = pop_str(interp);
		size_t combined = strlen(v1) + strlen(v2);
		debug("OP_ADD, adding '%s' and '%s' -> ", v1, v2);
		char* r = calloc(combined+1, sizeof(char));
		strncpy(r, v1, strlen(v1));
		strncat(r, v2, strlen(v2));
		debug("'%s'\n", r);
		free(v1);
		free(v2);
		push_str(interp, r, combined);
		free(r);
	}else{
		uint32_t v2 = pop_int(interp);
		if(!top_is_str(interp)){
			uint32_t v1 = pop_int(interp);
			debug("OP_ADD, computing %d + %d\n", v1, v2);
			push_int(interp, v1+v2);
		}else{
			char* v1 = pop_str(interp);
			debug("OP_ADD, adding '%s' and '%c' -> ", v1, (char)v2);
			size_t combined = strlen(v1) + 1;
			char* r = calloc(combined+1, sizeof(char));
			strncpy(r, v1, strlen(v1));
			r[strlen(v1)] = (char)v2;
			debug("'%s'\n", r);
			free(v1);
			push_str(interp, r, combined);
			free(r);
		}
	}
}
void op_sub(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_SUB, computing %d - %d\n", v1, v2);
	push_int(interp, (v1-v2) & 0xffff);
}

void op_mul(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_MUL, computing %d * %d\n", v1, v2);
	push_int(interp, (v1*v2) & 0xffff);
}

void op_div(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_DIV, computing %d / %d\n", v1, v2);
	push_int(interp, v1/v2);
}

void op_and(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_AND, computing %d & %d\n", v1, v2);
	push_int(interp, v1&v2);
}
void op_or(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_OR, computing %d | %d\n", v1, v2);
	push_int(interp, v1|v2);
	}
void op_xor(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_XOR, computing %d ^ %d\n", v1, v2);
	push_int(interp, v1^v2);
}
void op_not(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v1 = pop_int(interp);
	debug("OP_NOT, computing !%d\n", v1);
	push_int(interp, v1!=0?0:1);
}
void op_eq(interpreter* interp){
	if(top_is_str(interp)){
		char* v2 = pop_str(interp);
		char* v1 = pop_str(interp);
		debug("OP_EQ, computing '%s' == '%s'\n", v1, v2);
		push_int(interp, (strlen(v1) == strlen(v2)) | (strcmp(v1, v2)!=0?0:1)); //VULN: ORed instead of ANDed
		free(v1);
		free(v2);
	} else {
		uint32_t v2 = pop_int(interp);
		uint32_t v1 = pop_int(interp);
		debug("OP_EQ, computing %d == %d\n", v1, v2);
		push_int(interp, v1!=v2?0:1);
	}
}
void op_lt(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v2 = pop_int(interp);
	uint32_t v1 = pop_int(interp);
	debug("OP_LT, computing %d < %d\n", v1, v2);
	push_int(interp, v1<v2?1:0);
}
void op_dup(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t slot_nr = pop_int(interp);
	debug("OP_DUP, duplicating slot %d -> ", slot_nr);
	uint32_t ptr = get_ptr(interp, slot_nr);
	debug("ptr: 0x%x -> ", ptr);
	if(raw_is_str(interp, ptr)){
		char* v1 = raw_get_str(interp, ptr);
		debug("'%s'\n", v1);
		push_str(interp, v1, strlen(v1));
		free(v1);
	}else{
		uint32_t v1 = raw_get_int(interp, ptr);
		debug("%d\n", v1);
		push_int(interp, v1);
	}
}
void op_swap(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t slot_nr = pop_int(interp);
	debug("OP_SWAP, swapping top with slot %d -> ", slot_nr);
	uint32_t ptr = get_ptr(interp, slot_nr);
	debug("ptr: 0x%x\n", ptr);
	size_t slot_size = raw_get_size(interp, ptr);
	uint32_t top = interp->SP;
	size_t top_size = raw_get_size(interp, top);

	//INITIAL: top | top + top_size = from | .... | ptr | ptr + slot_size
	//TARGET:  top | top + slot_size = to  | .... | top | top + top_size
	char* slot_copy = calloc(slot_size, sizeof(unsigned char));
	memcpy(slot_copy, &interp->stack[ptr], slot_size);

	char* top_copy = calloc(top_size, sizeof(unsigned char));
	memcpy(top_copy, &interp->stack[top], top_size);

	size_t move_size = ptr - (top + top_size);
	memmove(&interp->stack[top + slot_size], &interp->stack[top+top_size], move_size);
	memmove(&interp->stack[top], slot_copy, slot_size);
	memmove(&interp->stack[top + slot_size + move_size], top_copy, top_size);

	free(slot_copy);
	free(top_copy);
}
void op_pop(interpreter* interp){
	debug("OP_POP\n");
	if(top_is_str(interp)){
		free(pop_str(interp));
	}else{
		pop_int(interp);
	}
}
void op_jmp(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t v1 = pop_int(interp);
	debug("OP_JMP, jumping to 0x%x\n", v1);
	interp->IP = v1;
}
void op_jmpi(interpreter* interp){
	if(top_is_str(interp)){
		exit(-1);
	}
	uint32_t cond = pop_int(interp);
	uint32_t jmploc = pop_int(interp);
	debug("OP_JMPI, jumping to 0x%x if %d is non-zero\n", jmploc, cond);
	if(cond){
		interp->IP = jmploc;
	}
}
void op_syscall(interpreter* interp){
	if(!top_is_str(interp)){
		exit(-1);
	}
	char* func_name = pop_str(interp);
	void* f = dlsym(RTLD_DEFAULT, func_name);
	uint32_t nargs = pop_int(interp);
	debug("OP_SYSCALL, calling function '%s' with %d args\n", func_name, nargs);
	argument args[MAX_ARGS];
	for(int i=0; i<nargs && i<MAX_ARGS; i++){
		if(top_is_str(interp)){
			args[i].arg_s = pop_str(interp);
		}else{
			args[i].arg_i = pop_int(interp);
		}
	}
	switch(nargs){
		case 0:
			push_int(interp, ((fn_0*)f)());
			break;
		case 1:
			push_int(interp, ((fn_1*)f)(args[0]));
			break;
		case 2:
			push_int(interp, ((fn_2*)f)(args[0], args[1]));
			break;
		case 3:
			push_int(interp, ((fn_3*)f)(args[0], args[1], args[2]));
			break;
		default:
			break;
	}
}
int interpret(interpreter* interp){

	unsigned long remaining_instructions = MAX_INS;

	while(remaining_instructions > 0 && interp->IP < interp->code_length){
		remaining_instructions--;
		debug("\nIP: %02x, SP: %04x, INS: %02x\n", interp->IP, interp->SP, interp->code[interp->IP]);
		debug("stack: ");
		debug_stack(interp);
		switch(interp->code[interp->IP++]){
			case OP_PUSH_INT:
				op_push_int(interp);
				break;
			case OP_PUSH_STR:
				op_push_str(interp);
				break;
			case OP_ADD:
				op_add(interp);
				break;
			case OP_SUB:
				op_sub(interp);	
				break;
			case OP_MUL:
				op_mul(interp);
				break;
			case OP_DIV:
				op_div(interp);		
				break;
			case OP_AND:
				op_and(interp);
				break;
			case OP_OR:
				op_or(interp);
				break;
			case OP_XOR:
				op_xor(interp);
				break;
			case OP_NOT:
				op_not(interp);
				break;
			case OP_EQ:
				op_eq(interp);	
				break;
			case OP_LT:
				op_lt(interp);
				break;
			case OP_DUP:
				op_dup(interp);	
				break;
			case OP_SWAP:
				op_swap(interp);
				break;
			case OP_POP:
				op_pop(interp);
				break;
			case OP_JMP:
				op_jmp(interp);
				break;
			case OP_JMPI:
				op_jmpi(interp);	
				break;
			case OP_SYSCALL:
				op_syscall(interp);	
				break;
			default:
				// NOP
				break;
		}
	}
	debug_stack(interp);
	return interp->stack[interp->SP];

}

int main(int argc, char** argv){

	if(argc<2){
		return 1;
	}

	interpreter interp = {
		.IP = 0,
		.SP = STACK_SIZE,
		.stack = calloc(STACK_SIZE, sizeof(unsigned char)),
		.code = NULL,
		.code_length = 0
	};

	if(!load_code(&interp, argv[1])){
		return 1;
	}

	return interpret(&interp);
}

