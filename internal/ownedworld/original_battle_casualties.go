package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"image"
	"strconv"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalBattleCasualtiesHeld = errors.New("first original enemy melee completed; held before next action")

type originalCasualtyAmount struct {
	Caller                uint16 `json:"caller"`
	Damage                uint64 `json:"damage"`
	Encoded               uint16 `json:"encoded"`
	BeforeHP, AfterHP     uint64
	BeforeWord, AfterWord uint16
}

type originalCasualtyRecord struct {
	Target                  originalEnemyTarget `json:"target"`
	Before, After, Loss     uint32
	Calls                   []originalCasualtyAmount `json:"calls"`
	PlannedDisplay, Display []uint16
	Updates                 uint32 `json:"updates"`
}

// Spec030 READY: one enemy melee, with the original executor and Go counts.
// General player startup, all later actions and world settlement remain held.
type originalBattleCasualties struct {
	Actions                                            *originalBattleActions
	Rows                                               [2][6]ArmyStack
	HP                                                 [2][6]uint64
	Projected                                          [48]byte
	HPWords                                            [24]byte
	Started, Impact, Committed, Complete               bool
	EntrySP, EntryBP, ImpactSP, ImpactBP, ImpactReturn uint16
	ClearStage                                         uint16
	DisplayValue                                       uint32
	Record                                             originalCasualtyRecord
}

func (x *originalBattleCasualties) checkProjection(m *dg.Machine) error {
	if !bytes.Equal(x.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718]) || !bytes.Equal(x.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0]) || !bytes.Equal(x.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c]) {
		return errors.New("Go casualty native projection changed")
	}
	return nil
}

func (x *originalBattleCasualties) enter(m *dg.Machine) (bool, error) {
	a := x.Actions
	c := m.CPU
	if a.Target == nil || a.Target.IP != 0x484c || a.Target.Caller != 0x1818 || !a.Active || x.Complete {
		return false, errors.New("Go casualty unsupported entry")
	}
	if x.Started {
		if c.R[dg.SP] != x.EntrySP || c.R[dg.BP] != x.EntryBP {
			return false, errors.New("Go casualty repeated entry frame")
		}
		return false, nil
	}
	if err := a.check(m, 0x484c, 0x22dbc, 0x23a42); err != nil {
		return false, err
	}
	t := *a.Target
	sp := a.Setup.Catalog.Profiles[t.Source.Unit]
	if sp.NativeKind < 1 || sp.NativeKind > 25 || t.Source.Count > 65535 || t.Target.Count > 32767 || t.Target.Count == 0 {
		return false, errors.New("Go casualty source/count bounds")
	}
	x.Rows, x.HP = a.Setup.Plan.Rows, a.Setup.Plan.HP
	copy(x.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
	copy(x.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0])
	copy(x.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c])
	x.EntrySP, x.EntryBP = c.R[dg.SP], c.R[dg.BP]
	x.Record = originalCasualtyRecord{Target: t, Before: t.Target.Count, After: t.Target.Count}
	x.DisplayValue = t.Target.Count
	x.Started = true
	return false, nil
}

func originalImpactCaller(code []byte, ret uint16) bool {
	if ret != 0x461d && (ret < 0x484c+4 || ret >= 0x54d2) {
		return false
	}
	at := 0xe570 + int(ret) - 4
	return at >= 0 && at+4 <= len(code) && code[at] == 0x0e && code[at+1] == 0xe8 && uint16(int(ret)+int(int16(binary.LittleEndian.Uint16(code[at+2:at+4])))) == 0x4626
}

