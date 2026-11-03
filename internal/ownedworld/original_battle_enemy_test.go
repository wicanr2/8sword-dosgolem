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

func enemyFixture(t *testing.T, code []byte, catalog game.OwnedCombatCatalog, ip, value uint16) (*dg.Machine, *originalBattleEnemy) {
	rows := [2][6]ArmyStack{{{"native:01", 70}, {"native:06", 30}}, {{"native:16", 10}, {"native:12", 50}}}
	m, a := actionFixture(t, code, catalog, rows)
	a.Casualties = &originalBattleCasualties{}
	r := &originalBattleRounds{Actions: a, Rows: rows, Slots: a.Setup.Plan.Slots, Active: true, Sorting: -1}
	copy(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
	a.Rounds = r
	s := &originalBattleEnemy{Rounds: r, Rows: rows, Projected: r.Projected, Mask: 63, EntrySP: 0xee02, Active: ip == 0xfa9, Record: originalEnemySpecialRecord{Selector: 4}}
	r.EnemySpells = s
	c := m.CPU
	c.IP = ip
	c.R[dg.BP] = 0xee00
	c.R[dg.BX] = 0
	for i := range s.Counters {
		s.Counters[i] = value
		m.Write16(0x1e880+0x8e78+uint32(i*2), value)
	}
	ret := uint16(0x219a)
	if ip == 0x2184 {
		ret = 0x20dc
	}
	m.Write16(0x1e880+0xee02, ret)
	m.Write16(0x1e880+0xee04, 0xf67)
	m.Write16(0x1e880+0xedfc, 0)
	m.Write16(0x1e880+0xedfa, 0)
	m.Write16(0x1e880+0xedf4, 0)
	return m, s
}
func TestOriginalEnemyModels(t *testing.T) {
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
	for _, ip := range []uint16{0x2184, 0xfa9, 0x165b, 0x187c, 0x1699, 0x189d} {
		for _, value := range []uint16{0, 1, 2, 15, 16, 32767, 32768, 65534} {
			if value == 0 && (ip == 0x1699 || ip == 0x189d) {
				continue
			}
			m, s := enemyFixture(t, code, catalog, ip, value)
			n := dg.New()
			copy(n.Mem, m.Mem)
			n.CPU.R = m.CPU.R
			n.CPU.Seg = m.CPU.Seg
			n.CPU.Flags = m.CPU.Flags
			n.CPU.IP = ip
			if er := n.Step(); er != nil {
				t.Fatal(er)
			}
			if handled, er := s.counter(m, ip); er != nil || !handled {
				t.Fatal("enemy counter", ip, value, er)
			}
			if !bytes.Equal(n.Mem, m.Mem) || n.CPU.R != m.CPU.R || n.CPU.IP != m.CPU.IP || n.CPU.Flags != m.CPU.Flags {
				t.Fatal("native/Go enemy counter", ip, value, n.CPU.Flags, m.CPU.Flags)
			}
			controls = append(controls, map[string]any{"ip": ip, "before": value, "after": s.Counters[0], "flags": m.CPU.Flags})
		}
	}
	models := []map[string]any{}
	for _, kind := range []uint16{10, 12} {
		for _, selector := range []int{0, 1, 2, 3, 5, 7} {
			for _, count := range []uint32{1, 35, 49, 50, 69} {
				amount, er := originalEnemyAmount(selector, kind, count)
				if er != nil {
					t.Fatal(er)
				}
				models = append(models, map[string]any{"selector": selector, "kind": kind, "before": count, "amount": amount, "after": count - min(count, uint32(amount))})
			}
		}
	}
	if amount, er := originalEnemyAmount(5, 12, 0); er != nil || amount != 1 {
		t.Fatal("original empty shifted target", amount, er)
	}
	for _, sc := range []struct {
		Selector int
		Kind     uint16
		Count    uint32
	}{{4, 12, 30}, {6, 12, 30}, {0, 0, 30}, {0, 12, 0}, {0, 12, 32768}, {7, 12, 20000}} {
		if _, er := originalEnemyAmount(sc.Selector, sc.Kind, sc.Count); er == nil {
			t.Fatal("unsafe enemy model", sc)
		}
	}
	refusals := []string{"source", "segment", "projection", "frame", "index", "map", "underflow", "overflow"}
	for _, name := range refusals {
		ip, value := uint16(0x1699), uint16(1)
		if name == "overflow" {
			ip, value = 0xfa9, 65535
		}
		if name == "underflow" {
			value = 0
		}
		m, s := enemyFixture(t, code, catalog, ip, value)
		switch name {
		case "source":
			m.Mem[0xf670+0x15fc] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "projection":
			m.Write16(0x1e880+0x8e78, 2)
		case "frame":
			m.Write16(0x1e880+0xee02, 0)
		case "index":
			m.CPU.R[dg.BX] = 12
		case "map":
			m.Write16(0x1e880+0xedfa, 6)
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, at := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		counts := s.Counters
		if _, er := s.counter(m, ip); er == nil {
			t.Fatal("unsafe enemy counter", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || at != m.CPU.IP || counts != s.Counters {
			t.Fatal("enemy refusal changed state", name)
		}
	}
	setupWrite(t, filepath.Join(work, "enemy-models.json"), map[string]any{"counter_controls": controls, "amount_models": models, "empty_shifted_target_amount": 1, "amount_refusals": 6, "counter_refusals": len(refusals)})
}

func enemyInput(t *testing.T, e *game.Engine, hold bool) error {
	t.Helper()
	if hold {
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x190a), func(*dg.Machine) (bool, error) { return false, errOriginalEnemyHeld })
	}
	// Existing encounter driver uses real Space keys to pass the player half.
	err := spellEncounter(t, e, 0, "pass", true, true)
	e.Oracle.SetStepGuard(nil)
	return err
}
func TestOriginalEnemySpecials(t *testing.T) {
	work, root, catalog := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	parent := filepath.Join(work, "enemy-r1")
	if er := os.MkdirAll(parent, 0700); er != nil {
		t.Fatal(er)
	}
	cases := []struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{}
	for i := 0; i < 8; i++ {
		cases = append(cases, struct {
			Name     string
			Selector int
			Kind     uint16
			Gate     uint16
			HD       bool
		}{fmt.Sprintf("selector-%d-hd", i), i, 10, 4, true})
	}
	cases = append(cases, struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{"native-mode", 0, 10, 4, false}, struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{"kind12", 0, 12, 4, true}, struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{"gate0", 3, 12, 0, true}, struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{"natural-dispatch", -1, 12, 4, true}, struct {
		Name     string
		Selector int
		Kind     uint16
		Gate     uint16
		HD       bool
	}{"clone12", 6, 12, 4, true})
	for _, sc := range cases {
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
				player := [6]ArmyStack{{"native:01", 70}, {"native:06", 30}}
				enemy := [6]ArmyStack{{fmt.Sprintf("native:%02d", sc.Kind), 50}, {"native:16", 10}}
				fixtureApplied := false
				swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x36ca), func(m *dg.Machine) (bool, error) {
					if fixtureApplied {
						return false, nil
					}
					fixtureApplied = true
					for i, row := range enemy {
						p := catalog.Profiles[row.Unit]
						m.Write16(0x1e880+0x5700+uint32(i*4), p.NativeKind)
						m.Write16(0x1e880+0x5702+uint32(i*4), uint16(row.Count))
					}
					if mode == 0 {
						for i, row := range player {
							p := catalog.Profiles[row.Unit]
							m.Write16(0x1e880+0x56e8+uint32(i*4), p.NativeKind)
							m.Write16(0x1e880+0x56ea+uint32(i*4), uint16(row.Count))
						}
					}
					return false, nil
				})
				e.Oracle.OnCall(oracle.Far(0xf67, 0x1daa), func(o *oracle.Oracle) {
					if !fixtureApplied {
						t.Fatal("enemy fixture boundary not reached")
					}
					for i, row := range enemy {
						p := catalog.Profiles[row.Unit]
						if o.Word(oracle.Far(0x1e88, 0x5700+uint16(i*4))) != p.NativeKind || o.Word(oracle.Far(0x1e88, 0x5702+uint16(i*4))) != uint16(row.Count) {
							t.Fatal("enemy fixture overwritten", i)
						}
					}
					o.WriteU16(oracle.Far(0x1e88, 0x26ae), sc.Gate)
				})
				observed := -1
				e.Oracle.OnCall(oracle.Far(0xf67, 0xd88), func(o *oracle.Oracle) {
					if sc.Selector >= 0 {
						r := o.Regs()
						o.WriteU16(oracle.Far(r.SS, r.BP-4), uint16(sc.Selector))
					}
				})
				e.Oracle.OnCall(oracle.Far(0xf67, 0xd96), func(o *oracle.Oracle) { r := o.Regs(); observed = int(o.Word(oracle.Far(r.SS, r.BP-4))) })
				var owner *originalBattleEnemy
				var rounds *originalBattleRounds
				if mode == 1 {
					_, er := installOriginalArmyProjection(e, catalog, player)
					must(er)
					setup, er := installOriginalBattleSetup(e, catalog, nil)
					must(er)
					a, er := installOriginalBattleActions(e, setup, true)
					must(er)
					rounds, er = installOriginalBattleRounds(e, a)
					must(er)
					owner, er = installOriginalBattleEnemy(e, rounds)
					must(er)
					owner.Hold = true
				}
				err := enemyInput(t, e, mode == 0)
				if !errors.Is(err, errOriginalEnemyHeld) {
					must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
					trace := map[string]any{}
					if owner != nil {
						trace = map[string]any{"record": owner.Record, "rows": owner.Rows, "counters": owner.Counters, "mask": owner.Mask, "active": owner.Active, "current": owner.Current, "alias": owner.Alias}
					}
					setupWrite(t, filepath.Join(dir, "failed.json"), map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs(), "observed_selector": observed, "owner": trace})
					f, er := os.Create(filepath.Join(dir, "failed.png"))
					must(er)
					must(png.Encode(f, e.Frame()))
					must(f.Close())
					t.Fatal("enemy action", err, e.Oracle.Regs())
				}
				frame := e.Frame()
				if sc.Selector >= 0 && observed != sc.Selector {
					t.Fatal("requested enemy selector not reached", sc.Selector, observed)
				}
				f, er := os.Create(filepath.Join(dir, "frame.png"))
				must(er)
				must(png.Encode(f, frame))
				must(f.Close())
				must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
				row := map[string]any{"name": sc.Name, "requested_selector": sc.Selector, "selector": observed, "kind": sc.Kind, "gate_field": sc.Gate, "mode": mode, "hd": sc.HD, "controlled_fixture": true, "units_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48)), "hp_hex": fmt.Sprintf("%x", append(e.Oracle.Bytes(oracle.Far(0x1e88, 0x8ca4), 12), e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e60), 12)...)), "counters_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x8e78), 12)), "seed": originalSeed(e.Oracle), "frame_sha256": contentSHA(frame.Pix)}
				if mode == 0 {
					reference = row
				} else {
					for _, key := range []string{"selector", "units_hex", "hp_hex", "counters_hex", "seed", "frame_sha256"} {
						if reference[key] != row[key] {
							t.Fatal("original/Go enemy differs", sc.Name, key, reference[key], row[key])
						}
					}
					if len(owner.Records) != 1 {
						t.Fatal("enemy not recorded")
					}
					row["record"] = owner.Records[0]
					row["rows"] = rounds.Rows
					row["counters"] = owner.Counters
					before := e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)
					cycles := e.Oracle.Cycles()
					for n := 0; n < 5; n++ {
						if er := e.AdvanceCycles(100000); !errors.Is(er, errOriginalEnemyHeld) {
							t.Fatal("enemy hold", er)
						}
					}
					if !bytes.Equal(before, e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) || cycles != e.Oracle.Cycles() {
						t.Fatal("enemy hold changed state")
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
func TestOriginalEnemyGuards(t *testing.T) {
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
		m, s := enemyFixture(t, code, catalog, 0x37b0, 1)
		s.Active = true
		s.EffectSP = 0xee02
		s.EffectBP = 0xef00
		s.EffectReturn = 0xe0d
		s.Current = &originalSpellEffect{Before: 70, After: 65, Planned: []uint16{70, 69, 68, 67, 66, 65}}
		m.CPU.R[dg.AX] = 70
		m.Write16(0x1e880+0xee00, 0xef00)
		m.Write16(0x1e880+0xee02, 0xe0d)
		m.Write16(0x1e880+0xee04, 0xf67)
		switch name {
		case "source":
			m.Mem[0xf670+0x36c6] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "frame":
			m.CPU.R[dg.BP]--
		case "projection":
			m.Write16(0x1e880+0x56ea, 69)
		case "index":
			m.CPU.R[dg.BX] = 24
		case "display":
			m.CPU.R[dg.AX] = 69
		case "committed":
			s.Current.Updates = 1
		case "inactive":
			s.Active = false
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		rows := s.Rows
		if _, er := s.impactWrite(m, 0x37b0); er == nil {
			t.Fatal("unsafe enemy impact", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP || rows != s.Rows || len(s.Current.Display) != 0 {
			t.Fatal("enemy impact refusal changed state", name)
		}
	}
	for _, name := range []string{"source", "segment", "frame", "ordinary", "dead", "wide", "uninitialized", "overlap", "gate", "sorting", "inactive"} {
		m, s := enemyFixture(t, code, catalog, 0xcf6, 1)
		s.Record.Selector = -1
		s.Active = false
		m.Write16(0x1e880+0xef00, 0x190a)
		m.Write16(0x1e880+0xef02, 0xf67)
		m.Write16(0x1e880+0xef04, 5)
		m.Write16(0x1e880+0x26ae, 0)
		switch name {
		case "source":
			m.Mem[0xf670+0xcf6] ^= 1
		case "segment":
			m.CPU.Seg[dg.DS]++
		case "frame":
			m.Write16(0x1e880+0xef00, 0)
		case "ordinary":
			m.Write16(0x1e880+0xef04, 0)
		case "dead":
			s.Rounds.Rows[1][s.Rounds.Slots[1][5]].Count = 0
		case "wide":
			s.Rounds.Rows[0][0].Count = 32768
		case "uninitialized":
			s.Mask = 0
		case "overlap":
			s.Active = true
			s.Record.Selector = 4
		case "gate":
			m.Write16(0x1e880+0x26ae, 65535)
		case "sorting":
			s.Rounds.Sorting = 0
		case "inactive":
			s.Rounds.Active = false
		}
		before := bytes.Clone(m.Mem)
		regs, flags, cycles, ip := m.CPU.R, m.CPU.Flags, m.CPU.Cycles, m.CPU.IP
		active := s.Active
		rows := s.Rows
		if _, er := s.begin(m); er == nil {
			t.Fatal("unsafe enemy entry", name)
		}
		if !bytes.Equal(before, m.Mem) || regs != m.CPU.R || flags != m.CPU.Flags || cycles != m.CPU.Cycles || ip != m.CPU.IP || active != s.Active || rows != s.Rows {
			t.Fatal("enemy entry refusal changed state", name)
		}
	}
	aliases := []map[string]any{}
	var site originalEnemyReadSite
	for _, v := range originalEnemyReads {
		if v.Guard {
			site = v
		}
	}
	for alias := uint16(0); alias < 12; alias++ {
		m, s := enemyFixture(t, code, catalog, 0xfca, 1)
		s.Active = true
		s.Record.Selector = 5
		s.Alias = alias
		m.Write16(0x1e880+0x6fb4, alias)
		m.Write16(0x1e880+0xedf8, 0)
		m.CPU.R[dg.BX] = alias * 4
		n := dg.New()
		copy(n.Mem, m.Mem)
		n.CPU.R = m.CPU.R
		n.CPU.Seg = m.CPU.Seg
		n.CPU.Flags = m.CPU.Flags
		n.CPU.IP = m.CPU.IP
		if er := n.Step(); er != nil {
			t.Fatal(er)
		}
		if _, er := s.read(m, site); er != nil {
			t.Fatal(er)
		}
		if !bytes.Equal(n.Mem, m.Mem) || n.CPU.Flags != m.CPU.Flags || n.CPU.IP != m.CPU.IP || n.CPU.R != m.CPU.R {
			t.Fatal("shifted guard original/Go", alias)
		}
		aliases = append(aliases, map[string]any{"alias": alias, "flags": m.CPU.Flags})
	}
	m, s := enemyFixture(t, code, catalog, 0xfca, 1)
	s.Active = true
	s.Record.Selector = 5
	s.Alias = 12
	m.Write16(0x1e880+0x6fb4, 12)
	m.Write16(0x1e880+0xedf8, 0)
	m.CPU.R[dg.BX] = 48
	before := bytes.Clone(m.Mem)
	if _, er := s.read(m, site); er == nil || !bytes.Equal(before, m.Mem) {
		t.Fatal("unknown shifted alias admitted", er)
	}
	setupWrite(t, filepath.Join(work, "enemy-guards.json"), map[string]any{"impact_refusals": 8, "entry_refusals": 11, "shifted_alias_controls": aliases, "shifted_alias_refusals": 1, "state_unchanged": true})
}

func TestOriginalEnemyWorld(t *testing.T) {
	name := "enemy-world-r1"
	player := [6]ArmyStack{{"native:01", 74}, {"openkb:wolf", 2}, {"openkb:arcr", 2}}
	enemy := [6]ArmyStack{{"native:12", 3}, {"native:16", 10}}
	work, root, combat := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	dir := filepath.Join(work, name)
	must(os.Mkdir(dir, 0700))
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	w := snap.World
	w.Army.Slots = player
	w.Army.Rules = "formation"
	w.Revision++
	snap, err = store.Commit(snap.Token, w)
	must(err)
	port := &worldArmyPort{Store: store, Current: snap}
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, assets, dir, true)
	defer e.Close()
	fixtureApplied := false
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x36ca), func(m *dg.Machine) (bool, error) {
		if fixtureApplied {
			return false, nil
		}
		fixtureApplied = true
		for i, row := range enemy {
			profile := combat.Profiles[row.Unit]
			m.Write16(0x1e880+0x5700+uint32(i*4), profile.NativeKind)
			m.Write16(0x1e880+0x5702+uint32(i*4), uint16(row.Count))
		}
		return false, nil
	})
	e.Oracle.OnCall(oracle.Far(0xf67, 0x1daa), func(o *oracle.Oracle) {
		if !fixtureApplied {
			t.Fatal("world enemy fixture missing")
		}
		for i, row := range enemy {
			if o.Word(oracle.Far(0x1e88, 0x5702+uint16(i*4))) != uint16(row.Count) {
				t.Fatal("world enemy fixture overwritten")
			}
		}
	})
	forced := false
	e.Oracle.OnCall(oracle.Far(0xf67, 0xd88), func(o *oracle.Oracle) {
		if !forced {
			r := o.Regs()
			o.WriteU16(oracle.Far(r.SS, r.BP-4), 1)
			forced = true
		}
	})
	projection, err := installOriginalArmyProjectionMode(e, combat, player, true)
	must(err)
	setup, err := installOriginalBattleSetup(e, combat, &player)
	must(err)
	actions, err := installOriginalBattleActions(e, setup, true)
	must(err)
	rounds, err := installOriginalBattleRounds(e, actions)
	must(err)
	projection.Rounds = rounds
	spells, err := installOriginalBattleSpells(e, rounds)
	must(err)
	support, err := installOriginalBattleSupport(e, spells)
	must(err)
	owner, err := installOriginalBattleEnemy(e, rounds)
	must(err)
	firstSideSet := false
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x2076), func(m *dg.Machine) (bool, error) {
		if firstSideSet {
			return false, nil
		}
		if er := actions.check(m, 0x2076, 0x205e6, 0x20689); er != nil {
			return false, er
		}
		sp := uint32(m.CPU.R[dg.SP])
		if sp > 65529 || m.Read16(0x1e880+sp) != 0x3c || m.Read16(0x1e880+sp+2) != 0xf67 || m.Read16(0x1e880+sp+4) != 0 {
			return false, errors.New("enemy world first-side caller")
		}
		m.Write16(0x1e880+sp+4, 1)
		firstSideSet = true
		return false, nil
	})
	world, err := installOriginalBattleWorld(e, port, projection, rounds)
	must(err)
	checkpoint, err := installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
	must(err)
	err = spellEncounter(t, e, 0, "", true, true)
	if !errors.Is(err, errOriginalBattleRoundsHeld) {
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed-battle.state")))
		setupWrite(t, filepath.Join(dir, "failed-battle.json"), map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs(), "spells": spells.Records, "enemy": owner.Records, "current_enemy": owner.Record, "rows": rounds.Rows, "history": rounds.History})
		t.Fatal("spell continuous battle", err)
	}
	if rounds.Result != "win" || !firstSideSet || !forced || len(owner.Records) == 0 || owner.Records[0].Selector != 1 || len(owner.Records[0].Effects) != 3 || len(rounds.History) < 2 {
		t.Fatal("enemy/ordinary world battle incomplete", rounds.Result, owner.Records, len(rounds.History))
	}
	for raw := 1; raw <= 2; raw++ {
		found := false
		for _, effect := range owner.Records[0].Effects {
			if int(effect.Raw) == raw {
				found = effect.Before == 2 && effect.After == 0 && effect.Updates == 1
			}
		}
		if !found {
			t.Fatal("expanded enemy effect not committed", raw)
		}
	}
	rounds.AllowWorld = true
	phase := true
	last := uint64(0)
	e.Oracle.OnCall(oracle.Far(0x160a, 0x87), func(o *oracle.Oracle) {
		if phase && o.Steps()-last > 50000 {
			last = o.Steps()
			o.PressKey(oracle.KeyEnter)
		}
	})
	stop := errors.New("spell world returned")
	start := e.Oracle.Steps()
	e.Oracle.SetStepGuard(func(o *oracle.Oracle) error {
		if world.Returned {
			return stop
		}
		if o.Steps() > start+50000000 {
			return errors.New("spell world budget")
		}
		return nil
	})
	for {
		err = catchWorldArmyFault(func() error { return e.AdvanceCycles(100000) })
		e.RenderAudio()
		if err != nil {
			break
		}
	}
	e.Oracle.SetStepGuard(nil)
	phase = false
	if !errors.Is(err, stop) || !world.Committed {
		t.Fatal("spell world return", err)
	}
	e.ReleaseAll()
	setupAdvance(t, e, 500)
	charges := fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x2aa8), 16))
	file, err := os.Create(filepath.Join(dir, "map.png"))
	must(err)
	must(png.Encode(file, e.Frame()))
	must(file.Close())
	location := checkpointLocation(e.Oracle)
	setupPress(t, e, 0x41)
	setupPress(t, e, 0x1c)
	setupPress(t, e, 0x1c)
	setupAdvance(t, e, 700)
	e.ReleaseAll()
	if checkpoint.Saves != 1 {
		t.Fatal("spell F7", checkpoint.Saves)
	}
	saved, err := store.Recover()
	must(err)
	if saved.World.Army.Slots != projection.Remaining {
		t.Fatal("spell survivors not saved")
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "saved.state")))
	setupWrite(t, filepath.Join(dir, "enemy.json"), map[string]any{"records": owner.Records, "counters": owner.Counters, "reads": owner.CounterReads, "consumes": owner.CounterConsumes, "player_counter_consumes": support.Consumes, "enemy_initial": enemy, "controlled_enemy_first": firstSideSet, "forced_first_selector": 1, "native_rows_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 48))})
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"status": "passed-original-enemy-world", "initial": player, "remaining": saved.World.Army.Slots, "world_sha256": worldDigest(saved.World), "charges_hex": charges, "records": spells.Records, "ordinary_actions": len(rounds.History), "result": rounds.Result, "resources": pairWorldResources(saved.World), "location": location, "checkpoint_saves": checkpoint.Saves, "controlled_abi_fixture": true, "battle_rules_applied": "native", "stored_rules": saved.World.Army.Rules})
}

