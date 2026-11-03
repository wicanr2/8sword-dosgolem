package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"math/bits"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalBattleRoundsHeld = errors.New("ordinary battle returned; held before world cleanup")

type originalRoundSite struct {
	IP             uint16
	Start, End     int
	Side, Register int
	Kind, Reverse  bool
	Immediate      uint16
	Length         uint16
}
type originalRoundSwap struct {
	Side, A, B       int
	BeforeA, BeforeB uint16
}
type originalBattleRounds struct {
	AllowWorld, Released bool
	Actions              *originalBattleActions
	Rows                 [2][6]ArmyStack
	Slots                [2][6]uint16
	HP                   [2][6]uint64
	Projected            [48]byte
	HPWords              [24]byte
	Active, Done         bool
	Result               string
	RawResult            uint16
	History              []originalCasualtyRecord
	Swaps                []originalRoundSwap
	SwapWrites           int
	Sorting              int
	SortSP, SortBP       uint16
	SortCalls            [2]uint64
	HalfTurns            [2]uint64
	MotionAfter          [2][6]uint16
}

func (r *originalBattleRounds) begin(m *dg.Machine) (bool, error) {
	if r.Active {
		return false, errors.New("round lifecycle repeated start")
	}
	r.Rows, r.Slots, r.HP = r.Actions.Setup.Plan.Rows, r.Actions.Setup.Plan.Slots, r.Actions.Setup.Plan.HP
	copy(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718])
	copy(r.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0])
	copy(r.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c])
	r.Active = true
	r.Sorting = -1
	return false, nil
}

func (r *originalBattleRounds) checkProjection(m *dg.Machine) error {
	c := r.Actions.Casualties
	if c != nil && c.Started {
		return c.checkProjection(m)
	}
	if !bytes.Equal(r.Projected[:], m.Mem[0x1e880+0x56e8:0x1e880+0x5718]) || !bytes.Equal(r.HPWords[:12], m.Mem[0x1e880+0x8ca4:0x1e880+0x8cb0]) || !bytes.Equal(r.HPWords[12:], m.Mem[0x1e880+0x8e60:0x1e880+0x8e6c]) {
		return errors.New("round data projection changed")
	}
	return nil
}

func roundSubFlags(flags, a, b uint16) uint16 {
	f := flags &^ 0x8d5
	v := a - b
	if a < b {
		f |= 1
	}
	if v == 0 {
		f |= 0x40
	}
	if v&0x8000 != 0 {
		f |= 0x80
	}
	if (a^b^v)&0x10 != 0 {
		f |= 0x10
	}
	if (a^b)&(a^v)&0x8000 != 0 {
		f |= 0x800
	}
	if bits.OnesCount8(byte(v))%2 == 0 {
		f |= 4
	}
	return f
}

func (r *originalBattleRounds) compare(m *dg.Machine, s originalRoundSite) (bool, error) {
	if err := r.Actions.check(m, s.IP, s.Start, s.End); err != nil {
		return false, err
	}
	c := m.CPU
	index := c.R[s.Register] / 4
	if !r.Active || r.Done || c.R[s.Register]%4 != 0 || index >= 6 {
		return false, fmt.Errorf("round comparison raw at %04X index=%04X", s.IP, c.R[s.Register])
	}
	row := r.currentRows()[s.Side][index]
	profile := r.Actions.Setup.Catalog.Profiles[row.Unit]
	value := uint16(row.Count)
	rhs := s.Immediate
	if s.Reverse {
		rhs = c.R[dg.AX]
	}
	if s.Kind {
		value = profile.NativeKind
		if row.Count == 0 {
			value = 0
		}
		if row.Count > 0 && profile.NativeKind == 0 {
			// Category equality only. No surrogate ID reaches a register/table.
			eq := rhs != 0 && profile.Ranged && (rhs == 3 || rhs == 24)
			c.Flags = roundSubFlags(c.Flags, 0, rhs)
			if eq {
				c.Flags |= 0x40
			} else {
				c.Flags &^= 0x40
			}
			c.IP += s.Length
			c.Cycles++
			return true, nil
		}
	}
	if s.Reverse {
		c.Flags = roundSubFlags(c.Flags, rhs, value)
	} else {
		c.Flags = roundSubFlags(c.Flags, value, rhs)
	}
	c.IP += s.Length
	c.Cycles++
	return true, nil
}

