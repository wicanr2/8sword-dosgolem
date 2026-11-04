package ownedworld

import (
	"fmt"
	"os"
	"strings"
	"testing"
)

func TestRustSpellReference(t *testing.T) {
	path := os.Getenv("EIGHTSWORD_RUST_SPELL_REFERENCE")
	if path == "" {
		t.Skip("explicit Rust spell vector output")
	}
	var out strings.Builder
	out.WriteString("# Verified Go helpers; model vectors, not fresh original executable receipts\n")
	for selector := 0; selector < 8; selector++ {
		for _, kind := range []uint16{10, 12} {
			for _, source := range []uint32{2, 6} {
				for _, target := range []uint32{1, 49, 50, 69, 10923, 32768} {
					for _, hp := range []uint64{9, 20} {
						for _, tk := range []uint16{11, 16} {
							for _, stat := range []uint16{0, 2, 6000} {
								got, err := originalSpellAmount(selector, kind, source, target, hp, tk, stat)
								value := fmt.Sprint(got)
								if err != nil {
									value = "ERR"
								}
								fmt.Fprintf(&out, "AMOUNT\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n", selector, kind, source, target, hp, tk, stat, value)
							}
						}
					}
				}
			}
		}
	}
	for _, kind := range []uint16{10, 12, 0} {
		for _, count := range []uint32{0, 1, 49, 50, 99, 100, 199, 200, 299, 300, 399, 400, 6553, 6554, 32767, 32768} {
			scaled, after, factor, err := originalClonePlan(kind, count)
			result := fmt.Sprintf("%d,%d,%d", scaled, after, factor)
			if err != nil {
				result = "ERR"
			}
			fmt.Fprintf(&out, "CLONE\t%d\t%d\t%s\n", kind, count, result)
		}
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = f.WriteString(out.String()); err != nil {
		t.Fatal(err)
	}
	if err = f.Close(); err != nil {
		t.Fatal(err)
	}
}
