//go:build ignore

package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
)

func armyPortFixture(t *testing.T) (*worldArmyPort, func(uint16) *dg.Machine) {
	t.Helper()
	input := os.Getenv("EIGHTSWORD_ARMY_PORT_INPUT")
	if input == "" {
		t.Fatal("real inputs required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"seed-world.json", &w}} {
		b, e := os.ReadFile(filepath.Join(input, v.Name))
		if e != nil {
			t.Fatal(e)
		}
		if e = pairStrictJSON(b, v.Dst); e != nil {
			t.Fatal(e)
		}
	}
	w.Army.Slots = [6]ArmyStack{{"native:01", 30}, {"openkb:wolf", 5}}
	w.Army.Offers["verified-militia-shop-r1"] = ArmyOffer{"native:01", 1000}
	base, e := os.ReadFile(filepath.Join(input, "original-save.ay"))
	if e != nil {
		t.Fatal(e)
	}
	dir := filepath.Join(t.TempDir(), "pair")
	if e = initializeProgressPair(dir, base, c, cc, w); e != nil {
		t.Fatal(e)
	}
	s, snap, e := openProgressPair(dir, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(s.Close)
	pam, e := os.ReadFile(filepath.Join(input, "PAM.AY"))
	if e != nil {
		t.Fatal(e)
	}
	code, e := worldArmyCode(pam)
	if e != nil {
		t.Fatal(e)
	}
	p := &worldArmyPort{Store: s, Current: snap, Expected: map[uint16][]byte{0x54ea: code[0x54ea:0x58f0]}, ShopOpen: true, ShopStock: 1000}
	makeMachine := func(ip uint16) *dg.Machine {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.Seg[dg.SS] = 0x1e88
		m.CPU.Seg[dg.DS] = 0x1e88
		m.CPU.IP = ip
		m.CPU.R[dg.BP] = 0xff00
		m.CPU.R[dg.SP] = 0xfef0
		ds := uint32(0x1e880)
		m.Write16(ds+0xfef0, 0x110)
		m.Write16(ds+0xfef2, 1)
		m.Write16(ds+0xff06, 1)
		m.Write16(ds+0xff08, 1000)
		m.Write16(ds+0xfefe, 1)
		for i, n := range pairWorldResources(p.Current.World).words() {
			m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
		}
		// Poisoned original rows demonstrate that every result uses Go IDs.
		for i := 0; i < 24; i++ {
			m.Mem[ds+0x54a+uint32(i)] = 255
		}
		return m
	}
	return p, makeMachine
}

func TestWorldArmyPortReadCommitAndCold(t *testing.T) {
	p, makeMachine := armyPortFixture(t)
	army := append([]byte(nil), makeMachine(0x56ec).Mem[0x1edca:0x1ede2]...)
	for _, v := range []struct {
		IP    uint16
		Route string
		Want  uint16
	}{{0x556a, "capacity", 1}, {0x55c2, "command", 1}, {0x55cd, "used", 45}} {
		m := makeMachine(v.IP)
		sp := m.CPU.R[dg.SP]
		if e := p.execute(m, v.IP, v.Route); e != nil {
			t.Fatal(e)
		}
		if m.CPU.R[dg.AX] != v.Want || m.CPU.IP != v.IP+3 || m.CPU.R[dg.SP] != sp+2 || m.CPU.Cycles != 1 {
			t.Fatal("call ABI", v, m.CPU)
		}
	}
	m := makeMachine(0x56ec)
	oldGold := p.Current.World.Army.Gold
	if e := p.execute(m, 0x56ec, "commit"); e != nil {
		t.Fatal(e)
	}
	if m.CPU.IP != 0x576b || m.Read16(0x1ed78) != uint16(oldGold-1) || p.Current.World.Army.Slots[0].Count != 31 || p.Current.World.Army.Slots[1].Count != 5 || !bytes.Equal(army, m.Mem[0x1edca:0x1ede2]) {
		t.Fatal("commit/projection/isolated rows")
	}
	token := p.Current.Token
	p.Store.Close()
	cold, v, e := openProgressPair(p.Store.Dir, p.Store.Catalog, p.Store.Combat)
	if e != nil {
		t.Fatal(e)
	}
	defer cold.Close()
	if v.Token != token {
		t.Fatal("cold differs")
	}
}

func TestWorldArmyPortRejectsWithoutGuestOrDiskWrites(t *testing.T) {
	for _, name := range []string{"code", "resource", "kind", "frame", "stack", "zero-count", "over-quote", "closed", "route", "stale"} {
		t.Run(name, func(t *testing.T) {
			p, makeMachine := armyPortFixture(t)
			ip, route := uint16(0x55cd), "used"
			if name == "zero-count" || name == "over-quote" {
				ip, route = 0x56ec, "commit"
			}
			m := makeMachine(ip)
			switch name {
			case "code":
				m.Mem[0x1100+0x54ea] ^= 1
			case "resource":
				m.Write16(0x1ed78, 1)
			case "kind":
				m.Write16(0x2e786, 26)
			case "frame":
				m.CPU.Seg[dg.DS] = 0x1234
			case "stack":
				m.CPU.R[dg.SP] = 65535
			case "zero-count":
				m.Write16(0x2e77e, 0)
			case "over-quote":
				m.Write16(0x2e77e, 1000)
			case "closed":
				p.ShopOpen = false
			case "route":
				route = "unknown"
			case "stale":
				w := p.Current.World
				w.Revision++
				if _, e := p.Store.Commit(p.Current.Token, w); e != nil {
					t.Fatal(e)
				}
			}
			oldMem := append([]byte(nil), m.Mem...)
			r, s, at, cycles := m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Cycles
			b, e := p.Store.readBytes()
			if e != nil {
				t.Fatal(e)
			}
			if e = p.execute(m, ip, route); e == nil {
				t.Fatal("unsafe request accepted")
			}
			after, e := p.Store.readBytes()
			if e != nil {
				t.Fatal(e)
			}
			if !bytes.Equal(oldMem, m.Mem) || m.CPU.R != r || m.CPU.Seg != s || m.CPU.IP != at || m.CPU.Cycles != cycles || !bytes.Equal(b.Native, after.Native) || !bytes.Equal(b.World, after.World) {
				t.Fatal("rejection wrote data")
			}
		})
	}
}

func TestWorldArmyCapacityUsesStringIDsAndWideCounts(t *testing.T) {
	p, _ := armyPortFixture(t)
	c := p.Store.Catalog
	a := p.Current.World.Army
	a.Slots = [6]ArmyStack{{"native:01", 1}, {"native:02", 1}, {"native:03", 1}, {"native:04", 1}, {"native:05", 1}, {"openkb:wolf", 1}}
	for id, want := range map[string]bool{"native:01": true, "openkb:wolf": true, "native:25": false} {
		got, e := worldArmyCapacity(c, a, id)
		if e != nil || got != want {
			t.Fatal(id, got, e)
		}
	}
	if _, e := worldArmyCapacity(c, a, "26"); e == nil {
		t.Fatal("numeric extension identity accepted")
	}
	a.Slots = [6]ArmyStack{{"native:01", 1000000}}
	a.Leadership = 1000000
	v, e := measureWorldArmy(c, a)
	if e != nil || v.Used != 1000000 || v.Total != 1000000 {
		t.Fatal("wide count", v, e)
	}
}
