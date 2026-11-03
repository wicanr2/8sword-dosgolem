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

// Spec030 READY: keep original random-encounter settlement UI and map return.
// Army identity and all six strategic resource mutations belong to Go.
type originalBattleWorld struct {
	Engine                      *game.Engine
	Port                        *worldArmyPort
	Projection                  *originalArmyProjection
	Rounds                      *originalBattleRounds
	Code                        []byte
	Token                       string
	Before                      OwnedWorld
	Expected                    [6]uint64
	RewardGold, RewardMerit     uint64
	EntrySP, EntryBP            uint16
	Active, Committed, Returned bool
	Writes                      map[uint16]bool
	Random                      *originalRandPlan
	Choice                      uint16
	Events                      []map[string]any
}

func (v *originalBattleWorld) check(m *dg.Machine, ip uint16) error {
	c := m.CPU
	if c.IP != ip || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == math.MaxUint64 {
		return errors.New("battle world segments/site")
	}
	for _, span := range [][2]int{{0x151c, 0x1796}, {0x1796, 0x1abe}} {
		if !bytes.Equal(v.Code[span[0]:span[1]], m.Mem[0x1100+span[0]:0x1100+span[1]]) {
			return errors.New("battle world source")
		}
	}
	if !v.Rounds.Done || !v.Rounds.Released || v.Projection.Captures != 1 || !bytes.Equal(v.Projection.Shadow, m.Mem[0x1e880+0x54a:0x1e880+0x562]) {
		return errors.New("battle world result/shadow")
	}
	return nil
}

func (v *originalBattleWorld) resources(m *dg.Machine) error {
	for i, n := range v.Expected {
		if uint64(m.Read16(0x1e880+0x4f2+uint32(i*2))) != n {
			return fmt.Errorf("battle world resource %d", i)
		}
	}
	return nil
}

func (v *originalBattleWorld) begin(m *dg.Machine) (bool, error) {
	if err := v.check(m, 0x1796); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if v.Active || v.Committed || sp < 32 || sp > 65520 || m.Read16(0x1e880+sp) != 0x172b || m.Read16(0x1e880+sp+2) != 0x110 || m.Read16(0x1e880+sp+4) != v.Projection.Result {
		return false, errors.New("battle world entry")
	}
	s, err := v.Port.snapshot()
	if err != nil {
		return false, err
	}
	if s.World.Army.Slots != v.Projection.Input || s.World.Battle != nil {
		return false, errors.New("battle world army binding")
	}
	v.Token, v.Before = s.Token, s.World
	v.Expected = pairWorldResources(s.World).words()
	if err = v.resources(m); err != nil {
		return false, err
	}
	for i, n := range s.World.Progress.Thresholds {
		if uint64(m.Read16(0x1e880+0x5b2+uint32(i*2))) != n {
			return false, errors.New("battle world threshold binding")
		}
	}
	idx, err := v.Port.Store.Catalog.index()
	if err != nil {
		return false, err
	}
	var command uint64
	for _, row := range v.Rounds.Actions.Setup.Plan.Rows[1] {
		if row.Count == 0 {
			continue
		}
		p, ok := idx[row.Unit]
		if !ok || p.NativeKind == 0 {
			return false, errors.New("battle world enemy identity")
		}
		gold := uint64(row.Count) * p.Gold
		weight := uint64(row.Count) * p.Command
		if v.RewardGold > math.MaxUint64-gold || command > math.MaxUint64-weight {
			return false, errors.New("battle world reward overflow")
		}
		v.RewardGold += gold
		command += weight
	}
	v.RewardMerit = command / 2
	seg := uint32(m.Read16(0x1e880+0x8362)) * 16
	if v.RewardGold > 32767 || v.RewardMerit > 32767 || uint64(m.Read16(0x1e880+0x8e84)) != v.RewardMerit || uint64(m.Read16(seg+0x3e)) != v.RewardGold {
		return false, errors.New("battle world reward binding")
	}
	v.EntrySP, v.EntryBP = c.R[dg.SP], c.R[dg.BP]
	v.Active = true
	v.Writes = map[uint16]bool{}
	return false, nil
}

