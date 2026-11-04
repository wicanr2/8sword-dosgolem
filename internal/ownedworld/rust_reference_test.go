package ownedworld

import (
	"fmt"
	"math"
	"os"
	"strings"
	"testing"
)

// Migration oracle only. Original executable evidence remains spec030's
// instruction/control receipts; these vectors compare Rust with proven Go.
func TestRustArithmeticReference(t *testing.T) {
	path := os.Getenv("EIGHTSWORD_RUST_REFERENCE")
	if path == "" {
		t.Skip("explicit Rust migration output")
	}
	var out strings.Builder
	out.WriteString("# attack count hp divisor multiplier pending target damage encoded pending_after count_after\n")
	emit := func(attack uint64, count uint16, hp uint64, divisor, multiplier uint16, pending uint64, target uint32) {
		amount, encoded, err := originalBattleAmountFor(attack, count, hp, divisor, multiplier)
		fmt.Fprintf(&out, "%d\t%d\t%d\t%d\t%d\t%d\t%d\t", attack, count, hp, divisor, multiplier, pending, target)
		if err != nil {
			out.WriteString("ERR\n")
			return
		}
		after := pending - min(pending, amount)
		countAfter := target - min(target, uint32(encoded))
		fmt.Fprintf(&out, "%d\t%d\t%d\t%d\n", amount, encoded, after, countAfter)
	}
	for _, attack := range []uint64{1, 6, 31, 100} {
		for _, count := range []uint16{0, 1, 30, 32767} {
			for _, hp := range []uint64{1, 7, 99} {
				for _, divisor := range []uint16{1, 5} {
					for _, multiplier := range []uint16{1, 2} {
						emit(attack, count, hp, divisor, multiplier, 1000, 30)
					}
				}
			}
		}
	}
	for _, v := range []struct {
		attack              uint64
		count               uint16
		hp                  uint64
		divisor, multiplier uint16
	}{
		{0, 1, 1, 1, 1}, {1, 1, 0, 1, 1}, {1, 1, 1, 0, 1}, {1, 1, 1, 1, 0},
		{math.MaxUint64, 2, 1, 1, 1}, {math.MaxUint64, 1, 1, 1, 2},
		{65535, 1, 1, 1, 1}, {65534, 1, 1, 1, 1}, {65536, 1, 2, 1, 1},
	} {
		emit(v.attack, v.count, v.hp, v.divisor, v.multiplier, 0, math.MaxUint32)
	}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	_, err = f.WriteString(out.String())
	ce := f.Close()
	if err != nil {
		t.Fatal(err)
	}
	if ce != nil {
		t.Fatal(ce)
	}
}
