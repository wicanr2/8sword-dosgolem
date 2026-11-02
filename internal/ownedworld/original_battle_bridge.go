package ownedworld

import (
	"bytes"
	"errors"
	"fmt"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec030 READY: original battle controls and effects, Go ordinary arithmetic.
// This candidate is not installed by the ordinary player entry.
type originalBattleArithmetic struct {
	Code    []byte
	Catalog game.OwnedCombatCatalog
	Enabled bool
	Calls   []originalBattleAmount
}
type originalBattleAmount struct {
	IP, Source, Target, SourceKind, TargetKind, SourceCount uint16
	Divisor, Multiplier, BeforeHP, AfterHP, Encoded         uint16
	Damage                                                  uint64
}

func originalBattleAmountFor(attack uint64, count uint16, hp uint64, divisor, multiplier uint16) (uint64, uint16, error) {
	if attack == 0 || hp == 0 || divisor == 0 || multiplier == 0 || attack > math.MaxUint64/uint64(max(count, 1)) {
		return 0, 0, errors.New("original bridge arithmetic input")
	}
	amount := attack * uint64(count) / uint64(divisor)
	if amount > math.MaxUint64/uint64(multiplier) {
		return 0, 0, errors.New("original bridge multiplication overflow")
	}
	amount *= uint64(multiplier)
	encoded := amount/hp + 1
	if amount > 65535 || encoded > 65535 {
		return 0, 0, errors.New("original bridge word result exceeds admitted range")
	}
	return amount, uint16(encoded), nil
}

func (x *originalBattleArithmetic) execute(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"original battle arithmetic: " + s} }
	c := m.CPU
	if !x.Enabled || c.IP != ip || c.Seg[dg.CS] != 0xf67 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.R[dg.SP] > 65527 || c.Cycles == math.MaxUint64 {
		return fail("site/segments/disabled")
	}
	start, end := uint16(0x1532), uint16(0x1592)
	if ip == 0x1592 {
		start, end = 0x1592, 0x15fc
	} else if ip != 0x1532 {
		return fail("unknown helper")
	}
	at := 0xe570 + int(start)
	if !bytes.Equal(x.Code[at:0xe570+int(end)], m.Mem[0xf670+int(start):0xf670+int(end)]) {
		return fail("helper source")
	}
	ds := uint32(0x1e880)
	sp := uint32(c.R[dg.SP])
	ret, seg := m.Read16(ds+sp), m.Read16(ds+sp+2)
	if seg != 0xf67 || ip == 0x1532 && (ret != 0x4658 && ret != 0x48b2) || ip == 0x1592 && ret != 0x32d9 {
		return fail("original caller")
	}
	source, target := m.Read16(ds+sp+4), m.Read16(ds+sp+6)
	if source >= 6 || target >= 6 {
		return fail("unit index")
	}
	sourceBase, targetBase, hpBase := uint32(0x5700), uint32(0x56e8), uint32(0x8ca4)
	divisor, multiplier := uint16(0), uint16(1)
	if ip == 0x1532 {
		d := uint32(m.Read16(ds+0x26ac)) + 5
		if d > 65535 {
			return fail("enemy divisor")
		}
		divisor = uint16(d)
	} else {
		modifier := m.Read16(ds + 0x26b2)
		boost := m.Read16(ds + 0x26b8)
		if modifier >= 5 || boost == 65535 {
			return fail("player divisor/multiplier")
		}
		divisor, multiplier = 5-modifier, boost+1
		sourceBase, targetBase, hpBase = 0x56e8, 0x5700, 0x8e60
	}
	sk, tk := m.Read16(ds+sourceBase+uint32(source)*4), m.Read16(ds+targetBase+uint32(target)*4)
	count, tc := m.Read16(ds+sourceBase+uint32(source)*4+2), m.Read16(ds+targetBase+uint32(target)*4+2)
	if sk < 1 || sk > 25 || tk < 1 || tk > 25 || count == 0 || tc == 0 {
		return fail("native profile/alive range")
	}
	sProfile, ok := x.Catalog.Profiles[fmt.Sprintf("native:%02d", sk)]
	tProfile, ok2 := x.Catalog.Profiles[fmt.Sprintf("native:%02d", tk)]
	if !ok || !ok2 || sProfile.NativeKind != sk || tProfile.NativeKind != tk || uint64(m.Read16(ds+0x70ce+uint32(sk)*4)) != sProfile.Attack || uint64(m.Read16(ds+0x70d0+uint32(tk)*4)) != tProfile.HP {
		return fail("typed catalog/factor binding")
	}
	damage, encoded, err := originalBattleAmountFor(sProfile.Attack, count, tProfile.HP, divisor, multiplier)
	if err != nil {
		return fail(err.Error())
	}
	address := ds + hpBase + uint32(target)*2
	before := m.Read16(address)
	after := before - uint16(damage)
	m.Write16(address, after)
	c.R[dg.AX] = encoded
	c.R[dg.SP] += 4
	c.IP = ret
	c.Cycles++
	x.Calls = append(x.Calls, originalBattleAmount{ip, source, target, sk, tk, count, divisor, multiplier, before, after, encoded, damage})
	return true, nil
}

func installOriginalBattleArithmetic(e *game.Engine, catalog game.OwnedCombatCatalog) (*originalBattleArithmetic, error) {
	if e.BattleRulesMode() != "native" {
		return nil, errors.New("original arithmetic candidate requires native rules")
	}
	if err := catalog.Validate(); err != nil {
		return nil, err
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	x := &originalBattleArithmetic{Code: code, Catalog: catalog, Enabled: true}
	for _, ip := range []uint16{0x1532, 0x1592} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0xf67, ip), func(m *dg.Machine) (bool, error) { return x.execute(m, ip) })
		swordOnCall(e.Oracle, oracle.Far(0xf67, ip+1), func(*oracle.Oracle) { panic(&worldArmyPortFault{"original arithmetic helper escaped Go bridge"}) })
	}
	return x, nil
}
