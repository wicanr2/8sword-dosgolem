//go:build ignore

// 030 DRAFT: original caller controls with an explicitly stubbed battle callee.
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/wicanr2/dosgolem/oracle"
)

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func write(path string, v any) {
	raw, e := json.MarshalIndent(v, "", "  ")
	must(e)
	f, e := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	must(e)
	_, e = f.Write(append(raw, '\n'))
	must(e)
	must(f.Close())
}

type control struct {
	Name                       string
	Region, Result, Legacy26AA uint16
	Boss                       bool
}

func main() {
	root := flag.String("root", "", "read-only game")
	state := flag.String("state", "", "fixed original snapshot")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 || *root == "" || *out == "" {
		panic("explicit paths and UID1000")
	}
	if _, e := os.Stat(*out); !os.IsNotExist(e) {
		panic("output exists")
	}
	must(os.Mkdir(*out, 0755))
	raw, e := os.ReadFile(*state)
	must(e)
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != "e618d4343697fa00a50ab4b6021b169f6a5e21e4eaf86100c1fac9cd7a98777b" {
		panic("source snapshot")
	}
	o, e := oracle.LoadWith(filepath.Join(*root, "PAM.AY"), *root, oracle.Options{Adlib: true})
	must(e)
	defer o.Close()
	must(o.LoadStateFile(*state))
	o.SetScratch(filepath.Join(*out, "scratch"))
	base := o.Save()
	ds := uint16(0x1e88)
	word := func(off uint16) uint16 { return o.Word(oracle.Addr{Seg: ds, Off: off}) }
	set := func(off, v uint16) { o.WriteU16(oracle.Addr{Seg: ds, Off: off}, v) }
	words := func(off uint16, n int) []uint16 {
		v := make([]uint16, n)
		for i := range v {
			v[i] = word(off + uint16(i*2))
		}
		return v
	}
	bases := []uint16{0x365e, 0x3706, 0x3766, 0x37c6, 0x3826, 0x3886, 0x38e6, 0x3946}
	var sc control
	var events []map[string]any
	var inputStep uint64
	var battleCalls, choiceCalls int
	randomInput := -1
	capture := func() map[string]any {
		return map[string]any{"progress": words(0x4f2, 6), "army": words(0x54a, 12), "battle": words(0x56e8, 24), "pool": words(0x365e, 516), "coordinates": words(0x8c30, 24), "position": []uint16{word(0x8e12), word(0x8e44)}, "region": word(0x56d6), "pieces": words(0x275a, 8), "legacy_26aa": word(0x26aa), "step": o.Steps()}
	}
	for _, ip := range []uint16{0x2fc3, 0x330e, 0x3733, 0x373e, 0x3745, 0x309e, 0x32a3, 0x1abe, 0x1d08, 0x1d48} {
		ip := ip
		o.OnCall(oracle.Addr{Seg: 0x110, Off: ip}, func(o *oracle.Oracle) {
			if ip == 0x1d08 {
				randomInput = int(o.Regs().AX)
			}
			if ip == 0x2fc3 {
				o.SetRegs(oracle.CallRegs{AX: 1, SetAX: true})
			} // explicit confirmation fixture
			if ip == 0x330e {
				o.SetRegs(oracle.CallRegs{AX: 0x41, SetAX: true})
			} // caller's tile result fixture
			if ip == 0x3733 {
				battleCalls++
			}
			if ip == 0x373e {
				for n := 0; n < 6; n++ {
					set(0x56e8+uint16(n*4), 0)
					set(0x56ea+uint16(n*4), 0)
					set(0x5700+uint16(n*4), 0)
					set(0x5702+uint16(n*4), 0)
				}
				if sc.Result != 2 {
					set(0x56e8, 1)
					set(0x56ea, 11)
				}
				if sc.Result != 0 {
					set(0x5700, 1)
					set(0x5702, 8)
					set(0x5710, 5)
					set(0x5712, 2)
				}
			}
			if ip == 0x1d48 {
				choiceCalls++
				o.SetRegs(oracle.CallRegs{AX: 2, SetAX: true})
			} // explicit roam, no map reload
			if len(events) > 40 {
				panic("event bound")
			}
			v := capture()
			v["ip"] = ip
			v["registers"] = o.Regs()
			events = append(events, v)
		})
	}
	o.OnCall(oracle.Addr{Seg: 0x160a, Off: 0x87}, func(o *oracle.Oracle) {
		if o.Steps()-inputStep < 50000 {
			return
		}
		inputStep = o.Steps()
		o.KeyDown(0x1c)
		o.KeyUp(0x1c)
		must(o.SendKeys("Return"))
	})
	var cases []control
	for _, area := range []uint16{0, 1, 7} {
		for _, result := range []uint16{0, 1, 2} {
			cases = append(cases, control{Name: fmt.Sprintf("region%d-result%d", area, result), Region: area, Result: result})
		}
	}
	cases = append(cases, control{Name: "region1-boss-bonus", Region: 1, Result: 0, Legacy26AA: 1, Boss: true})
	var rows []map[string]any
	for _, v := range cases {
		sc = v
		o.Restore(base)
		events = nil
		inputStep = 0
		battleCalls = 0
		choiceCalls = 0
		randomInput = -1
		set(0x56d6, sc.Region)
		set(0x56c4, 1)
		set(0x4f2, 1)
		set(0x4f4, 10000)
		set(0x4f6, 100)
		set(0x4f8, 500)
		set(0x4fa, 100)
		set(0x4fc, 10)
		set(0x26aa, sc.Legacy26AA)
		for n := 0; n < 8; n++ {
			set(0x275a+uint16(n*2), 0)
		}
		x, y := word(0x8e12), word(0x8e44)
		for n := 0; n < 12; n++ {
			set(0x8c30+uint16(n*4), 65535)
			set(0x8c32+uint16(n*4), 65535)
		}
		set(0x8c30, x)
		set(0x8c32, y)
		set(0x26bc+sc.Region*6, 65535)
		set(0x26be+sc.Region*6, 65535)
		if sc.Boss {
			set(0x26bc+sc.Region*6, x)
			set(0x26be+sc.Region*6, y)
		}
		for n := 0; n < 6; n++ {
			set(0x54a+uint16(n*4), 0)
			set(0x54c+uint16(n*4), 0)
			set(bases[sc.Region]+uint16(n*4), 0)
			set(bases[sc.Region]+2+uint16(n*4), 0)
		}
		set(0x54a, 1)
		set(0x54c, 12)
		for n, c := range []uint16{12, 7, 4} {
			set(bases[sc.Region]+uint16(n*4), uint16(n*2+1))
			set(bases[sc.Region]+2+uint16(n*4), c)
		}
		// Keep the separate ending guard alive; no final-game entry in this fixture.
		set(0x365e+24*4, 1)
		set(0x3660+24*4, 1)
		battleAddr := oracle.Addr{Seg: 0xf67, Off: 8}
		original := append([]byte(nil), o.Bytes(battleAddr, 4)...)
		o.WriteU16(battleAddr, 0xb8|sc.Result<<8)
		o.WriteU16(oracle.Addr{Seg: 0xf67, Off: 10}, 0xcb00)
		dir := filepath.Join(*out, sc.Name)
		must(os.Mkdir(dir, 0755))
		before := capture()
		must(o.SaveStateFile(filepath.Join(dir, "before.state")))
		_, err := o.CallBudget(14000000, oracle.Addr{Seg: 0x110, Off: 0x2dde})
		o.WriteU16(battleAddr, uint16(original[0])|uint16(original[1])<<8)
		o.WriteU16(oracle.Addr{Seg: 0xf67, Off: 10}, uint16(original[2])|uint16(original[3])<<8)
		row := map[string]any{"case": sc, "before": before, "after": capture(), "events": events, "battle_calls": battleCalls, "roam_fixture_calls": choiceCalls, "random_input": randomInput, "error": fmt.Sprint(err), "original_battle_bytes": original, "stub_bytes": []byte{0xb8, byte(sc.Result), 0, 0xcb}}
		rows = append(rows, row)
		write(filepath.Join(dir, "receipt.json"), row)
		must(o.SaveStateFile(filepath.Join(dir, "after.state")))
		if err != nil || battleCalls != 1 {
			write(filepath.Join(*out, "incomplete.json"), rows)
			panic(fmt.Sprint("guard wrapper fixture failed ", sc.Name, " ", err, " calls ", battleCalls))
		}
	}
	write(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-original-guard-caller-controls", "rows": rows, "go_version": runtime.Version(), "player_path": false, "source_state_sha256": fmt.Sprintf("%x", sha256.Sum256(raw)), "limits": []string{"Direct caller fixtures; battle entry replaced by MOV AX,result / RETF and explicit survivors, not actual original combat.", "Confirmation, central tile result and loss roaming are explicit fixtures; no natural guard encounter or GUI claim.", "Ending guard kept alive; final-game transition is outside scope. All fixture code restored before after.state."}})
	fmt.Println("guard caller controls", len(rows))
}
