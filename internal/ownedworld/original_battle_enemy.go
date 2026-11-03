package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalEnemyHeld = errors.New("Go enemy special returned; held before next actor")

type originalEnemySpecialRecord struct {
	Selector                      int
	SourceSlot, Kind              uint16
	Effects                       []originalSpellEffect
	Clone                         *originalCloneRecord
	BeforeCounters, AfterCounters [6]uint16
	FreezeWrites                  int
	GateSeen                      bool
	Gate                          uint16
	SeedBefore, SeedAfter         uint32
}
type originalBattleEnemy struct {
	Engine                           *game.Engine
	Rounds                           *originalBattleRounds
	Active, Hold                     bool
	Rows                             [2][6]ArmyStack
	Projected                        [48]byte
	EntrySP, EntryBP                 uint16
	Record                           originalEnemySpecialRecord
	Alias                            uint16
	Current                          *originalSpellEffect
	EffectSP, EffectBP, EffectReturn uint16
	Direct                           bool
	ClearStage                       uint16
	Counters                         [6]uint16
	Mask                             uint8
	InitIndex                        int
	CounterReads, CounterConsumes    uint64
	Records                          []originalEnemySpecialRecord
}

func originalEnemyAmount(selector int, kind uint16, before uint32) (uint16, error) {
	if (kind != 10 && kind != 12) || before > 32767 {
		return 0, errors.New("enemy amount identity/count")
	}
	var amount uint32
	switch selector {
	case 0, 1:
		amount = 5
		if kind == 12 {
			amount = 2
		}
	case 2:
		amount = 15
		if kind == 12 {
			amount = 6
		}
	case 3:
		amount = before
	case 5:
		d := uint32(2)
		if kind == 12 {
			d = 3
		}
		amount = before/d + 1
	case 7:
		amount = before
		if before >= 50 {
			if before*6 > 65535 {
				return 0, errors.New("enemy quake product range")
			}
			d := uint32(10)
			if kind == 12 {
				d = 20
			}
			amount = before*6/d + 1
		}
	default:
		return 0, errors.New("enemy selector has no damage")
	}
	if before == 0 && selector != 5 {
		return 0, errors.New("enemy empty target")
	}
	return uint16(amount), nil
}
func (s *originalBattleEnemy) counterProjection(m *dg.Machine) error {
	for i, n := range s.Counters {
		if s.Mask&(1<<i) != 0 && m.Read16(0x1e880+0x8e78+uint32(i*2)) != n {
			return errors.New("enemy action counter changed")
		}
	}
	return nil
}
func (s *originalBattleEnemy) projection(m *dg.Machine) error {
	r := s.Rounds
	if !bytes.Equal(s.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718]) || !bytes.Equal(r.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0]) || !bytes.Equal(r.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c]) {
		return errors.New("enemy special projection changed")
	}
	return s.counterProjection(m)
}
func (s *originalBattleEnemy) check(m *dg.Machine, ip uint16, start, end int) error {
	if !s.Rounds.Active || s.Rounds.Done {
		return errors.New("enemy special battle lifecycle")
	}
	if err := s.Rounds.Actions.check(m, ip, start, end); err != nil {
		return err
	}
	return s.counterProjection(m)
}
func (s *originalBattleEnemy) wrapper(m *dg.Machine, ip uint16) error {
	if err := s.check(m, ip, 0x1f266, 0x1fa29); err != nil {
		return err
	}
	if !s.Active || m.CPU.R[dg.BP] != s.EntrySP-2 {
		return errors.New("enemy special wrapper frame")
	}
	return nil
}
func (s *originalBattleEnemy) begin(m *dg.Machine) (bool, error) {
	if err := s.check(m, 0xcf6, 0x1f266, 0x1fa29); err != nil {
		return false, err
	}
	r := s.Rounds
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if s.Active && s.EntrySP == c.R[dg.SP] && s.EntryBP == c.R[dg.BP] && s.Record.Selector == -1 && sp <= 65520 && m.Read16(0x1e880+sp) == 0x190a && m.Read16(0x1e880+sp+2) == 0xf67 && m.Read16(0x1e880+sp+4) == s.Record.SourceSlot {
		return false, nil
	}
	if s.Active || s.Mask != 63 || r.Sorting != -1 || r.Actions.Casualties.Started || (r.Spells != nil && r.Spells.Active) || sp > 65520 || m.Read16(0x1e880+sp) != 0x190a || m.Read16(0x1e880+sp+2) != 0xf67 {
		return false, errors.New("enemy special entry context")
	}
	slot := m.Read16(0x1e880 + sp + 4)
	if slot >= 6 {
		return false, errors.New("enemy caster slot")
	}
	row := r.Rows[1][r.Slots[1][slot]]
	p := r.Actions.Setup.Catalog.Profiles[row.Unit]
	if row.Count == 0 || row.Count > 32767 || (p.NativeKind != 10 && p.NativeKind != 12) || m.Read16(0x1e880+0x26ae) > 6552 {
		return false, errors.New("enemy caster identity/gate")
	}
	for side, rows := range r.Rows {
		for _, row := range rows {
			if row.Count > 32767 || (side == 1 && row.Count > 0 && r.Actions.Setup.Catalog.Profiles[row.Unit].NativeKind == 0) {
				return false, errors.New("enemy special row bounds")
			}
		}
	}
	s.Rows, s.Projected = r.Rows, r.Projected
	s.EntrySP, s.EntryBP = c.R[dg.SP], c.R[dg.BP]
	s.Alias = m.Read16(0x1e880 + 0x6fb4)
	s.Record = originalEnemySpecialRecord{Selector: -1, SourceSlot: slot, Kind: p.NativeKind, BeforeCounters: s.Counters, SeedBefore: originalSeed(s.Engine.Oracle)}
	s.Current = nil
	s.Active = true
	return false, nil
}
func (s *originalBattleEnemy) dispatch(m *dg.Machine) (bool, error) {
	if err := s.wrapper(m, 0xd96); err != nil {
		return false, err
	}
	n := int(m.Read16(0x1e880 + uint32(m.CPU.R[dg.BP]) - 4))
	if n < 0 || n > 7 || m.CPU.R[dg.BX] != uint16(n*2) {
		return false, errors.New("enemy selector dispatch")
	}
	if s.Record.Selector == n {
		return false, nil
	}
	if s.Record.Selector != -1 {
		return false, errors.New("enemy selector changed")
	}
	if n == 7 {
		for _, row := range s.Rows[0] {
			if row.Count >= 50 && row.Count*6 > 65535 {
				return false, errors.New("enemy quake unsafe product")
			}
		}
	}
	s.Record.Selector = n
	return false, nil
}

