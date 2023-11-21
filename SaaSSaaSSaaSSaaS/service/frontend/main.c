#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <ctype.h>
#include <string.h>
#include <sys/stat.h>

#ifdef DEBUG
	#define debug printf
#else
	#define debug //debug
#endif

#define PWD_EXT (".pwd")
#define SRC_EXT (".src")
#define DATA_SUBDIR ("data")
#define COMPILER_CMD ("saascc")
#define INTERPRETER_CMD ("saarvm")

char* DATA_DIR = NULL;
char* COMPILER = NULL;
char* INTERPRETER = NULL;

void init(){
	char* cwd = getcwd(NULL, 0);
	
	DATA_DIR = malloc(strlen(cwd) + strlen(DATA_SUBDIR) + 2);
	strcpy(DATA_DIR, cwd);
	strcat(DATA_DIR, "/");
	strcat(DATA_DIR, DATA_SUBDIR);
	
	COMPILER = malloc(strlen(cwd) + strlen(COMPILER_CMD) + 2);
	strcpy(COMPILER, cwd);
	strcat(COMPILER, "/");
	strcat(COMPILER, COMPILER_CMD);
	
	INTERPRETER = malloc(strlen(cwd) + strlen(INTERPRETER_CMD) + 2);
	strcpy(INTERPRETER, cwd);
	strcat(INTERPRETER, "/");
	strcat(INTERPRETER, INTERPRETER_CMD);

	free(cwd);
}

char* get_trimmed_line(){
	char* line = NULL;
	size_t alloc_size = 0;
	size_t line_size = 0;
	if( (line_size = getline(&line, &alloc_size, stdin)) <= 0){
		exit(EXIT_FAILURE);
	}
	for(int i = line_size; iscntrl(line[i]) && i>=0; i--){
		line[i] = '\0';
	}
	return line;
}

int is_alnum(const char* line){
	size_t n = strlen(line);
	for(int i=0; i<n; i++){
		if(!isalnum(line[i])){
			return 0;
		}
	}
	return 1;
}

char* read_program_name(){
	char* program_name = get_trimmed_line();
	if((strlen(program_name)<8) || (strlen(program_name)>32) || (!is_alnum(program_name))){
		free(program_name);
		fprintf(stderr, "[ERR] Program name must consist of 8-32 alphanumerical characters!\n");
		exit(EXIT_FAILURE);
	}
	debug("Read program name '%s'\n", program_name);
	return program_name;
}
void greet(){
	printf("=================================================[ SaaSSaaSSaaSSaaS ]===============================================\n");
	printf("Saarsec's alluring allegiant superb secure and absolutely safe, speedy advanced arithmetic stack system as a service\n");
	printf("=================================================[ (c) saarsec 2023 ]===============================================\n");
	printf("\n");
}

int menu(){
	printf("Menu:\n");
	printf("1 - Run Program\n");
	printf("2 - Create new public program\n");
	printf("3 - Create new private script\n");
	printf("\n");
	debug("Working dir: %s\n", DATA_DIR);
	debug("\n");
	printf("Your choice: ");
	char* line = get_trimmed_line();
	int retval = line[0] - '0';
	free(line);
	return retval;
}

int check_password(const char* program_path){
	int result = 0;

	char* pwd_path = malloc(strlen(program_path) + strlen(PWD_EXT) + 1);
	strcpy(pwd_path, program_path);
	strcat(pwd_path, PWD_EXT);
	debug("Looking for password file at '%s'\n", pwd_path);

	if(!access(pwd_path, R_OK)){
		debug("Password file '%s' DOES exist, checking password...\n", pwd_path);
		char password[64] = {0};
		FILE* fptr = fopen(pwd_path, "r");
		fread(password, sizeof(char), sizeof(password)-1, fptr);
		fclose(fptr);
		printf("Please enter the password: ");
		char* entered = get_trimmed_line();
		result = !strncmp(password, entered, strlen(password));
		free(entered);
	}else{
		debug("Password file '%s' does not exist\n", pwd_path);
		result = 1;
	}

	free(pwd_path);
	return result;
}