func TestOriginalEnemyExpanded(t *testing.T) {
	work, root, catalog := setupInputs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	dir := filepath.Join(work, "enemy-expanded-r1")
	must(os.Mkdir(dir, 0700))
	e := setupCold(t, root, os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS"), dir, true)
	defer e.Close()
	player := [6]ArmyStack{{"openkb:wolf", 100}, {"openkb:arcr", 10}}
	enemy := [6]ArmyStack{{"native:10", 50}, {"native:16", 10}}
	shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
	fixtureApplied := false
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x36ca), func(m *dg.Machine) (bool, error) {
		if fixtureApplied {
			return false, nil
		}
		fixtureApplied = true
		for i, row := range enemy {
			profile := catalog.Profiles[row.Unit]
			m.Write16(0x1e880+0x5700+uint32(i*4), profile.NativeKind)
			m.Write16(0x1e880+0x5702+uint32(i*4), uint16(row.Count))
		}
		return false, nil
	})
	e.Oracle.OnCall(oracle.Far(0xf67, 0xd88), func(o *oracle.Oracle) { r := o.Regs(); o.WriteU16(oracle.Far(r.SS, r.BP-4), 1) })
	_, err := installOriginalArmyProjectionMode(e, catalog, player, true)
	must(err)
	setup, err := installOriginalBattleSetup(e, catalog, &player)
	must(err)
	actions, err := installOriginalBattleActions(e, setup, true)
	must(err)
	rounds, err := installOriginalBattleRounds(e, actions)
	must(err)
	owner, err := installOriginalBattleEnemy(e, rounds)
	must(err)
	owner.Hold = true
	err = enemyInput(t, e, false)
	if !errors.Is(err, errOriginalEnemyHeld) {
		must(e.Oracle.SaveStateFile(filepath.Join(dir, "failed.state")))
		setupWrite(t, filepath.Join(dir, "failed.json"), map[string]any{"error": fmt.Sprint(err), "record": owner.Record, "rows": rounds.Rows})
		t.Fatal(err)
	}
	if !fixtureApplied || len(owner.Records) != 1 || len(owner.Records[0].Effects) != 2 {
		t.Fatal("expanded special not applied", owner.Records)
	}
	native := e.Oracle.Bytes(oracle.Far(0x1e88, 0x56e8), 24)
	if !bytes.Equal(native, make([]byte, 24)) || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		t.Fatal("expanded special escaped projection")
	}
	must(e.Oracle.SaveStateFile(filepath.Join(dir, "held.state")))
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"initial": player, "rows": rounds.Rows, "record": owner.Records[0], "native_player_hex": fmt.Sprintf("%x", native), "original_shadow_unchanged": true, "controlled_fixture": true})
}

