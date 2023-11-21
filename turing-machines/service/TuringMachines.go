package main

import (
	"fmt"
	"regexp"
	"strings"
)

type TuringMachineAction struct {
	C string   `json:"c"`
	A []string `json:"a"`
	H int      `json:"h"`
	S string   `json:"s"`
}

type TuringMachineState struct {
	Name    string                `json:"name"`
	Actions []TuringMachineAction `json:"actions""`
}

type TuringMachineDef struct {
	Name   string               `json:"name"`
	States []TuringMachineState `json:"states"`
}

func (machine *TuringMachineDef) Check() bool {
	if machine.States == nil {
		return false
	}

	for _, state := range machine.States {
		if state.Name == "" || state.Actions == nil {
			return false
		}
		for _, action := range state.Actions {
			if action.S == "" {
				return false
			}
		}
	}

	return true
}

const CppTemplate = `
class CompiledTuringMachine : public TuringMachine {
public:
	inline CompiledTuringMachine(uint8_t *tapeStart, uint8_t *tapeEnd) : TuringMachine(tapeStart, tapeEnd) {}

	bool run(int steps) override {
		for (int i = 0; i < steps; i++) {
			if (head < tapeStart || head >= tapeEnd) {
				std::cerr << "Head is out of tape!\n";
				return false;
			}
			%s
		}
		return false;
	}

	const char *stateName(int state) override {
		%s
	}
};
`

// ExpressionRegex A safe expression follows this regex
var ExpressionRegex = regexp.MustCompile(`^(r[0-9a-f]|h|\d|0x[0-9a-f]+| |!=|[+\-<>()=])+$`)
var ExpressionRegex2 = regexp.MustCompile(`r([0-9a-f])`) // replace registers

func expressionToCpp(expr string) (string, error) {
	if !ExpressionRegex.MatchString(expr) {
		return "", fmt.Errorf("expression contains invalid tokens: '%s'", expr)
	}
	expr = ExpressionRegex2.ReplaceAllString(expr, `(registers[0x$1])`)
	expr = strings.ReplaceAll(expr, "h", "(*head)")
	return expr, nil
}

func conditionToCpp(c string) (string, error) {
	if len(c) == 1 {
		return fmt.Sprintf("*head == '\\x%02x'", c[0]), nil
	}
	return expressionToCpp(c)
}

func actionToCpp(a string) (string, error) {
	expressions := strings.SplitN(a, "=", 2)
	if len(expressions) != 2 {
		return "", fmt.Errorf("invalid action format, must be <a>=<b>: '%s'", a)
	}
	exprLeft, err := expressionToCpp(expressions[0])
	if err != nil {
		return "", err
	}
	exprRight, err := expressionToCpp(expressions[1])
	if err != nil {
		return "", err
	}
	return exprLeft + " = " + exprRight + ";", nil
}

func stringToCppLiteral(s string) string {
	return BytesToCppLiteral([]byte(s))
}

func BytesToCppLiteral(bytes []byte) string {
	var sb strings.Builder
	sb.WriteRune('"')
	for _, b := range bytes {
		if b >= ' ' && b <= '~' && b != '"' && b != '\\' {
			sb.WriteByte(b)
		} else {
			_, _ = fmt.Fprintf(&sb, "\\x%02x", b)
		}
	}
	sb.WriteRune('"')
	return sb.String()
}

func (machine *TuringMachineDef) Compile() (string, error) {
	stateIds := make(map[string]int)
	for i, state := range machine.States {
		stateIds[state.Name] = i
	}

	// build switch for states
	var sb strings.Builder
	sb.WriteString("switch (state) {\n")
	for id, state := range machine.States {
		_, _ = fmt.Fprintf(&sb, "\t\t\tcase %d: {\n", id)
		for _, action := range state.Actions {
			sb.WriteString("\t\t\t\t")
			if action.C != "" {
				condition, err := conditionToCpp(action.C)
				if err != nil {
					return "", err
				}
				_, _ = fmt.Fprintf(&sb, "if (%s) { ", condition)
			}
			if action.A != nil {
				for _, a := range action.A {
					cppAction, err := actionToCpp(a)
					if err != nil {
						return "", err
					}
					sb.WriteString(cppAction)
				}
			}
			if action.H != 0 {
				_, _ = fmt.Fprintf(&sb, "head += %d; ", action.H)
			}

			if nextState, ok := stateIds[action.S]; ok {
				_, _ = fmt.Fprintf(&sb, "state = %d; ", nextState)
			} else {
				return "", fmt.Errorf("invalid state name: '%s'", action.S)
			}
			sb.WriteString("break;")

			if action.C != "" {
				sb.WriteString(" }")
			}
			sb.WriteString("\n")
		}
		sb.WriteString("\t\t\t\treturn true;\n\t\t\t}\n")
	}
	sb.WriteString("\t\t\tdefault: return true;\n")
	sb.WriteString("\t\t\t}")

	// build switch for state names
	var sb2 strings.Builder
	sb2.WriteString("switch (state) {\n")
	for id, state := range machine.States {
		_, _ = fmt.Fprintf(&sb2, "\t\tcase %d: return %s;\n", id, stringToCppLiteral(state.Name))
	}
	sb2.WriteString("\t\tdefault: return \"?\";\n")
	sb2.WriteString("\t\t}")

	return fmt.Sprintf(CppTemplate, sb.String(), sb2.String()), nil
}
