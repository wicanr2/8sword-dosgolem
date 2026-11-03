package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"math/bits"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalBattleTargetHeld = errors.New("original enemy target held before attack and casualties")

type originalBattlePresenceSite struct {
	IDA, Start, End int
	Side            int
}

// Original IDA MZ linear addresses. Runtime CS0F67 IP = IDA - 0x1e570.
var originalBattlePresenceSites = []originalBattlePresenceSite{
	{0x2057a, 0x2055e, 0x205a2, 1}, {0x205be, 0x205a2, 0x205e6, 0},
	{0x1fb97, 0x1fb6c, 0x1ff1b, 1}, {0x1fc50, 0x1fb6c, 0x1ff1b, 0},
	{0x1fc96, 0x1fb6c, 0x1ff1b, 0}, {0x1fca5, 0x1fb6c, 0x1ff1b, 0},
	{0x1fcb4, 0x1fb6c, 0x1ff1b, 0}, {0x1fce3, 0x1fb6c, 0x1ff1b, 0},
	{0x1fd17, 0x1fb6c, 0x1ff1b, 0}, {0x1fd44, 0x1fb6c, 0x1ff1b, 0},
	{0x1fd58, 0x1fb6c, 0x1ff1b, 0}, {0x1fd9b, 0x1fb6c, 0x1ff1b, 1},
	{0x1feca, 0x1fb6c, 0x1ff1b, 0},
}

type originalEnemyTarget struct {
	IP, Caller, SourceSlot, TargetSlot, SourceRaw, TargetRaw uint16
	Source, Target                                           ArmyStack
}

type originalBattleActions struct {
	Setup         *originalBattleSetup
	Active        bool
	Comparisons   uint64
	ExtendedReads uint64
	AliasReads    []originalBattleAlias
	Sites         map[uint16]uint64
	Target        *originalEnemyTarget
	Casualties    *originalBattleCasualties
	Rounds        *originalBattleRounds
}

type originalBattleAlias struct{ BX, Slot, MapWord, Offset, Value uint16 }

func (x *originalBattleActions) check(m *dg.Machine, ip uint16, start, end int) error {
	c := m.CPU
	if c.IP != ip || c.Seg[dg.CS] != 0xf67 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == ^uint64(0) || x.Setup == nil || x.Setup.Phase != "ready" || end > len(x.Setup.Code)+0x10000 || start < 0x1e570 {
		return errors.New("battle presence site/segments/phase/source bounds")
	}
	if !bytes.Equal(x.Setup.Code[start-0x10000:end-0x10000], m.Mem[start-0x10000+0x1100:end-0x10000+0x1100]) {
		return errors.New("battle presence source bytes")
	}
	if x.Rounds != nil && x.Rounds.Active {
		if err := x.Rounds.checkProjection(m); err != nil {
			return err
		}
	} else if x.Casualties != nil && x.Casualties.Started {
		if err := x.Casualties.checkProjection(m); err != nil {
			return err
		}
	} else {
		rows, err := x.Setup.rows(m)
		if err != nil || rows != x.Setup.Plan.Rows {
			return errors.New("battle presence typed/native projection changed")
		}
	}
	for side, base := range []uint32{0x6fb6, 0x6fc2} {
		for i, raw := range x.slots()[side] {
			if m.Read16(0x1e880+base+uint32(i*2)) != raw {
				return fmt.Errorf("battle presence slot map changed side=%d slot=%d expected=%04X actual=%04X", side, i, raw, m.Read16(0x1e880+base+uint32(i*2)))
			}
		}
	}
	return nil
}

func (x *originalBattleActions) begin(m *dg.Machine) (bool, error) {
	if err := x.check(m, 0x35, 0x1e5a5, 0x1e5a8); err != nil {
		return false, err
	}
	x.Active = true
	if x.Rounds != nil {
		return x.Rounds.begin(m)
	}
	return false, nil // Original round and RNG continue; no projected fake count.
}

func originalCountZeroFlags(prior, value uint16) uint16 {
	f := prior &^ 0x8d5
	if value == 0 {
		f |= 0x40
	}
	if value&0x8000 != 0 {
		f |= 0x80
	}
	if bits.OnesCount8(uint8(value))%2 == 0 {
		f |= 4
	}
	return f
}