func (x *originalBattleCasualties) impactEnter(m *dg.Machine) (bool, error) {
	if err := x.Actions.check(m, 0x4626, 0x22b96, 0x22dbc); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	t := x.Record.Target
	if m.Read16(0x1e880+sp) == 0x461d {
		if err := x.Actions.check(m, 0x4626, 0x22af8, 0x22b95); err != nil {
			return false, err
		}
		bp := uint32(c.R[dg.BP])
		if bp < 16 || bp > 65525 || m.Read16(0x1e880+bp) != x.EntrySP-2 || m.Read16(0x1e880+bp+4) != 0xf67 || m.Read16(0x1e880+bp+6) != t.SourceSlot || m.Read16(0x1e880+bp+8) != t.TargetSlot {
			return false, errors.New("Go casualty step wrapper frame")
		}
		ret := m.Read16(0x1e880 + bp + 2)
		if ret < 0x484c+4 || ret >= 0x54d2 {
			return false, errors.New("Go casualty step parent range")
		}
		at := 0xe570 + int(ret) - 4
		code := x.Actions.Setup.Code
		if code[at] != 0x0e || code[at+1] != 0xe8 || uint16(int(ret)+int(int16(binary.LittleEndian.Uint16(code[at+2:at+4])))) != 0x4588 {
			return false, errors.New("Go casualty step parent call")
		}
	}
	if !x.Started || x.Complete || sp > 65511 || len(x.Record.Calls) != 1 || x.Record.Calls[0].Encoded == 1 || m.Read16(0x1e880+sp+2) != 0xf67 || !originalImpactCaller(x.Actions.Setup.Code, m.Read16(0x1e880+sp)) || m.Read16(0x1e880+sp+4) != t.SourceSlot || m.Read16(0x1e880+sp+6) != t.TargetSlot {
		return false, fmt.Errorf("Go casualty nested impact caller/frame SP=%04X ret=%04X CS=%04X args=%04X,%04X calls=%d impact=%v near=%v", sp, m.Read16(0x1e880+sp), m.Read16(0x1e880+sp+2), m.Read16(0x1e880+sp+4), m.Read16(0x1e880+sp+6), len(x.Record.Calls), x.Impact, originalImpactCaller(x.Actions.Setup.Code, m.Read16(0x1e880+sp)))
	}
	if x.Impact {
		if c.R[dg.SP] != x.ImpactSP || c.R[dg.BP] != x.ImpactBP {
			return false, errors.New("Go casualty repeated impact")
		}
		return false, nil
	}
	x.ImpactSP, x.ImpactBP, x.ImpactReturn = c.R[dg.SP], c.R[dg.BP], m.Read16(0x1e880+sp)
	x.Impact = true
	return false, nil
}

func originalCasualtyDisplay(before uint32, encoded uint16) (uint32, []uint16) {
	if encoded == 1 {
		return before, nil
	}
	if uint32(encoded) >= before {
		v := []uint16{}
		for n := int(min(before, 5)); n >= 0; n-- {
			v = append(v, uint16(n))
		}
		return 0, v
	}
	after := before - uint32(encoded) + 1
	start := before
	if encoded >= 5 {
		start = before - uint32(encoded) + 5
	}
	v := []uint16{}
	for n := start; n >= after; n-- {
		v = append(v, uint16(n))
	}
	return after, v
}

func (x *originalBattleCasualties) helper(m *dg.Machine) (bool, error) {
	if err := x.Actions.check(m, 0x1532, 0x1faa2, 0x1fb02); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	t := x.Record.Target
	if !x.Started || x.Committed || x.Complete || sp > 65527 {
		return false, errors.New("Go casualty helper phase/stack")
	}
	ret := m.Read16(0x1e880 + sp)
	if m.Read16(0x1e880+sp+2) != 0xf67 || m.Read16(0x1e880+sp+4) != t.SourceRaw || m.Read16(0x1e880+sp+6) != t.TargetRaw || (ret == 0x48b2 && (x.Impact || len(x.Record.Calls) != 0)) || (ret == 0x4658 && (!x.Impact || len(x.Record.Calls) != 1)) || (ret != 0x48b2 && ret != 0x4658) {
		return false, errors.New("Go casualty helper caller/identity")
	}
	catalog := x.Actions.Setup.Catalog
	source, target := catalog.Profiles[t.Source.Unit], catalog.Profiles[t.Target.Unit]
	divisor := uint32(m.Read16(0x1e880+0x26ac)) + 5
	if divisor > 65535 || uint64(m.Read16(0x1e880+0x70ce+uint32(source.NativeKind)*4)) != source.Attack || (target.NativeKind != 0 && uint64(m.Read16(0x1e880+0x70d0+uint32(target.NativeKind)*4)) != target.HP) {
		return false, errors.New("Go casualty profile/divisor binding")
	}
	damage, encoded, err := originalBattleAmountFor(source.Attack, uint16(t.Source.Count), target.HP, uint16(divisor), 1)
	if err != nil {
		return false, err
	}
	if len(x.Record.Calls) == 1 && (x.Record.Calls[0].Damage != damage || x.Record.Calls[0].Encoded != encoded) {
		return false, errors.New("Go casualty inner amount changed")
	}
	before := x.HP[0][t.TargetRaw]
	after := uint64(0)
	if before > damage {
		after = before - damage
	}
	at := int(t.TargetRaw) * 2
	word := binary.LittleEndian.Uint16(x.HPWords[at : at+2])
	wordAfter := word
	if target.NativeKind != 0 {
		wordAfter -= uint16(damage)
		m.Write16(0x1e880+0x8ca4+uint32(at), wordAfter)
		binary.LittleEndian.PutUint16(x.HPWords[at:at+2], wordAfter)
	}
	x.HP[0][t.TargetRaw] = after
	x.Record.Calls = append(x.Record.Calls, originalCasualtyAmount{ret, damage, encoded, before, after, word, wordAfter})
	if ret == 0x4658 {
		x.Record.After, x.Record.PlannedDisplay = originalCasualtyDisplay(x.Record.Before, encoded)
		x.Record.Loss = x.Record.Before - x.Record.After
	}
	c.R[dg.AX] = encoded
	c.R[dg.SP] += 4
	c.IP = ret
	c.Cycles++
	return true, nil
}

