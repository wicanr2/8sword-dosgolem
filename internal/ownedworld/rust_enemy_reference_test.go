package ownedworld

import (
	"fmt"
	"os"
	"strings"
	"testing"
)

// Development export of the already validated Go helper. No original execution.
func TestRustEnemyReference(t *testing.T) {
	path := os.Getenv("EIGHTSWORD_RUST_ENEMY_REFERENCE")
	if path == "" {
		t.Skip("explicit Rust enemy reference output")
	}
	var out strings.Builder
	out.WriteString("# Current verified Go helper; inherited oracle cases follow separately\n")
	for selector := 0; selector < 8; selector++ {
		for _, kind := range []uint16{10, 12, 0} {
			for _, count := range []uint32{0, 1, 2, 5, 35, 49, 50, 69, 99, 100, 400, 6553, 10922, 10923, 32767, 32768} {
				got, err := originalEnemyAmount(selector, kind, count)
				value := fmt.Sprint(got)
				if err != nil {
					value = "ERR"
				}
				fmt.Fprintf(&out, "AMOUNT\t%d\t%d\t%d\t%s\n", selector, kind, count, value)
			}
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