// Execute the original motion branches with explicitly stubbed drawing/impact
// callees. This isolates slot writes; it is not a complete battle oracle.
func TestOriginalEnemyMotionResearch(t *testing.T) {
	work, _, catalog := setupInputs(t)
	pam, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	if err != nil {
		t.Fatal(err)
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		t.Fatal(err)
	}
	reports := []map[string]any{}
	for side := 0; side < 2; side++ {
		for from := 0; from < 3; from++ {
			for target := 0; target < 6; target++ {
				for _, empty := range []bool{false, true} {
					rows := [2][6]ArmyStack{}
					for raw := 0; raw < 3; raw++ {
						rows[side][raw] = ArmyStack{fmt.Sprintf("native:%02d", raw+1), 10}
					}
					if empty && target%3 != from {
						rows[side][target%3] = ArmyStack{}
					}
					rows[1-side][target] = ArmyStack{"native:01", 10}
					m, _ := actionFixture(t, code, catalog, rows)
					for army, base := range []uint32{0x6fb6, 0x6fc2} {
						for raw := 0; raw < 6; raw++ {
							m.Write16(0x1e880+base+uint32(raw*2), uint16(raw))
						}
						_ = army
					}
					start, end := uint16(0x3930), uint16(0x4587)
					if side == 1 {
						start, end = 0x484c, 0x54d2
					}
					m.CPU.IP = start
					for i, value := range []uint16{0xffff, 0xf67, uint16(from), uint16(target)} {
						m.Write16(0x1e880+0xef00+uint32(i*2), value)
					}
					stubs := []uint16{}
					steps := 0
					for m.CPU.IP != 0xffff {
						if steps > 20000 || m.CPU.Seg[dg.CS] != 0xf67 || m.CPU.IP < start || m.CPU.IP > end {
							t.Fatal("motion research escaped", side, from, target, m.CPU.IP)
						}
						steps++
						at := uint32(0xf670) + uint32(m.CPU.IP)
						op := m.Mem[at]
						if op == 0xe8 {
							sp := uint32(m.CPU.R[dg.SP])
							if m.Read16(0x1e880+sp) != 0xf67 {
								t.Fatal("motion near callee is not far wrapper")
							}
							stubs = append(stubs, m.CPU.IP)
							m.CPU.R[dg.SP] += 2
							m.CPU.IP += 3
							continue
						}
						if op == 0x9a {
							locals := uint16(10 + side*2)
							if m.CPU.IP != start+6 || m.CPU.R[dg.AX] != locals {
								t.Fatal("unclassified motion far call", side, m.CPU.IP, m.CPU.R[dg.AX])
							}
							stubs = append(stubs, m.CPU.IP)
							m.CPU.R[dg.SP] -= locals
							m.CPU.IP += 5
							continue
						}
						if er := m.Step(); er != nil {
							t.Fatal(er)
						}
					}
					after := [6]uint16{}
					for raw := range after {
						after[raw] = m.Read16(0x1e880 + 0x6fb6 + uint32(side*12+raw*2))
					}
					slots := [6]uint16{0, 1, 2, 3, 4, 5}
					expected, er := roundMotionPlanForTarget(rows[side], slots, from, target)
					if er != nil || after != expected {
						t.Fatal("original/Go full-target motion", side, from, target, empty, after, expected, er)
					}
					reports = append(reports, map[string]any{"side": side, "from": from, "target": target, "empty_destination": empty, "after": after, "go_after": expected, "stubbed_call_ips": stubs, "scope": "Original slot writes only; drawing and impact callees stubbed."})
				}
			}
		}
	}
	setupWrite(t, filepath.Join(work, "enemy-motion-research.json"), map[string]any{"rows": reports, "complete_battle": false})
}