func (r *originalBattleRounds) currentRows() [2][6]ArmyStack {
	if c := r.Actions.Casualties; c != nil && c.Started {
		return c.Rows
	}
	return r.Rows
}

func roundSortPlan(c game.OwnedCombatCatalog, rows [6]ArmyStack, slots [6]uint16, orders [4][3]byte, casterFront bool) ([6]uint16, []originalRoundSwap, error) {
	out := slots
	swaps := []originalRoundSwap{}
	for _, raw := range slots {
		if raw >= 6 {
			return out, nil, errors.New("round sort map bound")
		}
	}
	for _, order := range orders {
		for _, slot := range order {
			if slot >= 6 {
				return out, nil, errors.New("round sort order bound")
			}
		}
		for a := 0; a < 3; a++ {
			if rows[out[order[a]]].Count > 0 {
				continue
			}
			for b := a + 1; b < 3; b++ {
				s := rows[out[order[b]]]
				p := c.Profiles[s.Unit]
				if s.Count == 0 || p.Ranged || (!casterFront && (p.NativeKind == 10 || p.NativeKind == 12)) {
					continue
				}
				x, y := int(order[a]), int(order[b])
				swaps = append(swaps, originalRoundSwap{A: x, B: y, BeforeA: out[x], BeforeB: out[y]})
				out[x], out[y] = out[y], out[x]
				break
			}
		}
	}
	return out, swaps, nil
}

func (r *originalBattleRounds) sortBegin(m *dg.Machine, side int) (bool, error) {
	start, end, ip := 0x20724, 0x20ab4, uint16(0x21b4)
	if side == 1 {
		start, end, ip = 0x20ab4, 0x20dae, 0x2544
	}
	if err := r.Actions.check(m, ip, start, end); err != nil {
		return false, err
	}
	if !r.Active || r.Done || r.Sorting != -1 || r.Actions.Casualties.Started {
		return false, errors.New("round sort phase")
	}
	orders := [4][3]byte{}
	for i, base := range []uint32{0x708a, 0x708e, 0x7092, 0x7096} {
		copy(orders[i][:], m.Mem[0x1e880+base:0x1e880+base+3])
	}
	casterFront := false
	if side == 0 {
		normal, spells := false, false
		for _, s := range r.Rows[0] {
			p := r.Actions.Setup.Catalog.Profiles[s.Unit]
			normal = normal || (s.Count > 0 && p.NativeKind != 10 && p.NativeKind != 12)
		}
		for i := 0; i < 8; i++ {
			spells = spells || m.Read16(0x1e880+0x2aa8+uint32(i*2)) != 0
		}
		casterFront = !normal && !spells
	}
	_, swaps, err := roundSortPlan(r.Actions.Setup.Catalog, r.Rows[side], r.Slots[side], orders, casterFront)
	if err != nil {
		return false, err
	}
	for i := range swaps {
		swaps[i].Side = side
	}
	r.Swaps = swaps
	r.SwapWrites = 0
	r.Sorting = side
	r.SortSP = m.CPU.R[dg.SP]
	r.SortBP = m.CPU.R[dg.BP]
	r.SortCalls[side]++
	return false, nil
}

func (r *originalBattleRounds) sortWrite(m *dg.Machine, ip uint16, side, reg int) (bool, error) {
	start, end := 0x20724, 0x20ab4
	if side == 1 {
		start, end = 0x20ab4, 0x20dae
	}
	if err := r.Actions.check(m, ip, start, end); err != nil {
		return false, err
	}
	if r.Sorting != side || r.SwapWrites >= 2*len(r.Swaps) {
		return false, errors.New("round unexpected map write")
	}
	s := r.Swaps[r.SwapWrites/2]
	slot, value := s.A, s.BeforeB
	if r.SwapWrites%2 == 1 {
		slot, value = s.B, s.BeforeA
	}
	base := uint16(0x6fb6 + side*12)
	if m.CPU.R[reg] != base+uint16(slot*2) || m.CPU.R[dg.AX] != value {
		return false, errors.New("round map write disagrees with Go sort")
	}
	m.Write16(0x1e880+uint32(base)+uint32(slot*2), value)
	r.Slots[side][slot] = value
	r.SwapWrites++
	m.CPU.IP += 2
	m.CPU.Cycles++
	return true, nil
}

