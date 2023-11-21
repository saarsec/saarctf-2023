package main

import (
	"testing"
)

func TestRegex(t *testing.T) {
	tests := []string{"h", ">", "=", "1", ">=", ">=104", "h>=104"}
	for _, s := range tests {
		if !ExpressionRegex.MatchString(s) {
			t.Errorf("Failed: '%s'", s)
		}
	}
}
