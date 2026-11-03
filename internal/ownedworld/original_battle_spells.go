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

var errOriginalSpellHeld = errors.New("Go player spell completed; held before next action")

type originalSpellEffect struct {
	Selector            int `json:"selector"`
	Source, Target, Raw uint16
	Amount              uint16
	Before, After       uint32
	Display, Planned    []uint16
	Updates             uint64
}
type originalSpellRecord struct {
	Selector                    int
	Caster                      uint16
	Effects                     []originalSpellEffect
	BeforeCharges, AfterCharges [8]uint16
	Random                      *originalRandPlan
}
type originalBattleSpells struct {
	Engine                           *game.Engine
	Rounds                           *originalBattleRounds
	Active, Hold                     bool
	Rows                             [2][6]ArmyStack
	Projected                        [48]byte
	EntrySP, EntryBP, Caster         uint16
	Selector                         int
	Consumed                         bool
	Charges                          [8]uint16
	Random                           *originalRandPlan
	Current                          *originalSpellEffect
	EffectSP, EffectBP, EffectReturn uint16
	Direct                           bool
	ClearStage                       uint16
	Effects                          []originalSpellEffect
	Records                          []originalSpellRecord
}

func spellSupported(n int) bool { return n == 0 || n == 1 || n == 2 || n == 3 || n == 5 || n == 7 }

func originalSpellAmount(selector int, kind uint16, source, target uint32, hp uint64, targetKind uint16, stat uint16) (uint16, error) {
	var amount, term, factor uint64
	if !spellSupported(selector) || source == 0 || source > 32767 || target == 0 || target > 32767 || (kind != 10 && kind != 12) {
		return 0, errors.New("spell amount identity/word bounds")
	}
	switch selector {
	case 0, 1, 2:
		factor = uint64(stat)*5 + 5
		if kind == 12 {
			factor = uint64(stat)*2 + 2
		}
		term = uint64(source/3 + 1)
		if selector == 2 {
			factor = uint64(stat)*10 + 10
			if kind == 12 {
				factor = uint64(stat)*4 + 6
			}
			term = uint64(source) + 1
		}
		if selector == 2 && (targetKind < 6 || targetKind > 15) {
			amount = factor
		} else {
			if hp/10 == 0 || term*factor > 65535 {
				return 0, errors.New("spell factor/divisor range")
			}
			amount = term*factor/(hp/10) + 2
		}
	case 3:
		amount = uint64(target)
	case 5:
		amount = uint64(target/2 + 1)
	case 7:
		if target < 50 {
			amount = uint64(target)
		} else {
			if uint64(target)*6 > 65535 {
				return 0, errors.New("quake product range")
			}
			divisor := uint64(10)
			if kind == 12 {
				divisor = 20
			}
			amount = uint64(target)*6/divisor + uint64(stat)*10 + 1
		}
	}
	if amount > 65535 {
		return 0, errors.New("spell amount overflow")
	}
	return uint16(amount), nil
}