func (v *originalBattleWorld) frame(m *dg.Machine, ip uint16) error {
	if err := v.check(m, ip); err != nil {
		return err
	}
	bp := uint32(m.CPU.R[dg.BP])
	sp := uint32(m.CPU.R[dg.SP])
	if !v.Active || v.Committed || bp != uint32(v.EntrySP)-2 || sp != bp-4 || m.Read16(0x1e880+bp) != v.EntryBP || m.Read16(0x1e880+bp+2) != 0x172b || m.Read16(0x1e880+bp+4) != 0x110 {
		return errors.New("battle world frame")
	}
	return v.resources(m)
}

func (v *originalBattleWorld) execute(m *dg.Machine, ip uint16) (bool, error) {
	if err := v.frame(m, ip); err != nil {
		return false, err
	}
	c := m.CPU
	if v.Writes[ip] {
		return false, errors.New("battle world duplicate operation")
	}
	step := uint16(4)
	index := -1
	var next uint64
	switch ip {
	case 0x1895:
		if v.Rounds.Result != "win" || uint64(c.R[dg.AX]) != v.RewardMerit {
			return false, errors.New("battle world merit")
		}
		index = 1
		next = min(v.Expected[1]+v.RewardMerit, 30000)
	case 0x18a5:
		if v.Rounds.Result != "win" || !v.Writes[0x1895] || uint64(c.R[dg.AX]) != v.RewardGold {
			return false, errors.New("battle world gold")
		}
		index = 3
		next = min(v.Expected[3]+v.RewardGold, 30000)
	case 0x1900:
		if v.Rounds.Result == "win" {
			return false, errors.New("battle world wrong failure branch")
		}
		alive := uint16(0)
		if v.Projection.Remaining[0].Count > 0 {
			alive = 1
		}
		c.Flags = roundSubFlags(c.Flags, alive, 0)
		step = 5
	case 0x192b:
		if v.Rounds.Result != "retreat" || v.Random != nil {
			return false, errors.New("battle world retreat RNG phase")
		}
		if err := checkOriginalRand(v.Engine.Oracle, v.Code); err != nil {
			return false, err
		}
		plan := planOriginalRand(originalSeed(v.Engine.Oracle))
		v.Random = &plan
		m.Write16(0x1e880+0x81bc, uint16(plan.After))
		m.Write16(0x1e880+0x81be, uint16(plan.After>>16))
		c.R[dg.AX] = plan.Value
		step = 5
	case 0x1944:
		if v.Rounds.Result != "retreat" || v.Random == nil {
			return false, errors.New("battle world retreat phase")
		}
		penalty, err := retreatPenalty(v.Expected[3], uint32(v.Random.Value))
		if err != nil {
			return false, err
		}
		if uint64(c.R[dg.AX]) != penalty {
			return false, errors.New("battle world retreat amount")
		}
		index = 3
		next = v.Expected[3] - penalty
	case 0x19e8:
		if v.Rounds.Result == "loss" || v.Expected[0] >= 5 || v.Expected[1] <= v.Before.Progress.Thresholds[v.Expected[0]] {
			return false, errors.New("battle world promotion")
		}
		index = 0
		next = v.Expected[0] + 1
	case 0x19ec, 0x19f5, 0x1a07:
		if !v.Writes[0x19e8] {
			return false, errors.New("battle world promotion order")
		}
		switch ip {
		case 0x19ec:
			index = 2
			next = min(v.Expected[2]+100, 30000)
			step = 5
		case 0x19f5:
			index = 4
			next = min(v.Expected[4]+100, 30000)
			step = 5
		case 0x1a07:
			index = 5
			next = min(v.Expected[5]+v.Expected[0]*3, 30000)
			if uint64(c.R[dg.AX]) != v.Expected[0]*3 {
				return false, errors.New("battle world spell power")
			}
		}
	default:
		return false, errors.New("battle world unknown operation")
	}
	if index >= 0 {
		m.Write16(0x1e880+0x4f2+uint32(index*2), uint16(next))
		v.Expected[index] = next
	}
	v.Writes[ip] = true
	c.IP += step
	c.Cycles++
	v.Events = append(v.Events, map[string]any{"ip": ip, "resources": v.Expected})
	return true, nil
}

