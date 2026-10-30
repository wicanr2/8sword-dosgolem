//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	dg "github.com/wicanr2/dosgolem"
)

func presenceFixture(t *testing.T) (*armyPresence, *dg.Machine) {
	p, makeMachine := armyPortFixture(t)
	m := makeMachine(0x1650)
	m.Write16(0x2e782, 0x0bd3)
	m.Write16(0x2e784, 0x110)
	v := &armyPresence{Port: p, Code: append([]byte(nil), m.Mem[0x1100+0x151c:0x1100+0x1796]...)}
	return v, m
}
func emptyPresence(t *testing.T, v *armyPresence) {
	w := v.Port.Current.World
	w.Revision++
	w.Army.Slots = [6]ArmyStack{}
	s, e := v.Port.Store.Commit(v.Port.Current.Token, w)
	if e != nil {
		t.Fatal(e)
	}
	v.Port.Current = s
}
func TestPresenceUsesOwnedIDsAndPairedLoss(t *testing.T) {
	for _, present := range []bool{false, true} {
		t.Run(map[bool]string{false: "empty", true: "wolves"}[present], func(t *testing.T) {
			v, m := presenceFixture(t)
			if present {
				w := v.Port.Current.World
				w.Revision++
				w.Army.Slots = [6]ArmyStack{{"openkb:wolf", 5}}
				s, e := v.Port.Store.Commit(v.Port.Current.Token, w)
				if e != nil {
					t.Fatal(e)
				}
				v.Port.Current = s
			} else {
				emptyPresence(t, v)
			}
			native := append([]byte(nil), m.Mem[0x1edca:0x1ede2]...)
			if ok, e := v.instruction(m, 0x1650); !ok || e != nil {
				t.Fatal(e)
			}
			flag := uint16(1)
			if present {
				flag = 0
			}
			if m.Read16(0x2e77e) != flag || m.CPU.IP != 0x1671 || v.HasArmy != present {
				t.Fatal("wrong Go presence")
			}
			if !present {
				gold := v.Port.Current.World.Army.Gold
				loss := gold / 3
				m.CPU.IP = 0x16a4
				m.CPU.R[dg.CX] = 3
				m.CPU.R[dg.AX] = uint16(loss)
				m.Write16(0x2e77a, uint16(loss))
				if ok, e := v.instruction(m, 0x16a4); !ok || e != nil {
					t.Fatal(e)
				}
				if v.Debits != 1 || v.Port.Current.World.Army.Gold != gold-loss || m.Read16(0x1ed78) != uint16(gold-loss) || m.CPU.IP != 0x16a8 {
					t.Fatal("loss projection")
				}
				token := v.Port.Current.Token
				v.Port.Store.Close()
				cold, s, e := openProgressPair(v.Port.Store.Dir, v.Port.Store.Catalog, v.Port.Store.Combat)
				if e != nil {
					t.Fatal(e)
				}
				defer cold.Close()
				if s.Token != token {
					t.Fatal("cold token")
				}
			}
			if !bytes.Equal(native, m.Mem[0x1edca:0x1ede2]) {
				t.Fatal("native rows changed")
			}
		})
	}
}
func TestNoArmyLossMatchesOriginalCPU(t *testing.T) {
	input := os.Getenv("EIGHTSWORD_PRESENCE_INPUT")
	raw, e := os.ReadFile(filepath.Join(input, "../oracle-r2.json"))
	if e != nil {
		t.Fatal(e)
	}
	var oracle struct {
		Losses []struct {
			Before  uint64 `json:"gold_before"`
			After   uint64 `json:"gold_after"`
			Loss    uint64 `json:"loss"`
			Divisor uint16 `json:"divisor"`
		}
	}
	if e = json.Unmarshal(raw, &oracle); e != nil {
		t.Fatal(e)
	}
	if len(oracle.Losses) != 20 {
		t.Fatal("missing original cases")
	}
	v, _ := presenceFixture(t)
	emptyPresence(t, v)
	for _, r := range oracle.Losses {
		w := v.Port.Current.World
		w.Army.Gold = r.Before
		next, loss, e := planNoArmyLoss(v.Port.Store.Catalog, v.Port.Store.Combat, w, r.Divisor)
		if e != nil || next.Army.Gold != r.After || loss != r.Loss {
			t.Fatal(r, e)
		}
	}
}
func TestPresenceRejectsWithoutWrites(t *testing.T) {
	for _, name := range []string{"source", "segment", "frame", "resource", "overflow", "stale", "double-gate", "debit-before-presence", "divisor", "quotient", "double-debit"} {
		t.Run(name, func(t *testing.T) {
			v, m := presenceFixture(t)
			emptyPresence(t, v)
			ip := uint16(0x1650)
			if name == "divisor" || name == "quotient" || name == "double-debit" {
				if _, e := v.instruction(m, ip); e != nil {
					t.Fatal(e)
				}
				ip = 0x16a4
				m.CPU.IP = ip
				m.CPU.R[dg.CX] = 3
				m.CPU.R[dg.AX] = uint16(v.Port.Current.World.Army.Gold / 3)
				m.Write16(0x2e77a, m.CPU.R[dg.AX])
			}
			switch name {
			case "source":
				m.Mem[0x1100+0x151c] ^= 1
			case "segment":
				m.CPU.Seg[dg.DS] = 1
			case "frame":
				m.Write16(0x2e782, 0x0bd4)
			case "resource":
				m.Write16(0x1ed78, 1)
			case "overflow":
				m.CPU.Cycles = ^uint64(0)
			case "stale":
				w := v.Port.Current.World
				w.Revision++
				if _, e := v.Port.Store.Commit(v.Port.Current.Token, w); e != nil {
					t.Fatal(e)
				}
			case "double-gate":
				if _, e := v.instruction(m, ip); e != nil {
					t.Fatal(e)
				}
				m.CPU.IP = ip
			case "debit-before-presence":
				ip = 0x16a4
				m.CPU.IP = ip
			case "divisor":
				m.CPU.R[dg.CX] = 1
			case "quotient":
				m.CPU.R[dg.AX]++
			case "double-debit":
				if _, e := v.instruction(m, ip); e != nil {
					t.Fatal(e)
				}
				m.CPU.IP = ip
			}
			mem := append([]byte(nil), m.Mem...)
			r, s, at, cycles := m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Cycles
			before, e := v.Port.Store.readBytes()
			if e != nil {
				t.Fatal(e)
			}
			if _, e = v.instruction(m, ip); e == nil {
				t.Fatal("unsafe request accepted")
			}
			after, e := v.Port.Store.readBytes()
			if e != nil {
				t.Fatal(e)
			}
			if !bytes.Equal(mem, m.Mem) || r != m.CPU.R || s != m.CPU.Seg || at != m.CPU.IP || cycles != m.CPU.Cycles || !bytes.Equal(before.Native, after.Native) || !bytes.Equal(before.World, after.World) {
				t.Fatal("rejection wrote data")
			}
		})
	}
}