func (p *originalBattleSpells) projection(m *dg.Machine) error {
	r := p.Rounds
	if !bytes.Equal(p.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718]) || !bytes.Equal(r.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0]) || !bytes.Equal(r.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c]) {
		return errors.New("spell projection changed")
	}
	return nil
}
func (p *originalBattleSpells) check(m *dg.Machine, ip uint16) error {
	if !p.Active || !p.Rounds.Active || p.Rounds.Done {
		return errors.New("spell lifecycle")
	}
	return p.Rounds.Actions.check(m, ip, 0x1e8a4, 0x1f265)
}
func (p *originalBattleSpells) begin(m *dg.Machine) (bool, error) {
	r := p.Rounds
	if err := r.Actions.check(m, 0x334, 0x1e8a4, 0x1f265); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if !r.Active || r.Done || p.Active || r.Sorting != -1 || r.Actions.Casualties.Started || sp > 65520 || m.Read16(0x1e880+sp) != 0x1cfe || m.Read16(0x1e880+sp+2) != 0xf67 {
		return false, errors.New("spell entry frame")
	}
	slot := m.Read16(0x1e880 + sp + 4)
	if slot < 3 || slot >= 6 {
		return false, errors.New("spell caster slot")
	}
	s := r.Rows[0][r.Slots[0][slot]]
	profile := r.Actions.Setup.Catalog.Profiles[s.Unit]
	if s.Count == 0 || s.Count > 32767 || (profile.NativeKind != 10 && profile.NativeKind != 12) {
		return false, errors.New("spell caster identity")
	}
	for _, s := range r.Rows[1] {
		if s.Count > 0 && r.Actions.Setup.Catalog.Profiles[s.Unit].NativeKind == 0 {
			return false, errors.New("extended enemy spell path not admitted")
		}
	}
	p.Rows, p.Projected = r.Rows, r.Projected
	p.EntrySP, p.EntryBP, p.Caster = c.R[dg.SP], c.R[dg.BP], slot
	p.Selector = -1
	p.Consumed = false
	p.Random = nil
	p.Effects = nil
	p.Current = nil
	for i := range p.Charges {
		p.Charges[i] = m.Read16(0x1e880 + 0x2aa8 + uint32(i*2))
	}
	p.Active = true
	return false, nil
}
func (p *originalBattleSpells) consume(m *dg.Machine) (bool, error) {
	if err := p.check(m, 0x31e); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if sp > 65525 || m.Read16(0x1e880+sp) != 0x2cc || m.Read16(0x1e880+sp+2) != 0xf67 || m.Read16(0x1e880+uint32(c.R[dg.BP])) != p.EntrySP-2 {
		return false, errors.New("spell charge caller")
	}
	selector := int(m.Read16(0x1e880 + sp + 4))
	if p.Consumed || !spellSupported(selector) || p.Charges[selector] == 0 {
		return false, errors.New("spell selection not admitted")
	}
	if !bytes.Equal(p.Rounds.Actions.Setup.Code[0xe88e:0xe8a3], m.Mem[0xf670+0x31e:0xf670+0x333]) {
		return false, errors.New("spell charge source")
	}
	for i, n := range p.Charges {
		if m.Read16(0x1e880+0x2aa8+uint32(i*2)) != n {
			return false, errors.New("spell charge binding")
		}
	}
	p.Selector, p.Consumed = selector, true
	m.Write16(0x1e880+0x2aa8+uint32(selector*2), p.Charges[selector]-1)
	c.R[dg.AX] = 0
	c.R[dg.BX] = uint16(selector * 2)
	c.R[dg.SP] += 4
	c.IP = 0x2cc
	c.Cycles++
	return true, nil
}
func (p *originalBattleSpells) assassination(m *dg.Machine) (bool, error) {
	if err := p.check(m, 0x6e4); err != nil {
		return false, err
	}
	if p.Selector != 3 || p.Random != nil || m.CPU.R[dg.BP] != p.EntrySP-2 || m.Read16(0x1e880+0x26ae) > 6552 {
		return false, errors.New("spell assassination phase")
	}
	if err := checkOriginalRand(p.Engine.Oracle, p.Rounds.Actions.Setup.Code); err != nil {
		return false, err
	}
	plan := planOriginalRand(originalSeed(p.Engine.Oracle))
	p.Random = &plan
	m.Write16(0x1e880+0x81bc, uint16(plan.After))
	m.Write16(0x1e880+0x81be, uint16(plan.After>>16))
	m.CPU.R[dg.AX] = plan.Value
	m.CPU.IP += 5
	m.CPU.Cycles++
	return true, nil
}
func (p *originalBattleSpells) effect(m *dg.Machine, ip uint16) (bool, error) {
	if err := p.check(m, ip); err != nil {
		return false, err
	}
	start, end := 0x219cc, 0x21bd2
	direct := ip == 0x3662
	if direct {
		start, end = 0x21bd2, 0x21c36
	}
	if err := p.Rounds.Actions.check(m, ip, start, end); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if p.Current != nil || !p.Consumed || sp > 65515 || m.Read16(0x1e880+sp+2) != 0xf67 || c.R[dg.BP] != p.EntrySP-2 {
		return false, errors.New("spell effect frame")
	}
	ret, source, target := m.Read16(0x1e880+sp), m.Read16(0x1e880+sp+4), m.Read16(0x1e880+sp+6)
	if source != p.Caster || target >= 6 || (direct && (p.Selector != 7 || ret != 0xc59)) || (!direct && ((p.Selector == 1 && ret != 0x516) || (p.Selector != 1 && (p.Selector == 7 || ret != 0x74a)))) {
		return false, errors.New("spell effect caller/selector")
	}
	raw := p.Rounds.Slots[1][target]
	s := p.Rows[0][p.Rounds.Slots[0][source]]
	t := p.Rows[1][raw]
	caster := p.Rounds.Actions.Setup.Catalog.Profiles[s.Unit]
	profile := p.Rounds.Actions.Setup.Catalog.Profiles[t.Unit]
	if profile.NativeKind == 0 || uint64(m.Read16(0x1e880+0x70d0+uint32(profile.NativeKind)*4)) != profile.HP {
		return false, errors.New("spell target profile binding")
	}
	amount, err := originalSpellAmount(p.Selector, caster.NativeKind, s.Count, t.Count, profile.HP, profile.NativeKind, m.Read16(0x1e880+0x26b0))
	if err != nil {
		return false, err
	}
	if p.Selector == 3 && (p.Random == nil || uint32(p.Random.Value%50) >= uint32(m.Read16(0x1e880+0x26ae))*10+10) {
		return false, errors.New("spell assassination result")
	}
	if m.Read16(0x1e880+0x8e76) != amount {
		return false, errors.New("Go/original spell amount differs")
	}
	// This Go result is authoritative. Original intermediate arithmetic is
	// retained only as a bounded compatibility check for these native targets.
	m.Write16(0x1e880+0x8e76, amount)
	e := &originalSpellEffect{Selector: p.Selector, Source: source, Target: target, Raw: raw, Amount: amount, Before: t.Count, After: t.Count - min(t.Count, uint32(amount))}
	if !direct {
		start := t.Count
		if e.After == 0 {
			start = min(t.Count, 5)
		} else if amount >= 5 {
			start = e.After + 5
		}
		for n := int(start); n >= int(e.After); n-- {
			e.Planned = append(e.Planned, uint16(n))
		}
	}
	p.Current = e
	p.EffectSP, p.EffectBP, p.EffectReturn = c.R[dg.SP], c.R[dg.BP], ret
	p.Direct = direct
	p.ClearStage = 0
	return false, nil
}
func (p *originalBattleSpells) effectSite(m *dg.Machine, ip uint16) error {
	if err := p.check(m, ip); err != nil {
		return err
	}
	e := p.Current
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	start, end := 0x219cc, 0x21bd2
	if p.Direct {
		start, end = 0x21bd2, 0x21c36
	}
	if err := p.Rounds.Actions.check(m, ip, start, end); err != nil {
		return err
	}
	if e == nil || e.Updates != 0 || bp != uint32(p.EffectSP)-2 || bp < 16 || m.Read16(0x1e880+bp) != p.EffectBP || m.Read16(0x1e880+bp+2) != p.EffectReturn || m.Read16(0x1e880+bp+4) != 0xf67 {
		return errors.New("spell impact frame")
	}
	return nil
}
func (p *originalBattleSpells) read(m *dg.Machine, ip uint16) (bool, error) {
	if err := p.effectSite(m, ip); err != nil {
		return false, err
	}
	e := p.Current
	reg := dg.SI
	at := m.CPU.R[dg.BX]
	if p.Direct {
		reg = dg.AX
		if m.CPU.R[dg.SI] != 0x5702+e.Raw*4 {
			return false, errors.New("spell direct count pointer")
		}
	} else if at != e.Raw*4 {
		return false, errors.New("spell count index")
	}
	m.CPU.R[reg] = uint16(e.Before)
	m.CPU.IP += 4
	if p.Direct {
		m.CPU.IP -= 2
	}
	m.CPU.Cycles++
	return true, nil
}
func (p *originalBattleSpells) write(m *dg.Machine, ip uint16) (bool, error) {
	if err := p.effectSite(m, ip); err != nil {
		return false, err
	}
	e := p.Current
	c := m.CPU
	offset := 24 + int(e.Raw)*4
	length := uint16(4)
	switch ip {
	case 0x3546, 0x35e6: // 21AB6 / 21B56: animation-only counts.
		if c.R[dg.BX] != e.Raw*4 || len(e.Display) >= len(e.Planned) || c.R[dg.AX] != e.Planned[len(e.Display)] {
			return false, errors.New("spell display sequence")
		}
		e.Display = append(e.Display, c.R[dg.AX])
		offset += 2
	case 0x363b, 0x363f, 0x36a5, 0x36a9: // death writes: 21BAB/21BAF or 21C15/21C19
		stage := uint16(0)
		if ip == 0x363f || ip == 0x36a9 {
			stage = 1
			offset += 2
		}
		if e.After != 0 || p.ClearStage != stage || c.R[dg.AX] != 0 || c.R[dg.SI] != e.Raw*4 {
			return false, errors.New("spell clear sequence")
		}
		p.ClearStage++
	case 0x3692: // 21C02 partial direct reduction
		if !p.Direct || e.After == 0 || c.R[dg.SI] != 0x5702+e.Raw*4 || uint32(c.R[dg.AX]) != e.After {
			return false, errors.New("spell direct write")
		}
		offset += 2
		length = 2
	default:
		return false, fmt.Errorf("unknown spell write %04X", ip)
	}
	m.Write16(0x1e880+0x56e8+uint32(offset), c.R[dg.AX])
	binary.LittleEndian.PutUint16(p.Projected[offset:offset+2], c.R[dg.AX])
	c.IP += length
	c.Cycles++
	return true, nil
}
func (p *originalBattleSpells) commit(m *dg.Machine, ip uint16) (bool, error) {
	if err := p.effectSite(m, ip); err != nil {
		return false, err
	}
	e := p.Current
	if e.Updates != 0 || (!p.Direct && len(e.Display) != len(e.Planned)) || (e.After == 0 && p.ClearStage != 2) || (e.After > 0 && p.ClearStage != 0) {
		return false, errors.New("spell effect incomplete")
	}
	p.Rows[1][e.Raw].Count = e.After
	e.Updates = 1
	return false, nil
}
func (p *originalBattleSpells) effectReturn(m *dg.Machine, ip uint16) (bool, error) {
	if err := p.check(m, ip); err != nil {
		return false, err
	}
	e := p.Current
	if e == nil || ip != p.EffectReturn || m.CPU.R[dg.SP] != p.EffectSP+4 || m.CPU.R[dg.BP] != p.EffectBP || e.Updates != 1 {
		return false, errors.New("spell effect return")
	}
	p.Effects = append(p.Effects, *e)
	p.Current = nil
	return false, nil
}
func (p *originalBattleSpells) finish(m *dg.Machine) (bool, error) {
	if !p.Active {
		if p.Hold && len(p.Records) > 0 {
			if err := p.Rounds.Actions.check(m, 0x1cfe, 0x1ff1c, 0x2031a); err != nil {
				return false, err
			}
			if m.CPU.R[dg.SP] != p.EntrySP+4 || m.CPU.R[dg.BP] != p.EntryBP {
				return false, errors.New("spell held return frame")
			}
			return false, errOriginalSpellHeld
		}
		return false, nil
	}
	if err := p.check(m, 0x1cfe); err != nil {
		return false, err
	}
	if p.Current != nil || m.CPU.R[dg.SP] != p.EntrySP+4 || m.CPU.R[dg.BP] != p.EntryBP {
		return false, errors.New("spell wrapper return")
	}
	var after [8]uint16
	for i, before := range p.Charges {
		after[i] = m.Read16(0x1e880 + 0x2aa8 + uint32(i*2))
		if int(i) != p.Selector && after[i] != before || int(i) == p.Selector && (after[i] > before || before-after[i] > 1) {
			return false, errors.New("spell final charges")
		}
	}
	p.Records = append(p.Records, originalSpellRecord{p.Selector, p.Caster, p.Effects, p.Charges, after, p.Random})
	p.Rounds.Rows, p.Rounds.Projected = p.Rows, p.Projected
	p.Active = false
	if p.Hold {
		return false, errOriginalSpellHeld
	}
	return false, nil
}
func installOriginalBattleSpells(e *game.Engine, r *originalBattleRounds) (*originalBattleSpells, error) {
	if r == nil || r.Spells != nil || r.Active {
		return nil, errors.New("spell install lifecycle")
	}
	p := &originalBattleSpells{Engine: e, Rounds: r, Selector: -1}
	r.Spells = p
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x31e), p.consume)
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x6e4), p.assassination)
	for _, ip := range []uint16{0x345c, 0x3662} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return p.effect(m, ip) })
	}
	for _, ip := range []uint16{0x34f2, 0x35a5, 0x3685} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return p.read(m, ip) })
	}
	for _, ip := range []uint16{0x3546, 0x35e6, 0x363b, 0x363f, 0x3692, 0x36a5, 0x36a9} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return p.write(m, ip) })
	}
	for _, ip := range []uint16{0x3643, 0x36ad} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return p.commit(m, ip) })
	}
	for _, ip := range []uint16{0x74a, 0x516, 0xc59} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return p.effectReturn(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x1cfe), p.finish)
	return p, nil
}