func (r *originalBattleRounds) sortEnd(m *dg.Machine, side int) (bool, error) {
	ip, start, end := uint16(0x2543), 0x20724, 0x20ab4
	if side == 1 {
		ip, start, end = 0x283d, 0x20ab4, 0x20dae
	}
	if err := r.Actions.check(m, ip, start, end); err != nil {
		return false, err
	}
	if r.Sorting != side || r.SwapWrites != 2*len(r.Swaps) || m.CPU.R[dg.SP] != r.SortSP || m.CPU.R[dg.BP] != r.SortBP {
		return false, errors.New("round sort incomplete return")
	}
	r.Sorting = -1
	return false, nil
}

func (r *originalBattleRounds) enter(m *dg.Machine, side int, ip uint16) (bool, error) {
	a := r.Actions
	c := a.Casualties
	cpu := m.CPU
	sp := uint32(cpu.R[dg.SP])
	start, end := 0x22dbc, 0x23a42
	if side == 0 {
		start, end = 0x21ea0, 0x22af5
		if ip == 0x3240 {
			start, end = 0x217b0, 0x219cc
		}
	} else if ip == 0x4626 {
		start, end = 0x22b96, 0x22dbc
	}
	if err := a.check(m, ip, start, end); err != nil {
		return false, err
	}
	if !r.Active || r.Done || r.Sorting != -1 || sp > 65511 || m.Read16(0x1e880+sp+2) != 0xf67 {
		return false, errors.New("round action context")
	}
	if c.Started {
		return false, errors.New("round overlapping action")
	}
	ss, ts, ret := m.Read16(0x1e880+sp+4), m.Read16(0x1e880+sp+6), m.Read16(0x1e880+sp)
	direct := ip == 0x4626 || ip == 0x3240
	if (side == 1 && !direct && ret != 0x1818) || (side == 1 && direct && ret != 0x1718 && ret != 0x19a5) || (side == 0 && !direct && ret != 0x1bec) || (side == 0 && direct && ret != 0x1aec && ret != 0x1da4) || ss >= 6 || ts >= 6 {
		return false, errors.New("round action caller/slots")
	}
	sr, tr := r.Slots[side][ss], r.Slots[1-side][ts]
	source, target := r.Rows[side][sr], r.Rows[1-side][tr]
	if source.Count == 0 || target.Count == 0 || source.Count > 65535 || target.Count > 32767 {
		return false, errors.New("round action alive/word bounds")
	}
	p := a.Setup.Catalog.Profiles[source.Unit]
	if p.NativeKind == 10 || p.NativeKind == 12 || p.Ranged != direct {
		return false, errors.New("round unsupported source class")
	}
	t := originalEnemyTarget{ip, ret, ss, ts, sr, tr, source, target}
	*c = originalBattleCasualties{Actions: a, Player: side == 0, Direct: direct, Rows: r.Rows, HP: r.HP, Projected: r.Projected, HPWords: r.HPWords, Started: true, EntrySP: cpu.R[dg.SP], EntryBP: cpu.R[dg.BP], DisplayValue: target.Count, Record: originalCasualtyRecord{Player: side == 0, Target: t, Before: target.Count, After: target.Count}}
	r.MotionAfter = r.Slots
	if !direct {
		from, to := int(ss), int(ts%3)
		v := r.MotionAfter[side][from]
		if from < to {
			for k := from; k < to; k++ {
				r.MotionAfter[side][k] = r.MotionAfter[side][k+1]
			}
		} else {
			for k := from; k > to; k-- {
				r.MotionAfter[side][k] = r.MotionAfter[side][k-1]
			}
		}
		r.MotionAfter[side][to] = v
	}

	if direct {
		c.Impact = true
		c.ImpactSP, c.ImpactBP, c.ImpactReturn = cpu.R[dg.SP], cpu.R[dg.BP], ret
	}
	a.Target = &c.Record.Target
	return false, nil
}