type originalEnemyReadSite struct {
	IDA                   int
	Side, Local, Selector int
	Read, SI, Guard       bool
}

var originalEnemyReads = []originalEnemyReadSite{
	{0x1f326, 0, 8, 0, false, false, false}, {0x1f3dd, 0, 12, 1, false, false, false}, {0x1f456, 0, 8, 2, false, false, false}, {0x1f4b6, 0, 8, 3, false, false, false},
	{0x1f4ef, 0, 8, 3, true, false, false}, {0x1f53a, 0, 8, 5, false, false, true}, {0x1f561, 0, 8, 5, true, false, false}, {0x1f57d, 0, 8, 5, true, false, false},
	{0x1f5a0, 1, 8, 6, false, false, false}, {0x1f5b3, 1, 8, 6, true, false, false}, {0x1f641, 1, 8, 6, true, false, false},
	{0x1f929, 0, 12, 7, true, false, false}, {0x1f949, 0, 12, 7, true, false, false}, {0x1f99d, 0, 12, 7, false, false, false}, {0x1f9c4, 0, 12, 7, false, false, false}, {0x1f9d8, 0, 12, 7, true, true, false},
}

func (s *originalBattleEnemy) read(m *dg.Machine, site originalEnemyReadSite) (bool, error) {
	ip := uint16(site.IDA - 0x1e570)
	if err := s.wrapper(m, ip); err != nil {
		return false, err
	}
	if s.Record.Selector != site.Selector {
		return false, errors.New("enemy count selector")
	}
	slot := m.Read16(0x1e880 + uint32(m.CPU.R[dg.BP]) - uint32(site.Local))
	if slot >= 6 {
		return false, errors.New("enemy count slot")
	}
	side, raw := site.Side, s.Rounds.Slots[site.Side][slot]
	if site.Guard {
		if m.Read16(0x1e880+0x6fb4) != s.Alias {
			return false, errors.New("enemy shifted alias changed")
		}
		if slot == 0 {
			if s.Alias >= 12 {
				return false, errors.New("enemy shifted alias outside two armies")
			}
			side, raw = int(s.Alias/6), s.Alias%6
		} else {
			raw = s.Rounds.Slots[0][slot-1]
		}
	}
	index := uint16(raw)
	if site.Guard {
		index += uint16(side * 6)
	}
	if m.CPU.R[dg.BX] != index*4 {
		return false, errors.New("enemy count raw mapping")
	}
	value := uint16(s.Rows[side][raw].Count)
	if site.Read {
		reg := dg.AX
		if site.SI {
			reg = dg.SI
		}
		m.CPU.R[reg] = value
		m.CPU.IP += 4
	} else {
		m.CPU.Flags = roundSubFlags(m.CPU.Flags, value, 0)
		m.CPU.IP += 5
	}
	m.CPU.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) gate(m *dg.Machine) (bool, error) {
	if err := s.wrapper(m, 0xf6b); err != nil {
		return false, err
	}
	n := m.CPU.R[dg.DX]
	if s.Record.Selector != 3 || n >= 50 || (s.Record.GateSeen && s.Record.Gate != n) {
		return false, errors.New("enemy assassination gate")
	}
	s.Record.GateSeen = true
	s.Record.Gate = n
	return false, nil
}
func (s *originalBattleEnemy) effect(m *dg.Machine, ip uint16) (bool, error) {
	if err := s.check(m, ip, 0x1f266, 0x1fa29); err != nil {
		return false, err
	}
	direct := ip == 0x38cc
	start, end := 0x21c36, 0x21e3c
	if direct {
		start, end = 0x21e3c, 0x21ea0
	}
	if err := s.Rounds.Actions.check(m, ip, start, end); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	sel := s.Record.Selector
	if !s.Active || c.R[dg.BP] != s.EntrySP-2 || sp > 65510 || m.Read16(0x1e880+sp+2) != 0xf67 {
		return false, errors.New("enemy impact entry frame")
	}
	ret, source, target := m.Read16(0x1e880+sp), m.Read16(0x1e880+sp+4), m.Read16(0x1e880+sp+6)
	if source != s.Record.SourceSlot || target >= 6 || (direct && (sel != 7 || ret != 0x141d)) || (!direct && ((sel == 1 && ret != 0xe51) || (sel != 1 && (sel == 4 || sel == 6 || sel == 7 || ret != 0xe0d)))) {
		return false, errors.New("enemy impact caller/selector")
	}
	raw := s.Rounds.Slots[0][target]
	row := s.Rows[0][raw]
	amount, err := originalEnemyAmount(sel, s.Record.Kind, row.Count)
	if err != nil {
		return false, err
	}
	if sel == 2 {
		kind := s.Rounds.Actions.Setup.Catalog.Profiles[row.Unit].NativeKind
		if kind < 6 || kind > 15 {
			return false, errors.New("enemy exorcism class")
		}
	}
	if sel == 3 && (!s.Record.GateSeen || uint32(s.Record.Gate) >= uint32(m.Read16(0x1e880+0x26ae))*10+10) {
		return false, errors.New("enemy assassination outcome")
	}
	if m.Read16(0x1e880+0x8cb2) != amount {
		return false, errors.New("Go/original enemy amount differs")
	}
	if s.Current != nil {
		e := s.Current
		if s.EffectSP == c.R[dg.SP] && s.EffectBP == c.R[dg.BP] && s.EffectReturn == ret && e.Source == source && e.Target == target && e.Amount == amount && e.Before == row.Count && e.Updates == 0 && len(e.Display) == 0 && s.ClearStage == 0 {
			return false, nil
		}
		return false, errors.New("enemy overlapping impact")
	}
	m.Write16(0x1e880+0x8cb2, amount)
	e := &originalSpellEffect{Selector: sel, Source: source, Target: target, Raw: raw, Amount: amount, Before: row.Count, After: row.Count - min(row.Count, uint32(amount))}
	if !direct {
		first := row.Count
		if e.After == 0 {
			first = min(row.Count, 5)
		} else if amount >= 5 {
			first = e.After + 5
		}
		for n := int(first); n >= int(e.After); n-- {
			e.Planned = append(e.Planned, uint16(n))
		}
	}
	s.Current = e
	s.EffectSP, s.EffectBP, s.EffectReturn = c.R[dg.SP], c.R[dg.BP], ret
	s.Direct = direct
	s.ClearStage = 0
	return false, nil
}
func (s *originalBattleEnemy) impactSite(m *dg.Machine, ip uint16) error {
	if err := s.check(m, ip, 0x1f266, 0x1fa29); err != nil {
		return err
	}
	start, end := 0x21c36, 0x21e3c
	if s.Direct {
		start, end = 0x21e3c, 0x21ea0
	}
	if err := s.Rounds.Actions.check(m, ip, start, end); err != nil {
		return err
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	e := s.Current
	if !s.Active || e == nil || bp != uint32(s.EffectSP)-2 || bp < 16 || m.Read16(0x1e880+bp) != s.EffectBP || m.Read16(0x1e880+bp+2) != s.EffectReturn || m.Read16(0x1e880+bp+4) != 0xf67 {
		return errors.New("enemy impact frame")
	}
	return nil
}
func (s *originalBattleEnemy) impactRead(m *dg.Machine, ip uint16) (bool, error) {
	if err := s.impactSite(m, ip); err != nil {
		return false, err
	}
	e := s.Current
	c := m.CPU
	if e.Updates != 0 {
		return false, errors.New("enemy count read after commit")
	}
	if s.Direct {
		if c.R[dg.SI] != 0x56ea+e.Raw*4 {
			return false, errors.New("enemy direct count pointer")
		}
		c.R[dg.AX] = uint16(e.Before)
		c.IP += 2
	} else {
		if c.R[dg.BX] != e.Raw*4 {
			return false, errors.New("enemy impact count index")
		}
		c.R[dg.SI] = uint16(e.Before)
		c.IP += 4
	}
	c.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) impactWrite(m *dg.Machine, ip uint16) (bool, error) {
	if err := s.impactSite(m, ip); err != nil {
		return false, err
	}
	e := s.Current
	c := m.CPU
	offset := int(e.Raw) * 4
	length := uint16(4)
	if e.Updates != 0 {
		return false, errors.New("enemy count write after commit")
	}
	switch ip {
	case 0x37b0, 0x3850:
		if c.R[dg.BX] != e.Raw*4 || len(e.Display) >= len(e.Planned) || c.R[dg.AX] != e.Planned[len(e.Display)] {
			return false, errors.New("enemy display sequence")
		}
		e.Display = append(e.Display, c.R[dg.AX])
		offset += 2
	case 0x38a5, 0x38a9, 0x390f, 0x3913:
		stage := uint16(0)
		if ip == 0x38a9 || ip == 0x3913 {
			stage = 1
			offset += 2
		}
		if e.After != 0 || s.ClearStage != stage || c.R[dg.AX] != 0 || c.R[dg.SI] != e.Raw*4 {
			return false, errors.New("enemy death clear sequence")
		}
		s.ClearStage++
	case 0x38fc:
		if !s.Direct || e.After == 0 || c.R[dg.SI] != 0x56ea+e.Raw*4 || uint32(c.R[dg.AX]) != e.After {
			return false, errors.New("enemy direct reduction")
		}
		offset += 2
		length = 2
	default:
		return false, fmt.Errorf("unknown enemy write %04X", ip)
	}
	// Expanded player rows retain zero native kind/count, including animation.
	if s.Rounds.Actions.Setup.Catalog.Profiles[s.Rows[0][e.Raw].Unit].NativeKind != 0 {
		m.Write16(0x1e880+0x56e8+uint32(offset), c.R[dg.AX])
		binary.LittleEndian.PutUint16(s.Projected[offset:offset+2], c.R[dg.AX])
	}
	c.IP += length
	c.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) impactCommit(m *dg.Machine, ip uint16) (bool, error) {
	if err := s.impactSite(m, ip); err != nil {
		return false, err
	}
	e := s.Current
	if e.Updates == 1 {
		if s.Rows[0][e.Raw].Count != e.After {
			return false, errors.New("enemy committed count changed")
		}
		return false, nil
	}
	if (!s.Direct && len(e.Display) != len(e.Planned)) || (e.After == 0 && s.ClearStage != 2) || (e.After > 0 && s.ClearStage != 0) {
		return false, errors.New("enemy impact incomplete")
	}
	s.Rows[0][e.Raw].Count = e.After
	e.Updates = 1
	return false, nil
}
func (s *originalBattleEnemy) impactReturn(m *dg.Machine, ip uint16) (bool, error) {
	if err := s.wrapper(m, ip); err != nil {
		return false, err
	}
	e := s.Current
	if e == nil || ip != s.EffectReturn || m.CPU.R[dg.SP] != s.EffectSP+4 || e.Updates != 1 {
		return false, errors.New("enemy effect return")
	}
	s.Record.Effects = append(s.Record.Effects, *e)
	s.Current = nil
	return false, nil
}
func (s *originalBattleEnemy) counter(m *dg.Machine, ip uint16) (bool, error) {
	start, end := 0x1fb6c, 0x1ff1b
	if ip == 0x2184 {
		start, end = 0x206da, 0x20724
	}
	if ip == 0xfa9 {
		start, end = 0x1f266, 0x1fa29
	}
	if err := s.check(m, ip, start, end); err != nil {
		return false, err
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	bx := c.R[dg.BX]
	if bx%2 != 0 || bx/2 >= 6 || bp < 20 || bp > 65520 {
		return false, errors.New("enemy counter index/frame")
	}
	raw := int(bx / 2)
	n := s.Counters[raw]
	length := uint16(4)
	switch ip {
	case 0x2184:
		if m.Read16(0x1e880+bp+2) != 0x20dc || m.Read16(0x1e880+bp+4) != 0xf67 || int(m.Read16(0x1e880+bp-4)) != raw || raw != s.InitIndex {
			return false, errors.New("enemy counter init order/caller")
		}
		n = 1
		s.InitIndex = (s.InitIndex + 1) % 6
		s.Mask |= 1 << raw
		length = 6
	case 0xfa9:
		if !s.Active || s.Record.Selector != 4 || bp != uint32(s.EntrySP)-2 || s.Mask != 63 || s.Record.FreezeWrites >= 6 || int(m.Read16(0x1e880+bp-12)) != s.Record.FreezeWrites || s.Rounds.Slots[1][s.Record.FreezeWrites] != uint16(raw) || n == 65535 {
			return false, errors.New("enemy extra action phase/order")
		}
		n++
		s.Record.FreezeWrites++
		f := roundSubFlags(c.Flags, n, 0) &^ uint16(0x810)
		if n&15 == 0 {
			f |= 0x10
		}
		if n == 0x8000 {
			f |= 0x800
		}
		c.Flags = (f &^ 1) | (c.Flags & 1)
	case 0x165b, 0x187c, 0x1699, 0x189d:
		if s.Mask != 63 || m.Read16(0x1e880+bp+2) != 0x219a || m.Read16(0x1e880+bp+4) != 0xf67 {
			return false, errors.New("enemy counter caller")
		}
		slot := m.Read16(0x1e880 + bp - 6)
		if slot >= 6 || s.Rounds.Slots[1][slot] != uint16(raw) {
			return false, errors.New("enemy counter map")
		}
		if ip == 0x165b || ip == 0x187c {
			c.Flags = roundSubFlags(c.Flags, n, 0)
			c.IP += 5
			c.Cycles++
			s.CounterReads++
			return true, nil
		}
		if n == 0 {
			return false, errors.New("enemy counter underflow")
		}
		cf := c.Flags & 1
		c.Flags = (roundSubFlags(c.Flags, n, 1) &^ 1) | cf
		n--
		s.CounterConsumes++
	default:
		return false, errors.New("unknown enemy counter")
	}
	m.Write16(0x1e880+0x8e78+uint32(raw*2), n)
	s.Counters[raw] = n
	c.IP += length
	c.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) clonePlan(m *dg.Machine) (bool, error) {
	if err := s.wrapper(m, 0x10c1); err != nil {
		return false, err
	}
	bp := uint32(m.CPU.R[dg.BP])
	slot := m.Read16(0x1e880 + bp - 8)
	if s.Record.Selector != 6 || s.Record.Clone != nil || slot >= 6 {
		return false, errors.New("enemy clone phase")
	}
	raw := s.Rounds.Slots[1][slot]
	row := s.Rows[1][raw]
	scaled, after, factor, err := originalClonePlan(s.Record.Kind, row.Count)
	if err != nil {
		return false, err
	}
	if uint32(m.Read16(0x1e880+bp-18)) != row.Count || m.Read16(0x1e880+bp-2) != factor || uint32(m.CPU.R[dg.AX]) != scaled {
		return false, errors.New("Go/original enemy clone plan")
	}
	c := &originalCloneRecord{Unit: row.Unit, Raw: raw, Target: slot, CasterKind: s.Record.Kind, Before: row.Count, Scaled: scaled, After: after}
	for n := row.Count; n <= scaled; n++ {
		c.Planned = append(c.Planned, uint16(n))
	}
	s.Record.Clone = c
	m.Write16(0x1e880+bp-18, uint16(scaled))
	m.CPU.IP += 3
	m.CPU.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) cloneWrite(m *dg.Machine) (bool, error) {
	if err := s.wrapper(m, 0x10f4); err != nil {
		return false, err
	}
	c := s.Record.Clone
	if s.Record.Selector != 6 || c == nil || c.Updates != 0 || m.CPU.R[dg.BX] != c.Raw*4 || len(c.Display) >= len(c.Planned) || m.CPU.R[dg.AX] != c.Planned[len(c.Display)] {
		return false, errors.New("enemy clone display")
	}
	at := 24 + int(c.Raw)*4 + 2
	m.Write16(0x1e880+0x56e8+uint32(at), m.CPU.R[dg.AX])
	binary.LittleEndian.PutUint16(s.Projected[at:at+2], m.CPU.R[dg.AX])
	c.Display = append(c.Display, m.CPU.R[dg.AX])
	m.CPU.IP += 4
	m.CPU.Cycles++
	return true, nil
}
func (s *originalBattleEnemy) cloneCommit(m *dg.Machine) (bool, error) {
	if err := s.wrapper(m, 0x112f); err != nil {
		return false, err
	}
	c := s.Record.Clone
	if s.Record.Selector != 6 || c == nil || len(c.Display) != len(c.Planned) {
		return false, errors.New("enemy clone incomplete")
	}
	if c.Updates == 1 {
		if s.Rows[1][c.Raw].Count != c.After {
			return false, errors.New("enemy clone committed count changed")
		}
		return false, nil
	}
	s.Rows[1][c.Raw].Count = c.After
	c.Updates = 1
	return false, nil
}
func (s *originalBattleEnemy) finish(m *dg.Machine) (bool, error) {
	if !s.Active {
		if s.Hold && len(s.Records) > 0 {
			if err := s.check(m, 0x190a, 0x1fb6c, 0x1ff1b); err != nil {
				return false, err
			}
			if m.CPU.R[dg.SP] != s.EntrySP+4 || m.CPU.R[dg.BP] != s.EntryBP {
				return false, errors.New("enemy held frame")
			}
			return false, errOriginalEnemyHeld
		}
		return false, nil
	}
	if err := s.check(m, 0x190a, 0x1f266, 0x1fa29); err != nil {
		return false, err
	}
	if s.Current != nil || m.CPU.R[dg.SP] != s.EntrySP+4 || m.CPU.R[dg.BP] != s.EntryBP || s.Record.Selector < 0 || (s.Record.Selector == 4 && s.Record.FreezeWrites != 6) || (s.Record.Selector == 6 && (s.Record.Clone == nil || s.Record.Clone.Updates != 1)) {
		return false, errors.New("enemy wrapper result incomplete")
	}
	s.Record.AfterCounters = s.Counters
	s.Record.SeedAfter = originalSeed(s.Engine.Oracle)
	s.Records = append(s.Records, s.Record)
	s.Rounds.Rows, s.Rounds.Projected = s.Rows, s.Projected
	s.Active = false
	if s.Hold {
		return false, errOriginalEnemyHeld
	}
	return false, nil
}
func installOriginalBattleEnemy(e *game.Engine, r *originalBattleRounds) (*originalBattleEnemy, error) {
	if r == nil || r.EnemySpells != nil || r.Active {
		return nil, errors.New("enemy special install lifecycle")
	}
	s := &originalBattleEnemy{Engine: e, Rounds: r}
	r.EnemySpells = s
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0xcf6), s.begin)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0xd96), s.dispatch)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0xf6b), s.gate)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x190a), s.finish)
	for _, site := range originalEnemyReads {
		site := site
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, uint16(site.IDA-0x1e570)), func(m *dg.Machine) (bool, error) { return s.read(m, site) })
	}
	for _, ip := range []uint16{0x36c6, 0x38cc} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.effect(m, ip) })
	}
	for _, ip := range []uint16{0x375c, 0x380f, 0x38ef} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.impactRead(m, ip) })
	}
	for _, ip := range []uint16{0x37b0, 0x3850, 0x38a5, 0x38a9, 0x38fc, 0x390f, 0x3913} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.impactWrite(m, ip) })
	}
	for _, ip := range []uint16{0x38ad, 0x3917} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.impactCommit(m, ip) })
	}
	for _, ip := range []uint16{0xe0d, 0xe51, 0x141d} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.impactReturn(m, ip) })
	}
	for _, ip := range []uint16{0x2184, 0xfa9, 0x165b, 0x187c, 0x1699, 0x189d} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.counter(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x10c1), s.clonePlan)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x10f4), s.cloneWrite)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x112f), s.cloneCommit)
	return s, nil
}