func (x *originalBattleCasualties) kind(m *dg.Machine, ida int) (bool, error) {
	ip := uint16(ida - 0x1e570)
	if err := x.Actions.check(m, ip, 0x22dbc, 0x23a42); err != nil {
		return false, err
	}
	c := m.CPU
	raw := c.R[dg.BX] / 4
	if !x.Started || x.Complete || c.R[dg.BX]%4 != 0 || raw >= 6 {
		return false, errors.New("Go casualty kind raw/phase")
	}
	s := x.Rows[0][raw]
	value := m.Read16(0x1e880 + 0x56e8 + uint32(raw)*4)
	if s.Unit != "" && x.Actions.Setup.Catalog.Profiles[s.Unit].NativeKind == 0 {
		value = 0
		if s.Count > 0 {
			value = 1
		}
	}
	c.Flags = originalCountZeroFlags(c.Flags, value)
	c.IP += 5
	c.Cycles++
	return true, nil
}

func (x *originalBattleCasualties) impactSite(m *dg.Machine, ip uint16) error {
	if err := x.Actions.check(m, ip, 0x22b96, 0x22dbc); err != nil {
		return err
	}
	c := m.CPU
	bp := uint32(c.R[dg.BP])
	if !x.Impact || x.Complete || len(x.Record.Calls) != 2 || bp != uint32(x.ImpactSP)-2 || bp < 16 || m.Read16(0x1e880+bp) != x.ImpactBP || m.Read16(0x1e880+bp+2) != x.ImpactReturn || m.Read16(0x1e880+bp+4) != 0xf67 {
		return errors.New("Go casualty impact frame/phase")
	}
	return nil
}

func (x *originalBattleCasualties) readCount(m *dg.Machine, ip uint16) (bool, error) {
	if err := x.impactSite(m, ip); err != nil {
		return false, err
	}
	c := m.CPU
	if x.Committed || c.R[dg.BX] != x.Record.Target.TargetRaw*4 {
		return false, errors.New("Go casualty count read identity")
	}
	c.R[dg.SI] = uint16(x.Record.Before)
	c.IP += 4
	c.Cycles++
	return true, nil
}

func (x *originalBattleCasualties) writeCount(m *dg.Machine, ip uint16) (bool, error) {
	if err := x.impactSite(m, ip); err != nil {
		return false, err
	}
	c := m.CPU
	t := x.Record.Target
	offset := int(t.TargetRaw) * 4
	if x.Committed {
		return false, errors.New("Go casualty count write after commit")
	}
	native := x.Actions.Setup.Catalog.Profiles[t.Target.Unit].NativeKind != 0
	switch ip {
	case 0x4730, 0x47d0: // IDA22CA0 / 22D40, animation counter only.
		index := len(x.Record.Display)
		if c.R[dg.BX] != t.TargetRaw*4 || index >= len(x.Record.PlannedDisplay) || c.R[dg.AX] != x.Record.PlannedDisplay[index] || x.ClearStage != 0 {
			return false, errors.New("Go casualty display sequence")
		}
		if native {
			m.Write16(0x1e880+0x56ea+uint32(offset), c.R[dg.AX])
			binary.LittleEndian.PutUint16(x.Projected[offset+2:offset+4], c.R[dg.AX])
		}
		x.DisplayValue = uint32(c.R[dg.AX])
		x.Record.Display = append(x.Record.Display, c.R[dg.AX])
	case 0x4825, 0x4829: // IDA22D95 / 22D99, death clears compatibility row.
		stage := uint16(0)
		if ip == 0x4829 {
			stage = 1
			offset += 2
		}
		if c.R[dg.SI] != t.TargetRaw*4 || c.R[dg.AX] != 0 || x.Record.After != 0 || x.ClearStage != stage || len(x.Record.Display) != len(x.Record.PlannedDisplay) {
			return false, errors.New("Go casualty death clear sequence")
		}
		if native {
			m.Write16(0x1e880+0x56e8+uint32(offset), 0)
			binary.LittleEndian.PutUint16(x.Projected[offset:offset+2], 0)
		}
		x.ClearStage++
	default:
		return false, errors.New("Go casualty unsupported write")
	}
	c.IP += 4
	c.Cycles++
	return true, nil
}

