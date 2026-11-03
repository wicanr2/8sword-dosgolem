package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func supportFixture(t *testing.T, code []byte, catalog game.OwnedCombatCatalog, ip uint16, value uint16) (*dg.Machine, *originalBattleSupport) {
	rows := [2][6]ArmyStack{{{"native:01", 30}, {"native:10", 1}}, {{"native:16", 35}}}
	m, a := actionFixture(t, code, catalog, rows)
	a.Casualties = &originalBattleCasualties{}
	r := &originalBattleRounds{Actions: a, Active: true, Rows: rows, Slots: a.Setup.Plan.Slots, Sorting: -1}
	copy(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
	p := &originalBattleSpells{Rounds: r, Rows: rows, Projected: r.Projected, Active: ip == 0x771, EntrySP: 0xee02, Consumed: true, Selector: 4}
	s := &originalBattleSupport{Spells: p, Mask: 63}
	p.Support = s
	r.Spells = p
	a.Rounds = r
	c := m.CPU
	c.IP = ip
	c.R[dg.BP] = 0xee00
	c.R[dg.BX] = 0
	for i := range s.Counters {
		s.Counters[i] = value
		m.Write16(0x1e880+0x8e46+uint32(i*2), value)
	}
	m.Write16(0x1e880+0xedf6, 0)
	m.Write16(0x1e880+0xedf4, 0)
	ret := uint16(0x2151)
	if ip == 0x2134 {
		ret = 0x20aa
		m.Write16(0x1e880+0xedfc, 0)
	}
	m.Write16(0x1e880+0xee02, ret)
	m.Write16(0x1e880+0xee04, 0xf67)
	return m, s
}

func TestOriginalSupportModels(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	controls := []map[string]any{}
	for _, ip := range []uint16{0x2134, 0x771, 0x1a11, 0x1c5e, 0x1a25, 0x1c7f} {
		for _, value := range []uint16{0, 1, 2, 15, 16, 32767, 32768, 65534} {
			if value == 0 && (ip == 0x1a25 || ip == 0x1c7f) {
				continue
			}
			m, s := supportFixture(t, code, catalog, ip, value)
			n := dg.New()
			copy(n.Mem, m.Mem)
			n.CPU.R = m.CPU.R
			n.CPU.Seg = m.CPU.Seg
			n.CPU.Flags = m.CPU.Flags
			n.CPU.IP = ip
			if err := n.Step(); err != nil {
				t.Fatal(err)
			}
			if handled, er := s.counter(m, ip); er != nil || !handled {
				t.Fatal("counter", ip, value, er)
			}
			if !bytes.Equal(n.Mem, m.Mem) || n.CPU.R != m.CPU.R || n.CPU.IP != m.CPU.IP || n.CPU.Flags != m.CPU.Flags {
				t.Fatal("original/Go counter differs", ip, value, n.CPU.Flags, m.CPU.Flags)
			}
			controls = append(controls, map[string]any{"ip": ip, "before": value, "after": s.Counters[0], "flags": m.CPU.Flags})
		}
	}
	clones := []map[string]any{}
	for _, kind := range []uint16{10, 12} {
		for _, count := range []uint32{1, 30, 49, 50, 99, 100, 199, 200, 299, 300, 399, 400} {
			scaled, after, factor, er := originalClonePlan(kind, count)
			if er != nil {
				t.Fatal(er)
			}
			clones = append(clones, map[string]any{"kind": kind, "count": count, "scaled": scaled, "after": after, "factor": factor})
		}
	}
	for _, sc := range []struct {
		Kind  uint16
		Count uint32
	}{{0, 30}, {10, 0}, {10, 32768}, {10, 7000}} {
		if _, _, _, er := originalClonePlan(sc.Kind, sc.Count); er == nil {
			t.Fatal("unsafe clone", sc)
		}
	}
	refusals := []string{"source", "segment", "counter-projection", "frame", "index", "map", "underflow", "overflow"}
	for _, name := range refusals {
		ip, value := uint16(0x1a25), uint16(1)
		if name == "overflow" {
			ip, value = 0x771, 65535
		}
		if name == "underflow" {
			value = 0
		}
		m, s := supportFixture(t, code, catalog, ip, value)
		switch name {
		case "source":
			m.Mem[0xf670+0x19ac] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "counter-projection":
			m.Write16(0x1e880+0x8e46, 2)
		case "frame":
			m.Write16(0x1e880+0xee02, 0)
		case "index":
			m.CPU.R[dg.BX] = 12
		case "map":
			m.Write16(0x1e880+0xedf6, 6)
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, at := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		counts := s.Counters
		if _, er := s.counter(m, ip); er == nil {
			t.Fatal("unsafe counter", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || at != m.CPU.IP || counts != s.Counters {
			t.Fatal("counter refusal changed state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "support-models.json"), map[string]any{"counter_controls": controls, "clone_models": clones, "clone_refusals": 4, "counter_refusals": len(refusals)})
}

func TestOriginalBattleSupport(t *testing.T) {
	work, root, catalog := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	parent := filepath.Join(work, "support-r1")
	if err := os.MkdirAll(parent, 0700); err != nil {
		t.Fatal(err)
	}
	for _, sc := range []struct {
		Name     string
		Selector int
		Kind     uint16
		HD       bool
		Cancel   string
	}{
		{"freeze-hd", 4, 12, true, ""}, {"clone-hd", 6, 10, true, ""}, {"clone-no-growth-hd", 6, 12, true, ""}, {"clone-native", 6, 10, false, ""}, {"clone-space", 6, 10, true, "target-space"},
		{"clone-skip-hd", 6, 12, true, ""},
	} {
		t.Run(sc.Name, func(t *testing.T) {
			must := func(er error) {
				t.Helper()
				if er != nil {
					t.Fatal(er)
				}
			}
			var reference map[string]any
			for mode := 0; mode < 2; mode++ {
				dir := filepath.Join(parent, fmt.Sprintf("%s-mode-%d", sc.Name, mode))
				must(os.Mkdir(dir, 0700))
				e := setupCold(t, root, assets, dir, sc.HD)
				player := [6]ArmyStack{{"native:01", 30}, {fmt.Sprintf("native:%02d", sc.Kind), 2}}
				if sc.Name == "clone-skip-hd" {
					player[0].Count = 50
				}
				e.Oracle.OnCall(oracle.Far(0xf67, 0x1daa), func(o *oracle.Oracle) {
					o.WriteU16(oracle.Far(0x1e88, 0x26aa), 1)
					o.WriteU16(oracle.Far(0x1e88, 0x26b0), 2)
					for i := uint16(0); i < 8; i++ {
						o.WriteU16(oracle.Far(0x1e88, 0x2aa8+i*2), 3)
					}
				})
				var support *originalBattleSupport
				var rounds *originalBattleRounds
				if mode == 0 {
					e.Oracle.OnCall(oracle.Far(0x110, 0x3365), func(o *oracle.Oracle) {
						for i, row := range player {
							p := catalog.Profiles[row.Unit]
							o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
							o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(row.Count))
						}
					})
				} else {
					_, er := installOriginalArmyProjection(e, catalog, player)
					must(er)
					setup, er := installOriginalBattleSetup(e, catalog, nil)
					must(er)
					a, er := installOriginalBattleActions(e, setup, true)
					must(er)
					rounds, er = installOriginalBattleRounds(e, a)
					must(er)
					p, er := installOriginalBattleSpells(e, rounds)
					must(er)
					support, er = installOriginalBattleSupport(e, p)
					must(er)
					p.Hold = true
				}
				err := spellEncounter(t, e, sc.Selector, sc.Cancel, mode == 1)
				if !errors.Is(err, errOriginalSpellHeld) {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
					setupWrite(t, filepath.Join(dir, "failed.json"), map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs(), "support": support})
					t.Fatal("support", err, e.Oracle.Regs())
				}
				frame := e.Frame()
				f, er := os.Create(filepath.Join(dir, "frame.png"))
				must(er)
				must(png.Encode(f, frame))
				must(f.Close())
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
				row := map[string]any{"name": sc.Name, "selector": sc.Selector, "kind": sc.Kind, "hd": sc.HD, "cancel": sc.Cancel, "mode": mode, "units_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "hp_hex": fmt.Sprintf("%x", append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)), "counters_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e46), 12)), "charges_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x2aa8), 16)), "seed": originalSeed(e.Oracle), "frame_sha256": contentSHA(frame.Pix), "controlled_fixture": true}
				if mode == 0 {
					reference = row
				} else {
					for _, key := range []string{"units_hex", "hp_hex", "counters_hex", "charges_hex", "seed", "frame_sha256"} {
						if reference[key] != row[key] {
							t.Fatal("original/Go support differs", key, reference[key], row[key])
						}
					}
					row["records"] = support.Records
					row["rows"] = rounds.Rows
					row["counters"] = support.Counters
					row["growth"] = support.Growth
					row["counter_reads"] = support.Reads
					row["counter_consumes"] = support.Consumes
					before := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
					cycles := e.Oracle.Cycles()
					for n := 0; n < 5; n++ {
						if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalSpellHeld) {
							t.Fatal(er)
						}
					}
					if !bytes.Equal(before, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || cycles != e.Oracle.Cycles() {
						t.Fatal("support hold changed state")
					}
				}
				setupWrite(t, filepath.Join(dir, "receipt.json"), row)
				e.Close()
			}
		})
		if t.Failed() {
			break
		}
	}
}

func TestOriginalSupportWorld(t *testing.T) {
	t.Run("clone", func(t *testing.T) {
		originalSpellWorld(t, "clone-world-r1", 6, [6]ArmyStack{{"native:01", 40}, {"native:10", 1}, {"openkb:wolf", 1}, {"openkb:arcr", 1}}, true)
	})
	if t.Failed() {
		return
	}
	t.Run("freeze", func(t *testing.T) {
		originalSpellWorld(t, "freeze-world-r1", 4, [6]ArmyStack{{"native:01", 74}, {"native:12", 2}, {"openkb:wolf", 1}, {"openkb:arcr", 1}}, true)
	})
}

func TestOriginalSupportGrowth(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"valid", "unrecorded", "identity", "uncommitted", "excess", "selector", "legacy"} {
		_, s := supportFixture(t, code, catalog, 0x771, 1)
		r := s.Spells.Rounds
		r.Done = true
		r.Released = true
		r.Rows[0][0].Count = 60
		c := &originalCloneRecord{Unit: "native:01", Raw: 0, Before: 30, After: 60, Updates: 1}
		s.Growth[0] = 30
		s.Records = []originalSupportRecord{{Selector: 6, Clone: c}}
		x := &originalArmyProjection{Input: r.Actions.Setup.Plan.Rows[0], Catalog: catalog, Rounds: r}
		switch name {
		case "unrecorded":
			s.Records = nil
		case "identity":
			c.Unit = "native:10"
		case "uncommitted":
			c.Updates = 0
		case "excess":
			r.Rows[0][0].Count = 61
		case "selector":
			s.Records[0].Selector = 4
		case "legacy":
			x.Rounds = nil
		}
		if name != "legacy" {
			got, er := x.captureRounds()
			if (er == nil) != (name == "valid") {
				t.Fatal("growth admission", name, got, er)
			}
		}
		encoded, er := originalArmyProjectionBytes(r.Rows[0], catalog)
		if er != nil {
			t.Fatal(er)
		}
		got, er := x.capture(encoded[:])
		if (er == nil) != (name == "valid") {
			t.Fatal("native growth admission", name, got, er)
		}
	}
	setupWrite(t, filepath.Join(work, "support-growth.json"), map[string]any{"valid": 1, "refusals": 6, "native_and_owned_returns": true})
}
func TestOriginalCloneGuards(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"source", "segment", "frame", "projection", "index", "display", "committed", "inactive"} {
		m, s := supportFixture(t, code, catalog, 0x920, 1)
		p := s.Spells
		p.Active = true
		p.Selector = 6
		m.CPU.R[dg.AX] = 30
		s.Clone = &originalCloneRecord{Unit: "native:01", Before: 30, After: 60, Planned: []uint16{30, 31}}
		switch name {
		case "source":
			m.Mem[0xf670+0x334] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "frame":
			m.CPU.R[dg.BP]--
		case "projection":
			m.Write16(0x1e880+0x56ea, 29)
		case "index":
			m.CPU.R[dg.BX] = 24
		case "display":
			m.CPU.R[dg.AX] = 31
		case "committed":
			s.Clone.Updates = 1
		case "inactive":
			p.Active = false
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		rows := p.Rows
		growth := s.Growth
		if _, er := s.cloneWrite(m); er == nil {
			t.Fatal("unsafe clone write", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP || rows != p.Rows || growth != s.Growth || len(s.Clone.Display) != 0 {
			t.Fatal("clone refusal changed state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "support-clone-guards.json"), map[string]any{"refusals": 8, "state_unchanged": true})
}
