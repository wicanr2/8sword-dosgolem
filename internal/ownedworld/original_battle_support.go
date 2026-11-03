package ownedworld

import (
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type originalCloneRecord struct {
	Unit                    string
	Raw, Target, CasterKind uint16
	Before, Scaled, After   uint32
	Planned, Display        []uint16
	Updates                 uint64
}
type originalSupportRecord struct {
	Selector      int
	Before, After [6]uint16
	FreezeWrites  int
	Clone         *originalCloneRecord
}
type originalBattleSupport struct {
	Spells                      *originalBattleSpells
	Counters, Before            [6]uint16
	Mask                        uint8
	InitIndex, FreezeIndex      int
	InitWrites, Consumes, Reads uint64
	Clone                       *originalCloneRecord
	Growth                      [6]uint32
	Records                     []originalSupportRecord
}

func originalClonePlan(kind uint16, count uint32) (uint32, uint32, uint16, error) {
	if (kind != 10 && kind != 12) || count == 0 || count > 32767 {
		return 0, 0, 0, errors.New("clone identity/count")
	}
	factor := uint32(10)
	switch {
	case count < 50:
		factor = 20
	case count < 100:
		factor = 14
	case count < 200:
		factor = 13
	case count < 300:
		factor = 12
	case count < 400:
		factor = 11
	}
	if uint64(count)*uint64(factor) > 65535 {
		return 0, 0, 0, errors.New("clone original product overflow")
	}
	divisor := uint32(10)
	if kind == 12 {
		divisor = 20
	}
	scaled := count * factor / divisor
	if scaled > 32767 {
		return 0, 0, 0, errors.New("clone display range")
	}
	return scaled, max(scaled, count), uint16(factor), nil
}

func (s *originalBattleSupport) projection(m *dg.Machine) error {
	for i, n := range s.Counters {
		if s.Mask&(1<<i) != 0 && m.Read16(0x1e880+0x8e46+uint32(i*2)) != n {
			return errors.New("Go action counter projection changed")
		}
	}
	return nil
}
func (s *originalBattleSupport) start() {
	s.Before = s.Counters
	s.FreezeIndex = 0
	s.Clone = nil
}
func (s *originalBattleSupport) check(m *dg.Machine, ip uint16, start, end int) error {
	r := s.Spells.Rounds
	if !r.Active || r.Done {
		return errors.New("support battle lifecycle")
	}
	if err := r.Actions.check(m, ip, start, end); err != nil {
		return err
	}
	return s.projection(m)
}
func (s *originalBattleSupport) counter(m *dg.Machine, ip uint16) (bool, error) {
	start, end := 0x1ff1c, 0x20319
	if ip == 0x2134 {
		start, end = 0x2068a, 0x206da
	}
	if ip == 0x771 {
		start, end = 0x1e8a4, 0x1f265
	}
	if err := s.check(m, ip, start, end); err != nil {
		return false, err
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	bx := c.R[dg.BX]
	if bx%2 != 0 || bx/2 >= 6 || bp < 20 || bp > 65520 {
		return false, errors.New("support counter frame/index")
	}
	raw := int(bx / 2)
	value := s.Counters[raw]
	length := uint16(4)
	switch ip {
	case 0x2134: // sub_2068A: initialize every raw row before player half.
		if m.Read16(0x1e880+bp+2) != 0x20aa || m.Read16(0x1e880+bp+4) != 0xf67 || int(m.Read16(0x1e880+bp-4)) != raw || raw != s.InitIndex {
			return false, errors.New("counter initialization caller/order")
		}
		value = 1
		s.InitIndex = (s.InitIndex + 1) % 6
		s.Mask |= 1 << raw
		s.InitWrites++
		length = 6
	case 0x771: // sub_1E8A4 selector4: preserve duplicate empty raw entries.
		p := s.Spells
		if !p.Active || !p.Consumed || p.Selector != 4 || bp != uint32(p.EntrySP)-2 || s.Mask != 63 || s.FreezeIndex >= 6 || int(m.Read16(0x1e880+bp-12)) != s.FreezeIndex || s.Spells.Rounds.Slots[0][s.FreezeIndex] != uint16(raw) || value == 65535 {
			return false, errors.New("freeze phase/order/bounds")
		}
		value++
		s.FreezeIndex++
		f := roundSubFlags(c.Flags, value, 0) &^ uint16(0x810)
		if value&15 == 0 {
			f |= 0x10
		}
		if value == 0x8000 {
			f |= 0x800
		}
		c.Flags = (f &^ 1) | (c.Flags & 1)
	case 0x1a11, 0x1c5e, 0x1a25, 0x1c7f:
		if s.Mask != 63 || m.Read16(0x1e880+bp+2) != 0x2151 || m.Read16(0x1e880+bp+4) != 0xf67 {
			return false, errors.New("counter consumer caller")
		}
		slot := m.Read16(0x1e880 + bp - 10)
		if slot >= 6 || s.Spells.Rounds.Slots[0][slot] != uint16(raw) {
			return false, errors.New("counter consumer map")
		}
		if ip == 0x1a11 || ip == 0x1c5e {
			c.Flags = roundSubFlags(c.Flags, value, 0)
			c.IP += 5
			c.Cycles++
			s.Reads++
			return true, nil
		}
		if value == 0 {
			return false, errors.New("counter underflow")
		}
		cf := c.Flags & 1
		c.Flags = (roundSubFlags(c.Flags, value, 1) &^ 1) | cf
		value--
		s.Consumes++
	default:
		return false, fmt.Errorf("unknown support counter %04X", ip)
	}
	m.Write16(0x1e880+0x8e46+uint32(raw*2), value)
	s.Counters[raw] = value
	c.IP += length
	c.Cycles++
	return true, nil
}

func (s *originalBattleSupport) cloneSite(m *dg.Machine, ip uint16) error {
	if err := s.check(m, ip, 0x1e8a4, 0x1f265); err != nil {
		return err
	}
	p := s.Spells
	if !p.Active || !p.Consumed || p.Selector != 6 || m.CPU.R[dg.BP] != p.EntrySP-2 {
		return errors.New("clone wrapper phase")
	}
	return nil
}
func (s *originalBattleSupport) clonePlan(m *dg.Machine) (bool, error) {
	if err := s.cloneSite(m, 0x8ed); err != nil {
		return false, err
	}
	p := s.Spells
	bp := uint32(m.CPU.R[dg.BP])
	slot := m.Read16(0x1e880 + bp - 8)
	if s.Clone != nil || slot >= 6 {
		return false, errors.New("clone target lifecycle")
	}
	raw := p.Rounds.Slots[0][slot]
	row := p.Rows[0][raw]
	target := p.Rounds.Actions.Setup.Catalog.Profiles[row.Unit]
	caster := p.Rounds.Actions.Setup.Catalog.Profiles[p.Rows[0][p.Rounds.Slots[0][p.Caster]].Unit]
	if target.NativeKind < 1 || target.NativeKind > 25 {
		return false, errors.New("extended clone target not admitted")
	}
	scaled, after, factor, err := originalClonePlan(caster.NativeKind, row.Count)
	if err != nil {
		return false, err
	}
	if uint32(m.Read16(0x1e880+bp-18)) != row.Count || m.Read16(0x1e880+bp-2) != factor || uint32(m.CPU.R[dg.AX]) != scaled {
		return false, errors.New("Go/original clone plan differs")
	}
	record := &originalCloneRecord{Unit: row.Unit, Raw: raw, Target: slot, CasterKind: caster.NativeKind, Before: row.Count, Scaled: scaled, After: after}
	for n := row.Count; n <= scaled; n++ {
		record.Planned = append(record.Planned, uint16(n))
	}
	s.Clone = record
	m.Write16(0x1e880+bp-18, uint16(scaled))
	m.CPU.IP += 3
	m.CPU.Cycles++
	return true, nil
}
func (s *originalBattleSupport) cloneWrite(m *dg.Machine) (bool, error) {
	if err := s.cloneSite(m, 0x920); err != nil {
		return false, err
	}
	r := s.Clone
	c := m.CPU
	if r == nil || r.Updates != 0 || c.R[dg.BX] != r.Raw*4 || len(r.Display) >= len(r.Planned) || c.R[dg.AX] != r.Planned[len(r.Display)] {
		return false, errors.New("clone animation sequence")
	}
	p := s.Spells
	at := int(r.Raw)*4 + 2
	value := c.R[dg.AX]
	m.Write16(0x1e880+0x56e8+uint32(at), value)
	p.Projected[at] = byte(value)
	p.Projected[at+1] = byte(value >> 8)
	r.Display = append(r.Display, value)
	c.IP += 4
	c.Cycles++
	return true, nil
}
func (s *originalBattleSupport) cloneCommit(m *dg.Machine) (bool, error) {
	if err := s.cloneSite(m, 0x95b); err != nil {
		return false, err
	}
	r := s.Clone
	if r == nil || r.Updates != 0 || len(r.Display) != len(r.Planned) {
		return false, errors.New("clone incomplete result")
	}
	s.Spells.Rows[0][r.Raw].Count = r.After
	s.Growth[r.Raw] += r.After - r.Before
	r.Updates = 1
	return false, nil
}
func (s *originalBattleSupport) finish() error {
	p := s.Spells
	if p.Selector == 4 && s.FreezeIndex != 6 {
		return errors.New("freeze incomplete result")
	}
	if p.Selector == 6 && s.Clone != nil && s.Clone.Updates != 1 {
		return errors.New("clone result uncommitted")
	}
	s.Records = append(s.Records, originalSupportRecord{p.Selector, s.Before, s.Counters, s.FreezeIndex, s.Clone})
	return nil
}

func installOriginalBattleSupport(e *game.Engine, p *originalBattleSpells) (*originalBattleSupport, error) {
	if p == nil || p.Support != nil || p.Rounds.Active {
		return nil, errors.New("support install lifecycle")
	}
	s := &originalBattleSupport{Spells: p}
	p.Support = s
	for _, ip := range []uint16{0x2134, 0x771, 0x1a11, 0x1c5e, 0x1a25, 0x1c7f} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return s.counter(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x8ed), s.clonePlan)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x920), s.cloneWrite)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x95b), s.cloneCommit)
	return s, nil
}
