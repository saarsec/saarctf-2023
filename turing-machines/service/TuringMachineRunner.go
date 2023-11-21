package main

import (
	"context"
	"crypto/rand"
	"errors"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"time"
)

var letters = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")

func RandomString(n int) string {
	b := make([]rune, n)
	r := make([]byte, n)
	_, err := rand.Read(r)
	if err != nil {
		log.Panicln(err)
	}
	for i := range b {
		b[i] = letters[int(r[i])%len(letters)]
	}
	return string(b)
}

const TestTemplate = `
%s
%s

uint8_t *tape = %s_tape;
constexpr size_t tape_size = %d;
TuringMachine *machine = new CompiledTuringMachine(tape, tape + tape_size);
FinalStateReporter *reporter = new FinalStateReporter(stdout);

int main() {
	bool terminated = machine->run(1000);
	reporter->reportFinalState(machine->state, machine->stateName(machine->state));
	reporter->reportFinalTape(tape, tape_size);
	return terminated ? 0 : 1;
}
`

func CompileTestProgramToCpp(machine *TuringMachineDef, tape []byte) (string, error) {
	if !machine.Check() {
		return "", errors.New("invalid machine")
	}
	headerfile, err := ioutil.ReadFile("turingcode/turingmachine.h")
	if err != nil {
		return "", err
	}

	machinecls, err := machine.Compile()
	if err != nil {
		return "", err
	}

	code := fmt.Sprintf(TestTemplate, string(headerfile), machinecls, BytesToCppLiteral(tape), len(tape))
	return code, nil
}

func RunTestProgram(machine *TuringMachineDef, tape []byte) ([]byte, error) {
	code, err := CompileTestProgramToCpp(machine, tape)
	if err != nil {
		return nil, err
	}

	filename := "/tmp/" + RandomString(16) + ".bin"
	defer os.Remove(filename)

	// Compile C++ program
	cmd := exec.Command("g++", "-O1", "-o", filename, "-x", "c++", "-")
	cmd.Stderr = os.Stderr
	stdin, _ := cmd.StdinPipe()
	err = cmd.Start()
	if err != nil {
		return nil, err
	}
	stdin.Write([]byte(code))
	stdin.Close()
	err = cmd.Wait()
	if err != nil {
		return nil, err
	}

	// Run C++ program
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	cmd = exec.CommandContext(ctx, "sh", "-c", "ulimit -n 10 && exec "+filename)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return output, err
	}
	return output, nil
}