char* path_for_name(const char* program_name){
	char* program_name_joined = malloc(strlen(program_name) + strlen(DATA_SUBDIR) + 2);
	strcpy(program_name_joined, DATA_SUBDIR);
	strcat(program_name_joined, "/");
	strcat(program_name_joined, program_name);
	debug("ID '%s' -> '%s'\n", program_name, program_name_joined);
	return program_name_joined;
}

void run_program(){
	printf("Please enter the name of the program you'd like to run: ");
	char* program_name = read_program_name();
	debug("You entered '%s'!\n", program_name);
	char* program_path = path_for_name(program_name);

	if(access(program_path, F_OK)){
		printf("Error, no such program!\n");
		return;
	}
	debug("Resolved path: '%s'!\n", program_path);

	if(!check_password(program_path)){
		printf("Error, invalid password!\n");
	}else{
		printf("Running %s:\n", program_name);
		execl(INTERPRETER, INTERPRETER, program_path, (char *) NULL);
	}
	
	free(program_path);
	free(program_name);
}

void create_new_password(const char* program_path){
	char* pwd_path = malloc(strlen(program_path) + strlen(PWD_EXT) + 1);
	strcpy(pwd_path, program_path);
	strcat(pwd_path, PWD_EXT);

	debug("Writing password file to '%s'\n", pwd_path);

	char password[64] = {0};
	unsigned char randbyte[16] = {0};
	FILE* rfptr = fopen("/dev/urandom","rb");
	fread(randbyte, sizeof(unsigned char), sizeof(randbyte), rfptr);
	fclose(rfptr);
	for(int i=0; i<sizeof(randbyte) && 2*i<sizeof(password); i++){
		debug("Random byte %d = %08x", randbyte[i]);
		sprintf(&password[2*i], "%02x", randbyte[i]);
	}

	FILE* fptr = fopen(pwd_path, "w");
	if(!fptr){
		fprintf(stderr, "[ERR] Could not create file %s!\n", pwd_path);
		exit(EXIT_FAILURE);
	}
	fprintf(fptr, "%s", password);
	fclose(fptr);

	printf("Your password is: %s\n", password);

	free(pwd_path);
}



void read_source(const char* program_path){
	char* src_path = malloc(strlen(program_path) + strlen(SRC_EXT) + 1);
	strcpy(src_path, program_path);
	strcat(src_path, SRC_EXT);
	debug("Writing source file to '%s'\n", src_path);
	printf("Please enter your program one line at a time\n");
	printf("Terminate your input with a blank line\n");

	FILE* fptr = fopen(src_path, "w");
	if(!fptr){
		fprintf(stderr, "[ERR] Could not create file %s!\n", src_path);
		exit(EXIT_FAILURE);
	}
	free(src_path);
	char* line = NULL;
	while(strlen((line = get_trimmed_line()))>0){
		fprintf(fptr, "%s\n", line);
		free(line);
	}
	free(line);
	fclose(fptr);

	debug("Finished reading!\n");

}

void compile(const char* program_path){
	char* src_path = malloc(strlen(program_path) + strlen(SRC_EXT) + 1);
	strcpy(src_path, program_path);
	strcat(src_path, SRC_EXT);
	debug("Compiling: %s %s %s %s\n", COMPILER, "-o", program_path, src_path);
	execl(COMPILER, COMPILER, "-o", program_path, src_path, (char *) NULL);
	free(src_path);
}

void new_program(int create_password){
	printf("Please enter a name for your program: ");
	char* program_name = read_program_name();
	char* program_path = path_for_name(program_name);
	free(program_name);
	if(!access(program_path, F_OK)){
		fprintf(stderr, "[ERR] Program exists already\n");
		exit(EXIT_FAILURE);
	}
	if(create_password){
		create_new_password(program_path);
	}
	read_source(program_path);
	compile(program_path);
}

	
int main(){
	init();
	greet();
	int retry = 1;
	while(retry){
		int choice = menu();
		retry = 0;
		switch(choice){
			case 1:
				run_program();
				break;
			case 2:
				new_program(0);
				break;
			case 3:
				new_program(1);
				break;
			default:
				retry = 1;
		}
	}

	return 0;
}
