package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func rulesRuntimePaths(t *testing.T) (string, string, string) {
	t.Helper()
	root, batch, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_RULE_CALLS"), os.Getenv("EIGHTSWORD_RULE_OUT")
	if root == "" || batch == "" || out == "" {
		t.Skip("需要原版、受控helper來源與新輸出")
	}
	return root, batch, out
}
func TestBattleRulesOriginalHelpers(t *testing.T) {
	root, batch, out := rulesRuntimePaths(t)
	for _, side := range []string{"player", "enemy"} {
		for _, name := range []string{"front-ally", "alone", "rear-ally", "rear-target", "other-kind", "two-allies"} {
			for _, mode := range []string{"native", "formation"} {
				t.Run(side+"-"+name+"-"+mode, func(t *testing.T) {
					refMode := "baseline"
					if mode == "formation" {
						refMode = "formation"
					}
					source := filepath.Join(batch, side+"-"+name, refMode)
					raw, err := os.ReadFile(filepath.Join(source, "trace.json"))
					if err != nil {
						t.Fatal(err)
					}
					var trace struct {
						Steps    uint64
						Eligible bool
					}
					if err = json.Unmarshal(raw, &trace); err != nil {
						t.Fatal(err)
					}
					dir := filepath.Join(out, side+"-"+name+"-"+mode)
					if err = os.Mkdir(dir, 0755); err != nil {
						t.Fatal(err)
					}
					e, err := Open(Options{Root: root, Saves: filepath.Join(dir, "scratch"), BattleRules: mode})
					if err != nil {
						t.Fatal(err)
					}
					defer e.Close()
					if err = e.Oracle.LoadStateFile(filepath.Join(source, "start-call.state")); err != nil {
						t.Fatal(err)
					}
					if err = e.bindBattleRules(0x110, 0x110); err != nil {
						t.Fatal(err)
					}
					// This fixture enters a helper directly; natural wrapper lifetime is a GUI gate.
					e.rules.Active = true
					if err = e.Advance(trace.Steps); err != nil {
						t.Fatal(err)
					}
					final := filepath.Join(dir, "final.state")
					if err = e.Oracle.SaveStateFile(final); err != nil {
						t.Fatal(err)
					}
					got, err := os.ReadFile(final)
					if err != nil {
						t.Fatal(err)
					}
					want, err := os.ReadFile(filepath.Join(source, "final.state"))
					if err != nil {
						t.Fatal(err)
					}
					if !bytes.Equal(got, want) {
						t.Fatal("formal rules differ from original controlled helper")
					}
					info := e.BattleRulesStatus()
					if mode == "formation" {
						if info.Calls != 1 || info.Applied != boolRuleCount(trace.Eligible) {
							t.Fatal(info)
						}
					} else if info.Calls != 0 || info.Applied != 0 {
						t.Fatal(info)
					}
					data, _ := json.MarshalIndent(info, "", "  ")
					if err = os.WriteFile(filepath.Join(dir, "rules.json"), append(data, '\n'), 0644); err != nil {
						t.Fatal(err)
					}
				})
			}
		}
	}
}
func boolRuleCount(v bool) uint64 {
	if v {
		return 1
	}
	return 0
}
func TestBattleRulesFaultsAndAuto(t *testing.T) {
	root, batch, out := rulesRuntimePaths(t)
	for _, fault := range []string{"bytes", "mapping", "stack"} {
		t.Run(fault, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir(), BattleRules: "formation"})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if err = e.Oracle.LoadStateFile(filepath.Join(batch, "player-front-ally/formation/before-hook.state")); err != nil {
				t.Fatal(err)
			}
			if err = e.bindBattleRules(0x110, 0x110); err != nil {
				t.Fatal(err)
			}
			e.rules.Active = true
			switch fault {
			case "bytes":
				a := oracle.Addr{Seg: 0xf67, Off: 0x1560}
				e.Oracle.WriteU8(a, e.Oracle.Byte(a)^1)
			case "mapping":
				e.Oracle.WriteU16(oracle.Addr{Seg: 0x1e88, Off: 0x6fb6}, 6)
			case "stack":
				e.Oracle.SetRegs(oracle.CallRegs{BP: 4, SetBP: true})
			}
			before := filepath.Join(out, "fault-"+fault+"-before.state")
			after := filepath.Join(out, "fault-"+fault+"-after.state")
			if err = e.Oracle.SaveStateFile(before); err != nil {
				t.Fatal(err)
			}
			if err = e.Advance(1); err == nil {
				t.Fatal("fault did not stop")
			}
			if err = e.Oracle.SaveStateFile(after); err != nil {
				t.Fatal(err)
			}
			a, _ := os.ReadFile(before)
			b, _ := os.ReadFile(after)
			if !bytes.Equal(a, b) {
				t.Fatal("fault changed guest")
			}
		})
	}
	dir := t.TempDir()
	os.WriteFile(filepath.Join(dir, "gamedata.ay"), bytes.Repeat([]byte{7}, 2987), 0600)
	if err := writeRulesMarker(dir, "formation"); err != nil {
		t.Fatal(err)
	}
	e, err := Open(Options{Root: root, Saves: dir})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.BattleRulesMode() != "formation" {
		t.Fatal("auto did not restore rule")
	}
	explicit, err := Open(Options{Root: root, Saves: dir, BattleRules: "native"})
	if err != nil {
		t.Fatal(err)
	}
	defer explicit.Close()
	if explicit.BattleRulesMode() != "native" || !explicit.rules.persist {
		t.Fatal("explicit rule must replace the marker on a genuine save")
	}
}