func (r *originalBattleRounds) playerGate(m *dg.Machine, ip uint16) (bool, error) {
	if ip == 0x334 {
		return false, errors.New("round special/spell not yet admitted")
	}
	if ip == 0x211a {
		if !r.Active || r.Done {
			return false, errors.New("round player half lifecycle")
		}
		r.HalfTurns[0]++
		return false, nil
	}
	if ip == 0x3240 && r.Actions.Casualties.Started {
		return r.playerImpact(m)
	}
	return r.enter(m, 0, ip)
}

func (r *originalBattleRounds) classify(m *dg.Machine, ip uint16) (bool, error) {
	if err := r.Actions.check(m, ip, 0x1ff1c, 0x20319); err != nil {
		return false, err
	}
	bp := uint32(m.CPU.R[dg.BP])
	if bp < 16 || bp > 65520 {
		return false, errors.New("round source classification frame")
	}
	slot := m.Read16(0x1e880 + bp - 0xa)
	if slot >= 6 {
		return false, errors.New("round source classification slot")
	}
	s := r.Rows[0][r.Slots[0][slot]]
	p := r.Actions.Setup.Catalog.Profiles[s.Unit]
	if p.NativeKind != 0 {
		return false, nil
	}
	if s.Count == 0 {
		return false, errors.New("round classification dead source")
	}
	if !p.Ranged {
		return false, nil
	}
	if ip == 0x1a3f {
		m.CPU.IP = 0x1a49
	} else if ip == 0x1c42 {
		m.CPU.IP = 0x1c53
	} else {
		return false, errors.New("round unknown classification branch")
	}
	m.CPU.Cycles++
	return true, nil
}

func (r *originalBattleRounds) playerImpact(m *dg.Machine) (bool, error) {
	c := r.Actions.Casualties
	if err := r.Actions.check(m, 0x3240, 0x217b0, 0x219cc); err != nil {
		return false, err
	}
	cpu := m.CPU
	sp := uint32(cpu.R[dg.SP])
	ret := m.Read16(0x1e880 + sp)
	if !c.Started || !c.Player || c.Committed || len(c.Record.Calls) != 0 || sp > 65511 || m.Read16(0x1e880+sp+2) != 0xf67 || m.Read16(0x1e880+sp+4) != c.Record.Target.SourceSlot || m.Read16(0x1e880+sp+6) != c.Record.Target.TargetSlot {
		return false, errors.New("round player impact context")
	}
	if c.Direct {
		if cpu.R[dg.SP] != c.EntrySP || cpu.R[dg.BP] != c.EntryBP {
			return false, errors.New("round direct player frame")
		}
		return false, nil
	}
	code := r.Actions.Setup.Code
	at := 0xe570 + int(ret) - 4
	if ret != 0x3237 && (ret < 0x3934 || ret >= 0x4585) {
		return false, errors.New("round player impact caller range")
	}
	if code[at] != 0x0e || code[at+1] != 0xe8 || uint16(int(ret)+int(int16(binary.LittleEndian.Uint16(code[at+2:at+4])))) != 0x3240 {
		return false, errors.New("round player impact call bytes")
	}
	if ret == 0x3237 {
		if err := r.Actions.check(m, 0x3240, 0x21712, 0x217af); err != nil {
			return false, err
		}
		bp := uint32(cpu.R[dg.BP])
		if bp < 16 || bp > 65525 || m.Read16(0x1e880+bp) != c.EntrySP-2 {
			return false, errors.New("round player step parent")
		}
	}
	if c.Impact {
		if c.ImpactSP != cpu.R[dg.SP] || c.ImpactBP != cpu.R[dg.BP] {
			return false, errors.New("round repeated player impact")
		}
		return false, nil
	}
	c.Impact = true
	c.ImpactSP, c.ImpactBP, c.ImpactReturn = cpu.R[dg.SP], cpu.R[dg.BP], ret
	return false, nil
}