func (v *originalBattleWorld) finish(m *dg.Machine, ip uint16) (bool, error) {
	if v.Committed {
		return false, nil
	}
	if err := v.frame(m, ip); err != nil {
		return false, err
	}
	if ip == 0x19b8 {
		if v.Rounds.Result != "loss" || v.Choice < 1 || v.Choice > 2 {
			return false, errors.New("battle world defeat choice")
		}
	} else if ip == 0x1ab8 {
		if v.Rounds.Result == "loss" {
			return false, errors.New("battle world loss entered promotion")
		}
		promoted := v.Expected[0] != uint64(v.Before.Progress.Rank)
		if (v.Expected[0] < 5 && v.Expected[1] > v.Before.Progress.Thresholds[v.Expected[0]]) && !promoted {
			return false, errors.New("battle world missed promotion")
		}
		if v.Rounds.Result == "win" && (!v.Writes[0x1895] || !v.Writes[0x18a5]) {
			return false, errors.New("battle world reward incomplete")
		}
		if v.Rounds.Result == "retreat" && !v.Writes[0x1944] {
			return false, errors.New("battle world penalty incomplete")
		}
	} else {
		return false, errors.New("battle world unknown return")
	}
	w := v.Before
	if w.Revision == math.MaxUint64 {
		return false, errors.New("battle world revision")
	}
	w.Revision++
	w.Army.Slots = v.Projection.Remaining
	w.Army.Gold = v.Expected[3]
	w.Army.Leadership = v.Expected[4]
	w.Army.RecruitRank = uint32(v.Expected[0])
	w.Progress.Rank = uint32(v.Expected[0])
	w.Progress.Merit = v.Expected[1]
	w.Progress.Legacy04F6 = v.Expected[2]
	w.Progress.Legacy04FC = v.Expected[5]
	s, err := v.Port.Store.Commit(v.Token, w)
	if err != nil {
		return false, err
	}
	v.Port.Current = s
	v.Token = s.Token
	v.Committed = true
	v.Events = append(v.Events, map[string]any{"result": v.Rounds.Result, "choice": v.Choice, "resources": v.Expected, "committed": true})
	return false, nil
}

func installOriginalBattleWorld(e *game.Engine, p *worldArmyPort, projection *originalArmyProjection, rounds *originalBattleRounds) (*originalBattleWorld, error) {
	if projection == nil || rounds == nil || projection.Rounds != rounds || p == nil || p.Store == nil {
		return nil, errors.New("battle world install binding")
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	v := &originalBattleWorld{Engine: e, Port: p, Projection: projection, Rounds: rounds, Code: code}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x1796), v.begin)
	for _, ip := range []uint16{0x1895, 0x18a5, 0x1900, 0x192b, 0x1944, 0x19e8, 0x19ec, 0x19f5, 0x1a07} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return v.execute(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x1970), func(m *dg.Machine) (bool, error) {
		if err := v.frame(m, 0x1970); err != nil {
			return false, err
		}
		if v.Rounds.Result != "loss" || m.CPU.R[dg.AX] < 1 || m.CPU.R[dg.AX] > 2 {
			return false, errors.New("battle world original loss option")
		}
		v.Choice = m.CPU.R[dg.AX]
		return false, nil
	})
	for _, ip := range []uint16{0x19b8, 0x1ab8} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return v.finish(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0xbd3), func(m *dg.Machine) (bool, error) {
		if v.Committed {
			if err := v.resources(m); err != nil {
				return false, err
			}
			v.Active = false
			v.Returned = true
		}
		return false, nil
	})
	return v, nil
}
