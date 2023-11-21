package main

import (
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/template/html/v2"
	"io/ioutil"
	"log"
	"os"
	"regexp"
	"strings"
)

var IdentRegex = regexp.MustCompile(`^[A-Za-z]{32}$`)

func SaveMachine(ident string, machine *TuringMachineDef) error {
	if !IdentRegex.MatchString(ident) {
		return errors.New("invalid ident")
	}
	data, err := json.Marshal(machine)
	if err != nil {
		return err
	}
	return ioutil.WriteFile("data/"+ident+".json", data, 0640)
}

func LoadMachine(ident string) (*TuringMachineDef, error) {
	if !IdentRegex.MatchString(ident) {
		return nil, errors.New("invalid ident")
	}
	data, err := ioutil.ReadFile("data/" + ident + ".json")
	if err != nil {
		return nil, err
	}
	machine := new(TuringMachineDef)
	if err := json.Unmarshal(data, machine); err != nil {
		return nil, err
	}
	return machine, nil
}

type TuringMachineFormData struct {
	Name   string `form:"name"`
	States string `form:"states"`
}

func handleNewMachine(c *fiber.Ctx) error {
	var data TuringMachineFormData
	if err := c.BodyParser(&data); err != nil {
		return err
	}
	machine := TuringMachineDef{Name: data.Name}
	if err := json.Unmarshal([]uint8(data.States), &machine.States); err != nil {
		return err
	}
	if !machine.Check() {
		return c.Render("machine_new", fiber.Map{"machine": machine, "error": "invalid machine"}, "base")
	}
	ident := RandomString(32)
	err := SaveMachine(ident, &machine)
	if err != nil {
		return c.Render("machine_new", fiber.Map{"machine": machine, "error": fmt.Sprintf("error %s", err)}, "base")
	}
	return c.Redirect("/machines/" + ident)
}

func handleGetMachine(c *fiber.Ctx) error {
	ident := c.Params("ident")
	machine, err := LoadMachine(ident)
	if err != nil {
		return err
	}
	return c.Render("machine_edit", fiber.Map{
		"id":      ident,
		"machine": machine,
		"base":    c.BaseURL(),
	}, "base")
}

type TuringMachineFormData2 struct {
	Ident  string `form:"ident"`
	Name   string `form:"name"`
	States string `form:"states"`
	Action string `form:"action"`
}

func handleUpdateMachine(c *fiber.Ctx) error {
	var data TuringMachineFormData2
	if err := c.BodyParser(&data); err != nil {
		return err
	}
	machine := TuringMachineDef{Name: data.Name}
	if err := json.Unmarshal([]uint8(data.States), &machine.States); err != nil {
		return err
	}
	if !machine.Check() {
		return c.Render("machine_get", fiber.Map{"id": data.Ident, "machine": machine, "error": "invalid machine"}, "base")
	}
	err := SaveMachine(data.Ident, &machine)
	if err != nil {
		errorText := fmt.Sprintf("error %s", err)
		if os.IsPermission(err) {
			errorText = "Updates are not permitted on this machine"
		}
		return c.Render("machine_edit", fiber.Map{
			"id":      data.Ident,
			"machine": machine,
			"base":    c.BaseURL(),
			"error":   errorText,
		}, "base")
	}

	// compile?
	if data.Action == "compile" {
		code, err := machine.Compile()
		if err != nil {
			return c.Render("machine_edit", fiber.Map{
				"id":      data.Ident,
				"machine": machine,
				"base":    c.BaseURL(),
				"error":   fmt.Sprintf("compiler error %s", err),
			}, "base")
		}
		c.Response().Header.Add("Content-Disposition", `attachment; filename="machine.cpp"`)
		return c.SendString(code)
	}

	if data.Action == "test" {
		return c.Redirect("/machine/run/" + data.Ident)
	}

	return c.Redirect("/machines/" + data.Ident)
}

func handleMachineRunGet(c *fiber.Ctx) error {
	ident := c.Params("ident")
	machine, err := LoadMachine(ident)
	if err != nil {
		return err
	}
	return c.Render("machine_run", fiber.Map{
		"id":      ident,
		"machine": machine,
	}, "base")
}

type TapeFormData struct {
	Ident  string `form:"ident"`
	Tape   string `form:"tape"`
	Action string `form:"action"`
}

func handleMachineRunPost(c *fiber.Ctx) error {
	var data TapeFormData
	if err := c.BodyParser(&data); err != nil {
		return err
	}
	// load machine
	machine, err := LoadMachine(data.Ident)
	if err != nil {
		return err
	}
	// decode tape
	tape, err := hex.DecodeString(strings.ReplaceAll(strings.ReplaceAll(data.Tape, " ", ""), "\n", ""))
	if err != nil {
		return c.Render("machine_run", fiber.Map{
			"id":      data.Ident,
			"machine": machine,
			"tape":    data.Tape,
			"error":   "tape is not proper hex!",
		}, "base")
	}

	if data.Action == "program" {
		code, err := CompileTestProgramToCpp(machine, tape)
		if err != nil {
			return c.Render("machine_run", fiber.Map{
				"id":      data.Ident,
				"machine": machine,
				"tape":    data.Tape,
				"error":   fmt.Sprintf("compiler error: %s", err),
			}, "base")
		}
		c.Response().Header.Add("Content-Disposition", `attachment; filename="machine_test.cpp"`)
		return c.SendString(code)
	}
	if data.Action == "run" {
		output, err := RunTestProgram(machine, tape)
		if err != nil {
			return c.Render("machine_run", fiber.Map{
				"id":      data.Ident,
				"machine": machine,
				"tape":    data.Tape,
				"output":  string(output),
				"error":   fmt.Sprintf("compiler or runtime error: %s", err),
			}, "base")
		}
		return c.Render("machine_run", fiber.Map{
			"id":      data.Ident,
			"machine": machine,
			"tape":    data.Tape,
			"output":  string(output),
		}, "base")
	}
	return c.SendString("Invalid action")
}

func Server(port int) {
	_ = os.MkdirAll("data", 0750)

	engine := html.New("./views", ".html")
	engine.AddFunc("json", func(o interface{}) string {
		data, err := json.MarshalIndent(o, "", "\t")
		if err != nil {
			return fmt.Sprintf("invalid json data: %s", err)
		}
		return string(data)
	})

	app := fiber.New(fiber.Config{Views: engine})
	app.Static("/static/", "./static")

	app.Get("/", func(c *fiber.Ctx) error {
		return c.Render("index", fiber.Map{}, "base")
	})

	app.Get("/machine/new", func(c *fiber.Ctx) error {
		return c.Render("machine_new", fiber.Map{"machine": TuringMachineDef{}}, "base")
	})
	app.Post("/machine/new", handleNewMachine)

	app.Get("/machines/:ident", handleGetMachine)
	app.Post("/machine/update", handleUpdateMachine)

	app.Get("/machine/run/:ident", handleMachineRunGet)
	app.Post("/machine/run/:ident", handleMachineRunPost)

	err := app.Listen(fmt.Sprintf(":%d", port))
	if err != nil {
		log.Panicln(err)
	}
}
