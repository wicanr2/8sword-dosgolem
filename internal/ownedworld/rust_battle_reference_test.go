package ownedworld

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func rustRows(rows [6]ArmyStack) string {
	parts := []string{}
	for _, row := range rows {
		id := row.Unit
		if id == "" {
			id = "-"
		}
		parts = append(parts, fmt.Sprintf("%s=%d", id, row.Count))
	}
	return strings.Join(parts, ",")
}
func rustSlots(slots [6]uint16) string {
	return fmt.Sprintf("%d,%d,%d,%d,%d,%d", slots[0], slots[1], slots[2], slots[3], slots[4], slots[5])
}
func rustHP(hp [6]uint64) string {
	return fmt.Sprintf("%d,%d,%d,%d,%d,%d", hp[0], hp[1], hp[2], hp[3], hp[4], hp[5])
}

// Migration reference only; these are the existing production Go planners.
func TestRustBattleModelReference(t *testing.T) {
	output := os.Getenv("EIGHTSWORD_RUST_BATTLE_MODELS")
	if output == "" {
		t.Skip("explicit Rust migration reference")
	}
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	var orders [4][3]byte
	var flat []string
	for i, base := range []int{0x708a, 0x708e, 0x7092, 0x7096} {
		copy(orders[i][:], code[0x1d780+base:0x1d780+base+3])
		for _, v := range orders[i] {
			flat = append(flat, fmt.Sprint(v))
		}
	}
	orderText := strings.Join(flat, ",")
	var out strings.Builder
	out.WriteString("# Go production planner reference, not a save format\n")
	emitSetup := func(rows [2][6]ArmyStack) {
		plan, er := planOriginalBattleSetup(catalog, rows)
		fmt.Fprintf(&out, "SETUP\t%s\t%s\t", rustRows(rows[0]), rustRows(rows[1]))
		if er != nil {
			out.WriteString("ERR\n")
			return
		}
		fmt.Fprintf(&out, "%s\t%s\t%s\t%s\n", rustSlots(plan.Slots[0]), rustSlots(plan.Slots[1]), rustHP(plan.HP[0]), rustHP(plan.HP[1]))
	}
	emitSetup([2][6]ArmyStack{})
	for n := 1; n <= 25; n++ {
		emitSetup([2][6]ArmyStack{{{fmt.Sprintf("native:%02d", n), 30}}})
	}
	for _, id := range openKBArtIDs {
		emitSetup([2][6]ArmyStack{{{id, ^uint32(0)}}})
	}
	emitSetup([2][6]ArmyStack{{{"native:01", 30}, {"native:10", 2}, {"native:03", 10}, {"native:12", 2}, {"openkb:arcr", 20}, {"native:25", 1}}, {{"native:10", 2}, {"native:12", 2}, {"native:24", 10}}})
	emitSetup([2][6]ArmyStack{{{"native:01", 30}, {"native:01", 1}}})
	emitSetup([2][6]ArmyStack{{{"native:01", 0}}})
	for mask := 0; mask < 64; mask++ {
		rows := [6]ArmyStack{{"native:01", 1}, {"native:03", 1}, {"native:10", 1}, {"native:12", 1}, {"openkb:arcr", 1}, {"native:25", 1}}
		for raw := range rows {
			if mask&(1<<raw) == 0 {
				rows[raw].Count = 0
			}
		}
		for _, caster := range []bool{false, true} {
			slots := [6]uint16{0, 1, 2, 3, 4, 5}
			after, _, er := roundSortPlan(catalog, rows, slots, orders, caster)
			if er != nil {
				t.Fatal(er)
			}
			fmt.Fprintf(&out, "SORT\t%s\t%s\t%s\t%t\t%s\n", rustRows(rows), rustSlots(slots), orderText, caster, rustSlots(after))
		}
	}
	for mask := 0; mask < 8; mask++ {
		var rows [6]ArmyStack
		for raw := 0; raw < 3; raw++ {
			if mask&(1<<raw) != 0 {
				rows[raw] = ArmyStack{fmt.Sprintf("native:%02d", raw+1), 30}
			}
		}
		for from := 0; from < 3; from++ {
			for target := 0; target < 6; target++ {
				slots := [6]uint16{0, 1, 2, 3, 4, 5}
				after, er := roundMotionPlanForTarget(rows, slots, from, target)
				result := "ERR"
				if er == nil {
					result = rustSlots(after)
				}
				fmt.Fprintf(&out, "MOTION\t%s\t%s\t%d\t%d\t%s\n", rustRows(rows), rustSlots(slots), from, target, result)
			}
		}
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
