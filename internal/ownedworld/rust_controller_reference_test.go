package ownedworld

import (
	"errors"
	"fmt"
	"github.com/wicanr2/dosgolem/oracle"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRustControllerReference(t *testing.T) {
	output := os.Getenv("EIGHTSWORD_RUST_CONTROLLER_REFERENCE")
	if output == "" {
		t.Skip("explicit native-controller reference")
	}
	work, root, catalog := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("source assets")
	}
	var out strings.Builder
	out.WriteString("# Original-interface source selection and ordinary actions; target choice is controlled\n")
	for i, player := range [][6]ArmyStack{{{"openkb:wolf", 1000}, {"openkb:arcr", 10}}, {{"openkb:wolf", 2}, {"native:01", 30}}, {{"openkb:wolf", 2}, {"native:01", 30}}, {{"openkb:wolf", 2}, {"openkb:arcr", 2}}} {
		dir := filepath.Join(work, fmt.Sprintf("controller-r2-%d", i))
		if err := os.Mkdir(dir, 0700); err != nil {
			t.Fatal(err)
		}
		e := setupCold(t, root, assets, dir, true)
		_, err := installOriginalArmyProjectionMode(e, catalog, player, true)
		if err != nil {
			t.Fatal(err)
		}
		s, err := installOriginalBattleSetup(e, catalog, &player)
		if err != nil {
			t.Fatal(err)
		}
		a, err := installOriginalBattleActions(e, s, true)
		if err != nil {
			t.Fatal(err)
		}
		r, err := installOriginalBattleRounds(e, a)
		if err != nil {
			t.Fatal(err)
		}
		first := uint16(65535)
		started := false
		e.Oracle.OnCall(oracle.Far(0xf67, 8), func(o *oracle.Oracle) { first = o.Word(oracle.Far(o.Regs().SS, o.Regs().SP+6)) })
		start := func() {
			if started {
				return
			}
			started = true
			fmt.Fprintf(&out, "START\t%d\t%d\t%s\t%s\n", i, first, rustRows(r.Rows[0]), rustRows(r.Rows[1]))
		}
		offer := func(o *oracle.Oracle, side int, slot uint16) {
			start()
			var pending [6]uint16
			for n := range pending {
				pending[n] = o.Word(oracle.Far(0x1e88, uint16(0x8e46+side*50+n*2)))
			}
			fmt.Fprintf(&out, "OFFER\t%d\t%d\t%d\t%s\t%s\t%s\t%s\t%s\n", side, slot, r.Slots[side][slot], rustSlots(r.Slots[0]), rustSlots(r.Slots[1]), rustSlots(pending), rustHP(r.HP[0]), rustHP(r.HP[1]))
		}
		e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(o *oracle.Oracle) {
			if !r.Active || r.Actions.Casualties.Started {
				return
			}
			slot := o.Word(oracle.Far(o.Regs().SS, o.Regs().BP-10))
			if slot >= 6 {
				t.Fatal("picker source slot", slot)
			}
			offer(o, 0, slot)
		})
		for _, ip := range []uint16{0x3930, 0x3240, 0x484c, 0x4626} {
			ip := ip
			e.Oracle.OnCall(oracle.Far(0xf67, ip), func(o *oracle.Oracle) {
				if !r.Active || r.Actions.Casualties.Started {
					return
				}
				side := 0
				if ip == 0x484c || ip == 0x4626 {
					side = 1
				}
				ss, ts := o.Word(oracle.Far(o.Regs().SS, o.Regs().SP+4)), o.Word(oracle.Far(o.Regs().SS, o.Regs().SP+6))
				if ss >= 6 || ts >= 6 {
					t.Fatal("action slots", ss, ts)
				}
				if side == 1 {
					offer(o, side, ss)
				}
				fmt.Fprintf(&out, "ATTACK\t%d\n", ts)
			})
		}
		err = roundEncounterObserved(t, e, i == 1 || i == 3, []bool{i == 2}, func(o *oracle.Oracle) {
			if o.Regs().AX == 0x0efe {
				out.WriteString("SKIP\n")
			} else if o.Byte(oracle.Far(0x1e88, 0x7138)) == 1 {
				out.WriteString("RETREAT\n")
			}
		})
		if !errors.Is(err, errOriginalBattleRoundsHeld) {
			t.Fatal("controller reference", i, err, e.Oracle.Regs())
		}
		if !started {
			start()
		}
		fmt.Fprintf(&out, "END\t%s\t%s\t%s\t%s\t%s\n", r.Result, rustRows(r.Rows[0]), rustRows(r.Rows[1]), rustSlots(r.Slots[0]), rustSlots(r.Slots[1]))
		setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"case": i, "first": first, "history": r.History, "rows": r.Rows, "slots": r.Slots, "HP": r.HP, "sort_calls": r.SortCalls, "result": r.Result, "seed_after": originalSeed(e.Oracle), "initial_seed": 0x12345678, "army_fixture": true, "controlled_target_inputs": true})
		e.Close()
	}
	f, err := os.OpenFile(output, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
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
