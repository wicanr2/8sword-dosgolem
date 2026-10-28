package eightsword

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

func battleAIRuntimePaths(t *testing.T) (string, string, string) {
	t.Helper()
	root, batch, out := os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_POLICY_TEST_BATCH"), os.Getenv("EIGHTSWORD_AI_ENGINE_OUT")
	if root == "" || batch == "" || out == "" {
		t.Skip("需要固定原版、已驗候選資料與新輸出目錄")
	}
	return root, batch, out
}
func TestBattleAIEngineMatchesAcceptedTargets(t *testing.T) {
	root, batch, out := battleAIRuntimePaths(t)
	names := []string{"normal-locked", "normal-choice", "normal-rear-only", "front-ranged-mixed", "rear-ranged-mixed", "special0-choice", "special2-choice", "special5-empty-original"}
	for _, name := range names {
		t.Run(name, func(t *testing.T) {
			dir := "ai-policy-r1"
			if name == "special5-empty-original" {
				dir = "ai-policy-extra-r2"
			}
			source := filepath.Join(batch, dir, name)
			for _, mode := range []string{"native", "target"} {
				t.Run(mode, func(t *testing.T) {
					reference := "baseline"
					if mode == "target" {
						reference = "override"
					}
					raw, err := os.ReadFile(filepath.Join(source, reference, "trace.json"))
					if err != nil {
						t.Fatal(err)
					}
					var trace struct {
						ExecutorStack []uint16
						HookIP        uint16
						EndStep       uint64
						StartStep     uint64
						AfterUnits    []uint16
						Changes       []struct {
							Phase                     string
							Segment, Offset, Old, New uint16
							Step                      uint64
						}
					}
					if err = json.Unmarshal(raw, &trace); err != nil {
						t.Fatal(err)
					}
					output := filepath.Join(out, name+"-"+mode)
					if err = os.Mkdir(output, 0755); err != nil {
						t.Fatal(err)
					}
					e, err := Open(Options{Root: root, Saves: filepath.Join(output, "scratch"), BattleAI: mode})
					if err != nil {
						t.Fatal(err)
					}
					defer e.Close()
					if err = e.Oracle.LoadStateFile(filepath.Join(batch, "ai-observation-r1/input-multi-r1/choi-hd-r1/multi-ready-before.state")); err != nil {
						t.Fatal(err)
					}
					if mode == "target" {
						err = e.bindBattleAI(0x110, 0x110)
					}
					if err != nil {
						t.Fatal(err)
					}
					if mode == "native" && e.battleAI != nil {
						t.Fatal("native installed target controller")
					}
					fixtureDone, dispatchDone := false, false
					e.Oracle.OnCall(oracle.Addr{Seg: 0xf67, Off: 0x216a}, func(o *oracle.Oracle) {
						if fixtureDone {
							return
						}
						fixtureDone = true
						for _, c := range trace.Changes {
							if c.Phase == "fixture" {
								if o.Steps() != c.Step || o.Word(oracle.Addr{Seg: c.Segment, Off: c.Offset}) != c.Old {
									t.Fatal("fixture source condition changed")
								}
								o.WriteU16(oracle.Addr{Seg: c.Segment, Off: c.Offset}, c.New)
							}
						}
					})
					e.Oracle.OnCall(oracle.Addr{Seg: 0xf67, Off: 0xd88}, func(o *oracle.Oracle) {
						if dispatchDone {
							return
						}
						dispatchDone = true
						for _, c := range trace.Changes {
							if c.Phase == "dispatch" {
								if o.Steps() != c.Step || o.Word(oracle.Addr{Seg: c.Segment, Off: c.Offset}) != c.Old {
									t.Fatal("dispatch source condition changed")
								}
								o.WriteU16(oracle.Addr{Seg: c.Segment, Off: c.Offset}, c.New)
							}
						}
					})
					observed := false
					e.Oracle.OnCall(oracle.Addr{Seg: 0xf67, Off: trace.HookIP}, func(*oracle.Oracle) {
						if observed {
							return
						}
						if name == "special5-empty-original" {
							r := e.Oracle.Regs()
							guard := e.Oracle.Word(oracle.Addr{Seg: r.DS, Off: 0x6fb4 + r.DX*2})
							if e.Oracle.Word(oracle.Addr{Seg: r.DS, Off: 0x56ea + guard*4}) == 0 {
								return
							}
						}
						observed = true
						if err = e.Oracle.SaveStateFile(filepath.Join(output, "after-decision.state")); err != nil {
							t.Fatal(err)
						}
					})
					nextKey := 0
					for nextKey < 6 && trace.StartStep+uint64(nextKey)*2000000 < e.Oracle.Steps() {
						nextKey++
					}
					e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
						if nextKey < 6 && o.Steps() >= trace.StartStep+uint64(nextKey)*2000000 {
							o.PressScan(" ")
							nextKey++
						}
						return nil
					})
					referenceEngine, err := Open(Options{Root: root, Saves: t.TempDir()})
					if err != nil {
						t.Fatal(err)
					}
					if err = referenceEngine.Oracle.LoadStateFile(filepath.Join(source, reference, "final.state")); err != nil {
						t.Fatal(err)
					}
					returnRegs := referenceEngine.Oracle.Regs()
					referenceEngine.Close()
					t.Logf("source return CS:IP=%04X:%04X SS:SP=%04X:%04X; recorded executor return=%04X:%04X", returnRegs.CS, returnRegs.IP, returnRegs.SS, returnRegs.SP, trace.ExecutorStack[1], trace.ExecutorStack[0])
					err = e.battleAIRun(func() error {
						return e.Oracle.RunUntil(oracle.NewCond("original full return boundary", func(o *oracle.Oracle) bool {
							r := o.Regs()
							return r.CS == returnRegs.CS && r.IP == returnRegs.IP && r.SS == returnRegs.SS && r.SP == returnRegs.SP
						}), oracle.Budget(40000000))
					})
					if err != nil {
						t.Fatal(err)
					}
					if !observed || e.Oracle.Steps() != trace.EndStep {
						t.Fatalf("effect boundary: observed=%v steps=%d want=%d ip=%v ai=%+v", observed, e.Oracle.Steps(), trace.EndStep, e.Oracle.IP(), e.BattleAIStatus())
					}
					if err = e.Oracle.SaveStateFile(filepath.Join(output, "final.state")); err != nil {
						t.Fatal(err)
					}
					for _, filename := range []string{"after-decision.state", "final.state"} {
						actual, err := os.ReadFile(filepath.Join(output, filename))
						if err != nil {
							t.Fatal(err)
						}
						expected, err := os.ReadFile(filepath.Join(source, reference, filename))
						if err != nil {
							t.Fatal(err)
						}
						if !bytes.Equal(actual, expected) {
							t.Fatalf("%s differs from accepted original executor", filename)
						}
					}
					info := e.BattleAIStatus()
					if info.Fault != nil {
						t.Fatal(info.Fault)
					}
					if mode == "target" && (!info.Bound || info.Decisions != 1) {
						t.Fatalf("target hook not exercised: %+v", info)
					}
					metadata := map[string]any{"case": name, "mode": mode, "steps": e.Oracle.Steps(), "reference": filepath.Join(dir, name, reference), "battle_ai": info, "same_after_decision_state": true, "same_final_state": true}
					data, err := json.MarshalIndent(metadata, "", "  ")
					if err != nil {
						t.Fatal(err)
					}
					if err = os.WriteFile(filepath.Join(output, "receipt.json"), append(data, '\n'), 0644); err != nil {
						t.Fatal(err)
					}
				})
			}
		})
	}
}
func TestBattleAIEngineModesAndFaults(t *testing.T) {
	root, batch, out := battleAIRuntimePaths(t)
	input := filepath.Join(batch, "ai-policy-r1/front-ranged-mixed/baseline/before-decision.state")
	for _, fault := range []string{"entry-bytes", "mapping", "stack"} {
		t.Run(fault, func(t *testing.T) {
			e, err := Open(Options{Root: root, Saves: t.TempDir(), BattleAI: "target"})
			if err != nil {
				t.Fatal(err)
			}
			defer e.Close()
			if err = e.Oracle.LoadStateFile(input); err != nil {
				t.Fatal(err)
			}
			if err = e.bindBattleAI(0x110, 0x110); err != nil {
				t.Fatal(err)
			}
			switch fault {
			case "entry-bytes":
				a := oracle.Addr{Seg: 0xf67, Off: 0x16e7}
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
				t.Fatal("fault changed guest before rejection")
			}
		})
	}
	e, err := Open(Options{Root: root, Saves: t.TempDir()})
	if err != nil {
		t.Fatal(err)
	}
	defer e.Close()
	if e.BattleAIMode() != "native" || e.battleAI != nil {
		t.Fatal("default changed")
	}
	if err = e.SetBattleAI("unknown"); err == nil || e.battleAI != nil {
		t.Fatal("unknown mode accepted")
	}
	if err = e.Oracle.LoadStateFile(input); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 3; i++ {
		if err = e.SetBattleAI("target"); err != nil {
			t.Fatal(err)
		}
		if err = e.SetBattleAI("native"); err != nil {
			t.Fatal(err)
		}
	}
	if err = e.SetBattleAI("target"); err != nil {
		t.Fatal(err)
	}
	if err = e.bindBattleAI(0x110, 0x110); err != nil {
		t.Fatal(err)
	}
	if err = e.Advance(1); err != nil {
		t.Fatal(err)
	}
	if e.BattleAIStatus().Decisions != 1 {
		t.Fatal("toggle registered duplicate hooks")
	}
}