func (x *originalBattleCasualties) commit(m *dg.Machine) (bool, error) {
	if err := x.impactSite(m, 0x4847); err != nil {
		return false, err
	}
	if x.Committed {
		return false, nil
	}
	if len(x.Record.Display) != len(x.Record.PlannedDisplay) || (x.Record.After == 0 && x.ClearStage != 2) || (x.Record.After > 0 && x.ClearStage != 0) || m.CPU.R[dg.SP] != x.ImpactSP-12 {
		return false, errors.New("Go casualty incomplete display/death")
	}
	x.Rows[0][x.Record.Target.TargetRaw].Count = x.Record.After
	x.DisplayValue = x.Record.After
	x.Committed = true
	x.Record.Updates++
	return false, nil // Original epilogue and outer movement restore continue.
}

func (x *originalBattleCasualties) finish(m *dg.Machine, ip uint16) (bool, error) {
	if !x.Started {
		return false, nil
	}
	if err := x.Actions.check(m, ip, 0x1fb6c, 0x1ff1b); err != nil {
		return false, err
	}
	if ip != x.Record.Target.Caller || m.CPU.R[dg.SP] != x.EntrySP+4 || m.CPU.R[dg.BP] != x.EntryBP {
		return false, errors.New("Go casualty outer return frame")
	}
	if !x.Committed {
		if x.Impact || len(x.Record.Calls) != 1 || x.Record.Calls[0].Encoded != 1 {
			return false, errors.New("Go casualty missing commit")
		}
		x.Committed = true
		x.Record.Updates++
	}
	x.Complete = true
	return false, errOriginalBattleCasualtiesHeld
}

func installOriginalBattleCasualties(e *game.Engine, a *originalBattleActions) (*originalBattleCasualties, error) {
	if a == nil || a.Casualties != nil || a.Active || a.Setup.Phase != "" || e.BattleRulesMode() != "native" {
		return nil, errors.New("Go casualty install lifecycle")
	}
	x := &originalBattleCasualties{Actions: a}
	a.Casualties = x
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x1532), x.helper)
	for _, ida := range []int{0x22df0, 0x23004, 0x2309a, 0x231f0, 0x23380, 0x23456, 0x234f4, 0x2376a, 0x238ac, 0x2397c} {
		ida := ida
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, uint16(ida-0x1e570)), func(m *dg.Machine) (bool, error) { return x.kind(m, ida) })
	}
	for _, ip := range []uint16{0x46da, 0x478f} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.readCount(m, ip) })
	}
	for _, ip := range []uint16{0x4730, 0x47d0, 0x4825, 0x4829} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.writeCount(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x4847), x.commit)
	for _, ip := range []uint16{0x1718, 0x1818, 0x19a5} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.finish(m, ip) })
	}
	return x, nil
}

func (x *originalBattleCasualties) text(e *game.Engine, out *image.RGBA, raw uint16, area image.Rectangle) error {
	count := x.Rows[0][raw].Count
	if x.Started && !x.Committed && raw == x.Record.Target.TargetRaw {
		count = x.DisplayValue
	}
	if count == 0 {
		return nil
	}
	s := strconv.FormatUint(uint64(count), 10)
	if e.Assets == nil || len(s) > 5 {
		return errors.New("Go casualty number assets/bounds")
	}
	for i, ch := range s {
		if _, ok := e.Assets.Glyphs[ch]; !ok {
			return fmt.Errorf("Go casualty missing number %U", ch)
		}
		cell := image.Rect(area.Min.X+96+i*24, area.Min.Y+210, area.Min.X+120+i*24, area.Min.Y+300)
		if !cell.In(area) {
			return errors.New("Go casualty number overflow")
		}
		e.Assets.DrawRune(out, ch, cell, [3]uint8{255, 241, 181})
	}
	return nil
}