func (r *originalBattleRounds) playerImpactSite(m *dg.Machine, ip uint16) error {
	if err := r.Actions.check(m, ip, 0x217b0, 0x219cc); err != nil {
		return err
	}
	c := r.Actions.Casualties
	bp := uint32(m.CPU.R[dg.BP])
	if !c.Started || !c.Impact || c.Complete || len(c.Record.Calls) != 1 || bp != uint32(c.ImpactSP)-2 || bp < 16 || m.Read16(0x1e880+bp) != c.ImpactBP || m.Read16(0x1e880+bp+2) != c.ImpactReturn || m.Read16(0x1e880+bp+4) != 0xf67 {
		return errors.New("round player impact frame")
	}
	return nil
}

func (r *originalBattleRounds) playerHelper(m *dg.Machine) (bool, error) {
	if err := r.Actions.check(m, 0x1592, 0x1fb02, 0x1fb6c); err != nil {
		return false, err
	}
	c := r.Actions.Casualties
	cpu := m.CPU
	sp := uint32(cpu.R[dg.SP])
	t := c.Record.Target
	if !c.Started || !c.Player || !c.Impact || c.Committed || sp > 65527 || len(c.Record.Calls) != 0 || m.Read16(0x1e880+sp) != 0x32d9 || m.Read16(0x1e880+sp+2) != 0xf67 || m.Read16(0x1e880+sp+4) != t.SourceRaw || m.Read16(0x1e880+sp+6) != t.TargetRaw {
		return false, errors.New("round player helper caller")
	}
	modifier, boost := m.Read16(0x1e880+0x26b2), m.Read16(0x1e880+0x26b8)
	s, p := r.Actions.Setup.Catalog.Profiles[t.Source.Unit], r.Actions.Setup.Catalog.Profiles[t.Target.Unit]
	if modifier >= 5 || boost == 65535 || (s.NativeKind != 0 && uint64(m.Read16(0x1e880+0x70ce+uint32(s.NativeKind)*4)) != s.Attack) || (p.NativeKind != 0 && uint64(m.Read16(0x1e880+0x70d0+uint32(p.NativeKind)*4)) != p.HP) {
		return false, errors.New("round player factor binding")
	}
	damage, encoded, err := originalBattleAmountFor(s.Attack, uint16(t.Source.Count), p.HP, 5-modifier, boost+1)
	if err != nil {
		return false, err
	}
	before := c.HP[1][t.TargetRaw]
	after := uint64(0)
	if before > damage {
		after = before - damage
	}
	at := 12 + int(t.TargetRaw)*2
	word := binary.LittleEndian.Uint16(c.HPWords[at : at+2])
	next := word
	if p.NativeKind != 0 {
		next -= uint16(damage)
		m.Write16(0x1e880+0x8e60+uint32(t.TargetRaw)*2, next)
		binary.LittleEndian.PutUint16(c.HPWords[at:at+2], next)
	}
	c.HP[1][t.TargetRaw] = after
	c.Record.Calls = append(c.Record.Calls, originalCasualtyAmount{0x32d9, damage, encoded, before, after, word, next})
	c.Record.After = c.Record.Before - min(c.Record.Before, uint32(encoded))
	c.Record.Loss = c.Record.Before - c.Record.After
	if c.Record.After == 0 {
		for n := int(min(c.Record.Before, 5)); n >= 0; n-- {
			c.Record.PlannedDisplay = append(c.Record.PlannedDisplay, uint16(n))
		}
	} else {
		start := c.Record.Before
		if encoded >= 5 {
			start = c.Record.Before - uint32(encoded) + 5
		}
		for n := int(start); n >= int(c.Record.After); n-- {
			c.Record.PlannedDisplay = append(c.Record.PlannedDisplay, uint16(n))
		}
	}
	cpu.R[dg.AX] = encoded
	cpu.R[dg.SP] += 4
	cpu.IP = 0x32d9
	cpu.Cycles++
	return true, nil
}

func (r *originalBattleRounds) finishAction(m *dg.Machine) (bool, error) {
	c := r.Actions.Casualties
	if c.Record.Updates != 1 || !c.Committed {
		return false, errors.New("round action incomplete")
	}
	if r.Slots != r.MotionAfter {
		return false, errors.New("round motion maps incomplete")
	}
	r.Rows, r.HP, r.Projected, r.HPWords = c.Rows, c.HP, c.Projected, c.HPWords
	r.History = append(r.History, c.Record)
	*c = originalBattleCasualties{Actions: r.Actions}
	r.Actions.Target = nil
	return false, nil
}