func (x *originalBattleActions) presence(m *dg.Machine, site originalBattlePresenceSite) (bool, error) {
	ip := uint16(site.IDA - 0x1e570)
	if err := x.check(m, ip, site.Start, site.End); err != nil {
		return false, err
	}
	c := m.CPU
	if !x.Active || x.Target != nil {
		return false, errors.New("battle presence phase")
	}
	var alias *originalBattleAlias
	if ip == 0x17d4 {
		bp := uint32(c.R[dg.BP])
		if bp < 16 || bp > 65520 {
			return false, errors.New("battle presence frame")
		}
		selected, source := m.Read16(0x1e880+bp-4), m.Read16(0x1e880+bp-6)
		if selected < 3 {
			if source != selected {
				return false, errors.New("battle transient target provenance")
			}
			raw := x.slots()[0][source]
			sr := x.slots()[1][source]
			word := m.Read16(0x1e880 + 0x6fa8 + uint32(source*2))
			if raw >= 6 || sr >= 6 || x.rows()[0][raw].Count == 0 || x.rows()[1][sr].Count == 0 || c.R[dg.BX] != word*4 {
				return false, errors.New("battle transient target origin/alive/BX")
			}
			offset := c.R[dg.BX] + 0x56ea
			alias = &originalBattleAlias{c.R[dg.BX], source, word, offset, m.Read16(0x1e880 + uint32(offset))}
		}
	}
	var value uint16
	extended := false
	if alias != nil {
		value = alias.Value
	} else {
		if c.R[dg.BX]%4 != 0 || c.R[dg.BX]/4 >= 6 {
			return false, errors.New("battle presence raw index")
		}
		row := x.rows()[site.Side][c.R[dg.BX]/4]
		value = uint16(row.Count)
		extended = row.Unit != "" && x.Setup.Catalog.Profiles[row.Unit].NativeKind == 0
		if extended {
			value = 0
			if row.Count != 0 {
				value = 1
			}
		}
	}
	c.Flags = originalCountZeroFlags(c.Flags, value)
	c.IP += 5
	c.Cycles++
	x.Comparisons++
	if alias != nil {
		x.AliasReads = append(x.AliasReads, *alias)
	}
	if extended {
		x.ExtendedReads++
	}
	if x.Sites == nil {
		x.Sites = map[uint16]uint64{}
	}
	x.Sites[ip]++
	return true, nil
}

func (x *originalBattleActions) hold(m *dg.Machine, ip uint16) (bool, error) {
	if x.Casualties != nil && x.Casualties.Started && ip == 0x4626 {
		return x.Casualties.impactEnter(m)
	}
	start, end := 0x22b96, 0x22dbc
	if ip == 0x484c {
		start, end = 0x22dbc, 0x23a42
	} else if ip != 0x4626 {
		return false, errors.New("unknown attack entry")
	}
	if err := x.check(m, ip, start, end); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if !x.Active || sp > 65527 || m.Read16(0x1e880+sp+2) != 0xf67 {
		return false, errors.New("attack entry phase/stack")
	}
	caller := m.Read16(0x1e880 + sp)
	if (ip == 0x484c && caller != 0x1818) || (ip == 0x4626 && caller != 0x1718 && caller != 0x19a5) {
		return false, errors.New("attack entry caller")
	}
	source, target := m.Read16(0x1e880+sp+4), m.Read16(0x1e880+sp+6)
	if source >= 6 || target >= 6 {
		return false, errors.New("attack entry slot")
	}
	sr, tr := x.slots()[1][source], x.slots()[0][target]
	if sr >= 6 || tr >= 6 {
		return false, errors.New("attack entry raw")
	}
	s, t := x.rows()[1][sr], x.rows()[0][tr]
	if s.Count == 0 || t.Count == 0 {
		return false, errors.New("attack entry dead source/target")
	}
	v := originalEnemyTarget{ip, caller, source, target, sr, tr, s, t}
	if x.Target != nil && *x.Target != v {
		return false, errors.New("held attack target changed")
	}
	if x.Target == nil {
		x.Target = &v
	}
	if x.Rounds != nil {
		return x.Rounds.enter(m, 1, ip)
	}
	if x.Casualties != nil && ip == 0x484c {
		return x.Casualties.enter(m)
	}
	return false, errOriginalBattleTargetHeld
}

// Research-only stage. General player startup remains blocked. Every first
// enemy attack is held, including all-native controls, before fixed-table use.
func installOriginalBattleActions(e *game.Engine, setup *originalBattleSetup, comparisons bool) (*originalBattleActions, error) {
	if setup == nil || setup.Actions != nil || setup.Phase != "" || !e.PAMLoaded || e.BattleRulesMode() != "native" {
		return nil, errors.New("battle presence install lifecycle")
	}
	x := &originalBattleActions{Setup: setup}
	setup.Actions = x
	if setup.Override == nil {
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, 0x35), x.begin)
	}
	if comparisons {
		for _, site := range originalBattlePresenceSites {
			site := site
			swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, uint16(site.IDA-0x1e570)), func(m *dg.Machine) (bool, error) { return x.presence(m, site) })
		}
	}
	for _, ip := range []uint16{0x4626, 0x484c} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.hold(m, ip) })
	}
	// Player dispatch and spells have not been admitted by this contract.
	for _, ip := range []uint16{0x211a, 0x334, 0x3240, 0x3930} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) {
			if x.Rounds != nil {
				return x.Rounds.playerGate(m, ip)
			}
			if ip == 0x211a && setup.Override == nil {
				return false, nil
			}
			return false, fmt.Errorf("battle presence unsupported player/special dispatch at 0F67:%04X", ip)
		})
	}
	return x, nil
}

func (x *originalBattleActions) rows() [2][6]ArmyStack {
	if x.Rounds != nil && x.Rounds.Active {
		return x.Rounds.currentRows()
	}
	return x.Setup.Plan.Rows
}
func (x *originalBattleActions) slots() [2][6]uint16 {
	if x.Rounds != nil && x.Rounds.Active {
		return x.Rounds.Slots
	}
	return x.Setup.Plan.Slots
}