func TestBattleTacticsOriginalHelpers(t *testing.T) {
	root, _, out := rulesRuntimePaths(t)
	controls := os.Getenv("EIGHTSWORD_TACTICS_HELPERS")
	if controls == "" {
		t.Skip("需要已驗雙側戰術helper控制")
	}
	out = filepath.Join(out, "tactics-helpers")
	if err := os.Mkdir(out, 0755); err != nil {
		t.Fatal(err)
	}
	for _, side := range []string{"player", "enemy"} {
		for _, name := range []string{"front-opposed", "rear-archer", "open-lane", "other-ranged", "combined", "other-kind", "rear-target", "threshold"} {
			for _, mode := range []string{"native", "formation", "tactics"} {
				t.Run(side+"-"+name+"-"+mode, func(t *testing.T) {
					label := side + "-" + name + "-" + mode
					source := filepath.Join(controls, label)
					raw, err := os.ReadFile(filepath.Join(source, "trace.json"))
					if err != nil {
						t.Fatal(err)
					}
					var trace struct {
						Steps               uint64
						Pressure, Formation bool
					}
					if err = json.Unmarshal(raw, &trace); err != nil {
						t.Fatal(err)
					}
					dir := filepath.Join(out, label)
					if err = os.Mkdir(dir, 0755); err != nil {
						t.Fatal(err)
					}
					e, err := Open(Options{Root: root, Saves: filepath.Join(dir, "scratch"), BattleRules: mode})
					if err != nil {
						t.Fatal(err)
					}
					defer e.Close()
					if err = e.Oracle.LoadStateFile(filepath.Join(source, "start-call.state")); err != nil {
						t.Fatal(err)
					}
					if err = e.bindBattleRules(0x110, 0x110); err != nil {
						t.Fatal(err)
					}
					e.rules.Active = true // Fixture is an isolated call; GUI covers natural wrapper entry.
					if err = e.Advance(trace.Steps); err != nil {
						t.Fatal(err)
					}
					if err = e.Oracle.SaveStateFile(filepath.Join(dir, "final.state")); err != nil {
						t.Fatal(err)
					}
					a, err := os.ReadFile(filepath.Join(dir, "final.state"))
					if err != nil {
						t.Fatal(err)
					}
					b, err := os.ReadFile(filepath.Join(source, "final.state"))
					if err != nil {
						t.Fatal(err)
					}
					if !bytes.Equal(a, b) {
						t.Fatal("tactics differs from original controlled helper")
					}
					info := e.BattleRulesStatus()
					suppressed := mode == "tactics" && trace.Pressure
					applied := mode != "native" && (trace.Formation || suppressed)
					if info.Suppressed != boolRuleCount(suppressed) || info.Applied != boolRuleCount(applied) {
						t.Fatal(info)
					}
					data, _ := json.MarshalIndent(info, "", "  ")
					if err = os.WriteFile(filepath.Join(dir, "rules.json"), append(data, '\n'), 0644); err != nil {
						t.Fatal(err)
					}
				})
			}
		}
	}
}

func TestBattleTacticsSourceFaults(t *testing.T) {
	root, _, out := rulesRuntimePaths(t)
	controls := os.Getenv("EIGHTSWORD_TACTICS_HELPERS")
	if controls == "" {
		t.Skip("需要戰術helper控制")
	}
	for _, name := range []string{"range", "duplicate", "unmapped"} {
		t.Run(name, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir(), BattleRules: "tactics"})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if err = e.Oracle.LoadStateFile(filepath.Join(controls, "player-front-opposed-tactics/before-hook.state")); err != nil {
				t.Fatal(err)
			}
			if err = e.bindBattleRules(0x110, 0x110); err != nil {
				t.Fatal(err)
			}
			e.rules.Active = true
			write := func(off, value uint16) { e.Oracle.WriteU16(oracle.Addr{Seg: 0x1e88, Off: off}, value) }
			want := ""
			switch name {
			case "range":
				write(0x6fc2, 6)
				want = "source-slot-mapping"
			case "duplicate":
				write(0x5706, 1)
				write(0x6fc4, 0)
				want = "source-duplicate-live-mapping"
			case "unmapped":
				write(0x6fc2, 5)
				want = "unmapped-live-source"
			}
			before, after := filepath.Join(out, "tactics-fault-"+name+"-before.state"), filepath.Join(out, "tactics-fault-"+name+"-after.state")
			if err = e.Oracle.SaveStateFile(before); err != nil {
				t.Fatal(err)
			}
			err = e.Advance(1)
			if err == nil || e.rules.Fault == nil || e.rules.Fault.Reason != want {
				t.Fatal("wrong fault", err, e.rules.Fault)
			}
			if err = e.Oracle.SaveStateFile(after); err != nil {
				t.Fatal(err)
			}
			a, _ := os.ReadFile(before)
			b, _ := os.ReadFile(after)
			if !bytes.Equal(a, b) {
				t.Fatal("fault changed guest")
			}
		})
	}
}

func TestBattleRulesAutomaticThreeModes(t *testing.T) {
	root, _, _ := rulesRuntimePaths(t)
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "gamedata.ay"), bytes.Repeat([]byte{7}, 2987), 0600); err != nil {
		t.Fatal(err)
	}
	for _, mode := range []string{"native", "formation", "tactics"} {
		if err := writeRulesMarker(dir, mode); err != nil {
			t.Fatal(err)
		}
		e, err := Open(Options{Root: root, Saves: dir})
		if err != nil {
			t.Fatal(err)
		}
		if e.BattleRulesMode() != mode || e.BattleRulesName() != battleRulesName(mode) {
			t.Fatal("auto mode", e.BattleRulesStatus())
		}
		e.Close()
	}
}
