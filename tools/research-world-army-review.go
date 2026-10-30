//go:build ignore

// 030 DRAFT: own the F2 canvas while preserving the original key-wait/return.
package main

import (
	"bytes"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type armyReviewRow struct {
	Slot   int    `json:"slot"`
	ID     string `json:"id"`
	Name   string `json:"name"`
	Count  uint32 `json:"count"`
	Used   uint64 `json:"used"`
	Native bool   `json:"native"`
}
type armyReviewData struct {
	Rows       [6]armyReviewRow `json:"rows"`
	Metrics    worldArmyMetrics `json:"metrics"`
	Gold       uint64           `json:"gold"`
	Leadership uint64           `json:"leadership"`
	Rules      string           `json:"rules"`
}

func describeArmyReview(c ArmyCatalog, w OwnedWorld) (armyReviewData, error) {
	v := armyReviewData{Gold: w.Army.Gold, Leadership: w.Army.Leadership, Rules: w.Army.Rules}
	m, e := measureWorldArmy(c, w.Army)
	if e != nil {
		return v, e
	}
	v.Metrics = m
	idx, _ := c.index()
	for i, s := range w.Army.Slots {
		v.Rows[i] = armyReviewRow{Slot: i, ID: s.Unit, Count: s.Count}
		if s.Unit != "" {
			p := idx[s.Unit]
			v.Rows[i].Name = p.Name
			v.Rows[i].Used = uint64(s.Count) * p.Command
			v.Rows[i].Native = p.NativeKind != 0
		}
	}
	return v, nil
}

type armyReview struct {
	Engine                                *game.Engine
	Port                                  *worldArmyPort
	Expected                              []byte
	Active                                bool
	Data                                  armyReviewData
	Token                                 string
	EntrySP                               uint16
	EntryMode                             uint16
	NativeRows                            []byte
	Opens, Closes, Skipped, NativeEntries uint64
	ThisSkip                              uint64
}

func (v *armyReview) checkSource(o *oracle.Oracle) error {
	if !bytes.Equal(v.Expected, o.Bytes(oracle.Far(0x110, 0x3e92), len(v.Expected))) {
		return errors.New("review dispatcher code changed")
	}
	return nil
}
func (v *armyReview) read() (progressPairSnapshot, error) {
	s, e := v.Port.snapshot()
	if e != nil {
		return s, e
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(v.Engine.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return s, errors.New("review resource binding")
		}
	}
	return s, nil
}
func installArmyReview(e *game.Engine, p *worldArmyPort) (*armyReview, error) {
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	v := &armyReview{Engine: e, Port: p, Expected: append([]byte(nil), code[0x3e92:0x3f08]...)}
	if err = v.checkSource(e.Oracle); err != nil {
		return nil, err
	}
	fail := func(s string) { panic(&worldArmyPortFault{"army review: " + s}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x3e92), func(o *oracle.Oracle) {
		if o.Word(oracle.Far(0x1e88, 0x56bc)) != 1 {
			return
		}
		if x := v.checkSource(o); x != nil {
			fail(x.Error())
		}
		r := o.Regs()
		mode := o.Word(oracle.Far(0x1e88, 0x7484))
		if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65527 || (mode != 1 && mode != 3) {
			fail("entry segments/mode")
		}
		ret := o.Word(oracle.Far(r.SS, r.SP))
		retCS := o.Word(oracle.Far(r.SS, r.SP+2))
		arg := o.Word(oracle.Far(r.SS, r.SP+4))
		if retCS != 0x110 || (ret != 0x3da2 && ret != 0x3d2d) || arg != 1 {
			fail("F2 caller")
		}
		s, x := v.read()
		if x != nil {
			fail(x.Error())
		}
		if v.Active {
			if v.EntrySP != r.SP || v.Token != s.Token || v.ThisSkip != 0 {
				fail("unexpected review reentry")
			}
			return
		}
		data, x := describeArmyReview(p.Store.Catalog, s.World)
		if x != nil {
			fail(x.Error())
		}
		v.Active = true
		v.Data = data
		v.Token = s.Token
		v.EntrySP = r.SP
		v.EntryMode = mode
		v.ThisSkip = 0
		v.NativeRows = o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		v.Opens++
	})
	for ip, arg := range map[uint16]uint16{0x3ebc: 0x2f, 0x3ece: 0x30} {
		ip, arg := ip, arg
		e.Oracle.OnHostInstruction(oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return v.skipRows(m, ip, arg) })
	}
	e.Oracle.OnCall(oracle.Far(0x110, 0x75c6), func(*oracle.Oracle) {
		if v.Active {
			v.NativeEntries++
			fail("native row renderer escaped")
		}
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x3ed8), func(o *oracle.Oracle) {
		if !v.Active {
			return
		}
		if x := v.checkSource(o); x != nil {
			fail(x.Error())
		}
		s, x := v.read()
		if x != nil {
			fail(x.Error())
		}
		if s.Token != v.Token || v.ThisSkip != 1 || !bytes.Equal(v.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			fail("review mutated the army or missed its renderer")
		}
		v.Active = false
		v.Closes++
	})
	return v, nil
}
func (v *armyReview) skipRows(m *dg.Machine, ip, arg uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"army review: " + s} }
	c := m.CPU
	ds := uint32(0x1e880)
	sp := c.R[dg.SP]
	if !v.Active || c.Seg[dg.CS] != 0x110 || c.IP != ip || c.Seg[dg.SS] != 0x1e88 || c.Seg[dg.DS] != 0x1e88 || sp > 65531 {
		return fail("row call ABI")
	}
	if m.Read16(ds+0x56bc) != 1 || m.Read16(ds+uint32(sp)) != 0x110 || m.Read16(ds+uint32(sp)+2) != arg {
		return fail("row call argument")
	}
	if (ip == 0x3ebc && (arg != 0x2f || v.EntryMode != 1)) || (ip == 0x3ece && (arg != 0x30 || v.EntryMode != 3)) || (ip != 0x3ebc && ip != 0x3ece) {
		return fail("row call mode")
	}
	if v.ThisSkip != 0 || c.Cycles == ^uint64(0) {
		return fail("row call repeated/accounting")
	}
	if !bytes.Equal(m.Mem[0x1100+0x3e92:0x1100+0x3f08], v.Expected) {
		return fail("row dispatcher bytes")
	}
	s, e := v.read()
	if e != nil {
		return fail(e.Error())
	}
	if s.Token != v.Token {
		return fail("stale review")
	}
	// The F2 caller discards the row renderer's AX. Return zero, consume its
	// explicit PUSH CS, and continue into the original sub_1844C key wait.
	c.R[dg.AX] = 0
	c.R[dg.SP] += 2
	c.IP += 3
	c.Cycles++
	v.ThisSkip++
	v.Skipped++
	return true, nil
}
func (v *armyReview) Summary() string {
	return fmt.Sprintf("F2 review %d opens/%d closes, %d native render calls skipped", v.Opens, v.Closes, v.Skipped)
}