func (r *originalBattleRounds) motionWrite(m *dg.Machine, s originalRoundMotion) (bool, error) {
	start, end := 0x21ea0, 0x22af5
	if s.Side == 1 {
		start, end = 0x22dbc, 0x23a42
	}
	if err := r.Actions.check(m, s.IP, start, end); err != nil {
		return false, err
	}
	c := r.Actions.Casualties
	side := 1
	if c.Player {
		side = 0
	}
	if !c.Started || c.Direct || !c.Committed || side != s.Side || s.Slot >= 3 || m.CPU.R[dg.AX] != r.MotionAfter[side][s.Slot] {
		return false, errors.New("round motion disagrees with Go map")
	}
	base := uint32(0x6fb6 + side*12 + s.Slot*2)
	m.Write16(0x1e880+base, m.CPU.R[dg.AX])
	r.Slots[side][s.Slot] = m.CPU.R[dg.AX]
	m.CPU.IP += 3
	m.CPU.Cycles++
	return true, nil
}

func (r *originalBattleRounds) returned(m *dg.Machine) (bool, error) {
	if r.Released {
		return false, nil
	}
	if err := r.Actions.check(m, 0x3c, 0x1e578, 0x1e5b1); err != nil {
		return false, err
	}
	if !r.Active || r.Actions.Casualties.Started || r.Sorting != -1 {
		return false, errors.New("round return incomplete")
	}
	alive := [2]bool{}
	for side := range r.Rows {
		for _, s := range r.Rows[side] {
			alive[side] = alive[side] || s.Count > 0
		}
	}
	result := "retreat"
	if !alive[1] {
		result = "win"
	} else if !alive[0] {
		result = "loss"
	}
	if (result == "win" && m.CPU.R[dg.AX] != 0) || (result == "loss" && m.CPU.R[dg.AX] != 1) {
		return false, errors.New("round native/Go result disagrees")
	}
	r.Result, r.RawResult, r.Done = result, m.CPU.R[dg.AX], true
	if r.AllowWorld {
		r.Released = true
		r.Active = false
		r.Actions.Active = false
		return false, nil
	}
	return false, errOriginalBattleRoundsHeld
}

func installOriginalBattleRounds(e *game.Engine, a *originalBattleActions) (*originalBattleRounds, error) {
	if a == nil || a.Rounds != nil || a.Active || a.Setup.Phase != "" {
		return nil, errors.New("round install lifecycle")
	}
	if _, err := installOriginalBattleCasualties(e, a); err != nil {
		return nil, err
	}
	r := &originalBattleRounds{Actions: a, Sorting: -1}
	a.Rounds = r
	for _, s := range originalRoundSites {
		s := s
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, s.IP), func(m *dg.Machine) (bool, error) { return r.compare(m, s) })
	}
	for side, ip := range []uint16{0x21b4, 0x2544} {
		side, ip := side, ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return r.sortBegin(m, side) })
	}
	for _, s := range originalRoundWrites {
		s := s
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, s.IP), func(m *dg.Machine) (bool, error) { return r.sortWrite(m, s.IP, s.Side, s.Register) })
	}
	for side, ip := range []uint16{0x2543, 0x283d} {
		side, ip := side, ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return r.sortEnd(m, side) })
	}
	for _, s := range originalRoundMotions {
		s := s
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, s.IP), func(m *dg.Machine) (bool, error) { return r.motionWrite(m, s) })
	}

	c := a.Casualties
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x1592), r.playerHelper)
	for _, ip := range []uint16{0x32ec, 0x339f} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return c.readCount(m, ip) })
	}
	for _, ip := range []uint16{0x3340, 0x33e0, 0x3435, 0x3439} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return c.writeCount(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x3457), c.commit)
	for _, ip := range []uint16{0x1bec, 0x1aec, 0x1da4} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return c.finish(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x3c), r.returned)
	for _, ip := range []uint16{0x1a3f, 0x1c42} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return r.classify(m, ip) })
	}
	return r, nil
}
