// 030 DRAFT: disposable numerical candidate. No game, RAM, clock or RNG access.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
)

type scenario struct {
	ID, Label, Level, Side, Route                      string
	SourceKind, SourceSlot, SourceCount                uint16
	Front                                              [3]uint16
	TargetKind, TargetSlot, TargetCount, HP, RawAmount uint16
	BaselineLoss                                       *uint16 `json:",omitempty"`
}
type mode struct {
	ID, Label string
	Pressure  uint16
	Formation bool
}

var modes = []mode{{"native", "原版規則", 0, false}, {"formation", "現有結陣", 0, true}, {"tactics25", "戰術候選：減25%", 25, true}, {"tactics50", "戰術候選：減50%", 50, true}}

type result struct {
	Mode                                                string
	PressureEligible, PressureApplied, FormationApplied bool
	Raw, AfterPressure, Amount, Loss, Remaining         uint16
}

func calculate(s scenario, m mode) (result, error) {
	r := result{Mode: m.ID, Raw: s.RawAmount}
	if (s.Side != "player" && s.Side != "enemy") || s.SourceSlot >= 6 || s.TargetSlot >= 6 || s.SourceKind < 1 || s.SourceKind > 25 || s.TargetKind < 1 || s.TargetKind > 25 || s.SourceCount == 0 || s.TargetCount == 0 || s.HP == 0 {
		return r, fmt.Errorf("invalid typed scenario")
	}
	if s.Route != "normal" && s.Route != "ranged" && s.Route != "special" {
		return r, fmt.Errorf("unknown route")
	}
	if m.Pressure != 0 && m.Pressure != 25 && m.Pressure != 50 {
		return r, fmt.Errorf("unapproved candidate percentage")
	}
	r.PressureEligible = s.Route != "special" && s.SourceKind == 3 && s.SourceSlot < 3 && s.Front[s.SourceSlot] > 0
	r.AfterPressure = s.RawAmount
	if r.PressureEligible && m.Pressure > 0 {
		r.AfterPressure = uint16(uint32(s.RawAmount) * uint32(100-m.Pressure) / 100)
		r.PressureApplied = true
	}
	r.Amount = r.AfterPressure
	if m.Formation && s.Route != "special" && s.TargetKind == 1 && s.TargetSlot < 3 {
		for i, n := range s.Front {
			if i != int(s.TargetSlot) && n > 0 {
				r.FormationApplied = true
			}
		}
		if r.FormationApplied {
			r.Amount = uint16(uint32(r.Amount) * 80 / 100)
		}
	}
	if s.Route == "special" {
		r.Loss = min(r.Amount, s.TargetCount)
	} else {
		encoded := uint16(r.Amount/s.HP + 1)
		if encoded > 1 {
			r.Loss = encoded - 1
			if encoded >= s.TargetCount {
				r.Loss = s.TargetCount
			}
		}
	}
	r.Remaining = s.TargetCount - r.Loss
	return r, nil
}
func main() {
	input := flag.String("input", "", "fixed typed scenarios")
	out := flag.String("out", "", "new output JSON")
	flag.Parse()
	raw, err := os.ReadFile(*input)
	must(err)
	var cases []scenario
	must(json.Unmarshal(raw, &cases))
	rows := []map[string]any{}
	for _, s := range cases {
		values := []result{}
		for _, m := range modes {
			v, e := calculate(s, m)
			must(e)
			if m.ID == "native" && s.BaselineLoss != nil && v.Loss != *s.BaselineLoss {
				panic("accepted original baseline differs")
			}
			values = append(values, v)
		}
		rows = append(rows, map[string]any{"scenario": s, "results": values})
	}
	b, err := json.MarshalIndent(map[string]any{"status": "DRAFT-offline-candidate", "modes": modes, "rows": rows}, "", "  ")
	must(err)
	f, err := os.OpenFile(*out, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	must(err)
	_, err = f.Write(append(b, '\n'))
	must(err)
	must(f.Close())
	fmt.Printf("candidate calculations: %d\n", len(cases)*len(modes))
}
func must(e error) {
	if e != nil {
		panic(e)
	}
}
