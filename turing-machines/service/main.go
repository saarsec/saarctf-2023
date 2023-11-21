package main

import (
	"encoding/json"
	"flag"
	"io/ioutil"
	"log"
	"os"
)

/*
 * USAGE: ./binary <machine.json>                         # compile to c++
 *        ./binary -tape <tape-file> <machine.json>       # compile to test file
 *        ./binary -type <tape-file> -run <machine.json>  # compile + test file
 *        ./binary -serve 8000                            # start server
 */
func main() {
	tapefile := flag.String("tape", "", "A start tape to run")
	run := flag.Bool("run", false, "Run the generated program")
	serve := flag.Int("serve", 0, "Port to start server")
	flag.Parse()

	if serve != nil && *serve != 0 {
		Server(*serve)
		return
	}

	if flag.NArg() == 0 {
		flag.Usage()
		os.Exit(1)
	}
	filename := flag.Arg(0)

	jsonFile, err := os.Open(filename)
	if err != nil {
		log.Panicln(err)
	}
	defer jsonFile.Close()

	byteValue, _ := ioutil.ReadAll(jsonFile)
	var machine TuringMachineDef
	err = json.Unmarshal(byteValue, &machine)
	if err != nil {
		log.Panicln(err)
	}

	if !machine.Check() {
		log.Panicln("machine invalid!")
	}

	if tapefile != nil && *tapefile != "" {
		tape, err := ioutil.ReadFile(*tapefile)
		if err != nil {
			log.Panicln(err)
		}

		if run != nil && *run {
			// run test binary
			result, err := RunTestProgram(&machine, tape)
			if result != nil && len(result) > 0 {
				_, _ = os.Stdout.Write(result)
			}
			if err != nil {
				log.Panicln(err)
			}
		} else {
			// generate test binary code
			code, err := CompileTestProgramToCpp(&machine, tape)
			if err != nil {
				log.Panicln(err)
			}
			os.Stdout.WriteString(code + "\n")
		}

	} else {
		// Compile turing machine to C++
		code, err := machine.Compile()
		if err != nil {
			log.Panicln(err)
		}
		os.Stdout.WriteString(code + "\n")
	}
}
