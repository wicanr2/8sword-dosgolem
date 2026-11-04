package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var errOriginalGuardHeld = errors.New("original guard result committed; held before map return")

// The existing WorldEncounter record owns guard survivors between F7 saves.
// Restore only those records into the original opaque NPC/sword projection.
func originalGuardOverlay(p progressPairSnapshot) ([]byte, error) {
	return originalGuardOverlayMode(p, false)
}
func originalGuardOverlayMode(p progressPairSnapshot, ending bool) ([]byte, error) {
	out := bytes.Clone(p.Bytes.Native)
	if _, err := savedSwords(out); err != nil {
		return nil, err
	}
	for key, rec := range p.World.Encounters {
		if !guardedKey(key) {
			continue
		}
		var region, index int
		if _, err := fmt.Sscanf(key, "guarded:%02d:%02d", &region, &index); err != nil || region < 0 || region > 7 || index < 0 || index >= len(guardedCoordinates[region]) || key != fmt.Sprintf("guarded:%02d:%02d", region, index) || region == 0 && index == 4 && !ending {
			return nil, errors.New("original guard record identity/ending")
		}
		if region == 0 && index == 4 {
			if err := originalEndingRecord(p, rec); err != nil {
				return nil, err
			}
			if rec.Cleared {
				continue
			} // Preserve the checkpoint roster for original confirmation/replay.
		}
		rows := rec.Enemy
		if rec.Cleared {
			rows = [6]ArmyStack{}
		}
		g := &guardedBinding{Context: EncounterContext{Region: uint16(region), Index: uint16(index)}}
		var err error
		out, err = projectGuardNPC(out, g, rows)
		if err != nil {
			return nil, err
		}
		if rec.Cleared {
			out, err = projectSwords(out, region, index, 0)
			if err != nil {
				return nil, err
			}
		}
	}
	return out, nil
}

func originalGuardNPC(raw []byte) ([1008]byte, error) {
	var result [1008]byte
	for i := 0; i < 504; i++ {
		v, err := guardSavedWord(raw, 0x365e+i*2)
		if err != nil {
			return result, err
		}
		binary.LittleEndian.PutUint16(result[i*2:], v)
	}
	return result, nil
}
func originalGuardFlags(raw []byte) ([16]byte, error) {
	var result [16]byte
	flags, err := savedSwords(raw)
	if err != nil {
		return result, err
	}
	for i, v := range flags {
		if v {
			binary.LittleEndian.PutUint16(result[i*2:], 1)
		}
	}
	return result, nil
}

type originalBattleGuard struct {
	Session                                                   *originalBattleSession
	ClearedVisit                                              bool
	Engine                                                    *game.Engine
	Port                                                      *worldArmyPort
	Projection                                                *originalArmyProjection
	Rounds                                                    *originalBattleRounds
	Code                                                      []byte
	Guard                                                     *guardedBinding
	Before                                                    progressPairSnapshot
	Expected                                                  [6]uint64
	NPC                                                       [1008]byte
	Flags                                                     [16]byte
	Shadow                                                    [24]byte
	Enemy                                                     [6]ArmyStack
	EntrySP, EntryBP, RewardSP, RewardBP                      uint16
	Active, Captured, RewardActive, Committed, Returned, Hold bool
	Monthly, Power, Sword                                     bool
	Random                                                    *originalRandPlan
	Ending, Replay, EndingPrepared, EndingHandoff             bool
	EndingSP                                                  uint16
	CommittedToken                                            string
	Choice                                                    uint16
	Events                                                    []map[string]any
}

func (g *originalBattleGuard) source(m *dg.Machine, ip uint16) error {
	c := m.CPU
	if c.IP != ip || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.Cycles == math.MaxUint64 {
		return errors.New("original guard segments/site")
	}
	for _, span := range [][2]int{{0x2446, 0x2dde}, {0x2dde, 0x32e0}, {0x1abe, 0x1daa}} {
		if !bytes.Equal(g.Code[span[0]:span[1]], m.Mem[0x1100+span[0]:0x1100+span[1]]) {
			return errors.New("original guard source bytes")
		}
	}
	return nil
}
func (g *originalBattleGuard) data(m *dg.Machine) error {
	if !bytes.Equal(g.NPC[:], m.Mem[0x1e880+0x365e:0x1e880+0x3a4e]) || !bytes.Equal(g.Flags[:], m.Mem[0x1e880+0x275a:0x1e880+0x276a]) || !bytes.Equal(g.Shadow[:], m.Mem[0x1e880+0x54a:0x1e880+0x562]) {
		return errors.New("original guard NPC/sword/shadow changed")
	}
	for i, v := range g.Expected {
		if uint64(m.Read16(0x1e880+0x4f2+uint32(i*2))) != v {
			return fmt.Errorf("original guard resource %d", i)
		}
	}
	return nil
}
func (g *originalBattleGuard) begin(m *dg.Machine) (bool, error) {
	if err := g.source(m, 0x2dde); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if sp > 65520 || m.Read16(0x1e880+sp) != 0x25ee || m.Read16(0x1e880+sp+2) != 0x110 {
		return false, errors.New("original guard caller")
	}
	if g.Session != nil && g.Returned {
		if err := g.Session.rearm(m); err != nil {
			return false, err
		}
	}
	if g.Active && !g.Captured && c.R[dg.SP] == g.EntrySP && c.R[dg.BP] == g.EntryBP {
		return false, g.data(m)
	}
	if g.Active || g.Committed || g.Projection.Phase != "" || g.Rounds.Active {
		return false, errors.New("original guard repeated lifecycle")
	}
	s, err := g.Port.snapshot()
	if err != nil {
		return false, err
	}
	if s.World.Battle != nil || s.World.Army.Slots != g.Projection.Input {
		return false, errors.New("original guard army/world binding")
	}
	bound, err := bindGuard(m.Mem, g.Port.Store.Catalog, g.Port.Store.Combat)
	if err != nil {
		return false, err
	}
	if bound.Context.Region == 0 && bound.Context.Index == 4 && !g.Ending {
		return false, errors.New("original final guard handoff pending")
	}
	clearedVisit := false
	if old, ok := s.World.Encounters[bound.key()]; ok {
		clearedVisit = g.Session != nil && bound.key() != "guarded:00:04" && old.Cleared && bound.Rows == [6]ArmyStack{}
	}
	if old, ok := s.World.Encounters[bound.key()]; ok && (old.Cleared || old.Enemy != bound.Rows) && !clearedVisit && !(g.Ending && bound.key() == "guarded:00:04" && old.Cleared && old.Enemy == bound.Rows) {
		return false, errors.New("original guard cleared/changed record")
	}
	overlay, err := originalGuardOverlayMode(s, g.Ending)
	if err != nil {
		return false, err
	}
	if err = guardNPCBinding(m.Mem, overlay, bound, false); err != nil {
		return false, err
	}
	npc, err := originalGuardNPC(overlay)
	if err != nil {
		return false, err
	}
	flags, err := originalGuardFlags(overlay)
	if err != nil {
		return false, err
	}
	var shadow [24]byte
	copy(shadow[:], m.Mem[0x1e880+0x54a:0x1e880+0x562])
	expected := pairWorldResources(s.World).words()
	for i, v := range expected {
		if uint64(m.Read16(0x1e880+0x4f2+uint32(i*2))) != v {
			return false, errors.New("original guard entry resources")
		}
	}
	g.Before, g.Guard, g.Expected, g.NPC, g.Flags, g.Shadow = s, bound, expected, npc, flags, shadow
	g.EntrySP, g.EntryBP = c.R[dg.SP], c.R[dg.BP]
	g.Active = true
	g.ClearedVisit = clearedVisit
	if rec, ok := s.World.Encounters[bound.key()]; g.Ending && bound.key() == "guarded:00:04" && ok && rec.Cleared {
		g.Replay, g.Committed = true, true
		g.CommittedToken = s.Token
	}
	g.Projection.Guard = bound
	g.Events = append(g.Events, map[string]any{"event": "bound", "key": bound.key(), "context": bound.Context, "enemy": bound.Rows})
	return false, nil
}
func (g *originalBattleGuard) frame(m *dg.Machine, ip uint16) error {
	if err := g.source(m, ip); err != nil {
		return err
	}
	bp := uint32(m.CPU.R[dg.BP])
	if !g.Active || bp != uint32(g.EntrySP)-2 || m.Read16(0x1e880+bp) != g.EntryBP || m.Read16(0x1e880+bp+2) != 0x25ee || m.Read16(0x1e880+bp+4) != 0x110 {
		return errors.New("original guard frame")
	}
	return g.data(m)
}
func (g *originalBattleGuard) presence(m *dg.Machine) (bool, error) {
	if g.ClearedVisit {
		return false, errors.New("cleared guard attempted battle")
	}
	if err := g.frame(m, 0x3048); err != nil {
		return false, err
	}
	if g.Captured || g.Projection.Phase != "" {
		return false, errors.New("original guard presence phase")
	}
	if g.Replay {
		return g.replay(m)
	}
	v := uint16(1)
	for _, row := range g.Projection.Input {
		if row.Count > 0 {
			v = 0
		}
	}
	m.Write16(0x1e880+uint32(m.CPU.R[dg.BP])-4, v)
	m.CPU.IP = 0x3069
	m.CPU.Cycles++
	return true, nil
}
func (g *originalBattleGuard) afterBattle(m *dg.Machine) (bool, error) {
	if err := g.frame(m, 0x309e); err != nil {
		return false, err
	}
	c := m.CPU
	if g.Captured || !g.Rounds.Done || !g.Rounds.Released || g.Projection.Captures != 1 || c.R[dg.BP] != g.Projection.EntryBP || c.R[dg.SP] != g.Projection.EntrySP+4 || c.R[dg.AX] != g.Projection.Result || g.Guard.Rows != g.Rounds.Actions.Setup.Plan.Rows[1] {
		return false, errors.New("original guard battle return binding")
	}
	var rows [6]ArmyStack
	at := 0
	for _, row := range g.Rounds.Rows[1] {
		if row.Count > 0 {
			rows[at] = row
			at++
		}
	}
	var encoded [24]byte
	if rows[0].Count > 0 {
		var err error
		encoded, err = originalArmyProjectionBytes(rows, g.Port.Store.Combat)
		if err != nil {
			return false, err
		}
	}
	if !bytes.Equal(encoded[:], m.Mem[0x1e880+0x5700:0x1e880+0x5718]) || (g.Rounds.Result == "win") != (rows[0].Count == 0) {
		return false, errors.New("original guard enemy cleanup differs")
	}
	offset := guardNPCAt(int(g.Guard.Context.Region), int(g.Guard.Context.Index)) - 0x365e
	copy(g.NPC[offset:offset+24], encoded[:])
	copy(m.Mem[0x1e880+0x365e+offset:0x1e880+0x365e+offset+24], encoded[:])
	m.Write16(0x1e880+uint32(c.R[dg.BP])-14, g.Projection.Result)
	g.Enemy = rows
	g.Captured = true
	c.IP = 0x326e
	c.Cycles++
	g.Events = append(g.Events, map[string]any{"event": "NPC-projected", "result": g.Rounds.Result, "enemy": rows})
	return true, nil
}
func (g *originalBattleGuard) rewardBegin(m *dg.Machine) (bool, error) {
	if err := g.source(m, 0x1abe); err != nil {
		return false, err
	}
	if err := g.data(m); err != nil {
		return false, err
	}
	c := m.CPU
	sp := uint32(c.R[dg.SP])
	if !g.Captured || g.RewardActive || g.Committed || sp > 65520 || m.Read16(0x1e880+sp) != 0x32aa || m.Read16(0x1e880+sp+2) != 0x110 || m.Read16(0x1e880+sp+4) != g.Projection.Result || c.R[dg.BP] != g.Projection.EntryBP {
		return false, errors.New("original guard reward entry")
	}
	g.RewardSP, g.RewardBP = c.R[dg.SP], c.R[dg.BP]
	g.RewardActive = true
	return false, nil
}
func (g *originalBattleGuard) rewardFrame(m *dg.Machine, ip uint16) error {
	if err := g.source(m, ip); err != nil {
		return err
	}
	if err := g.data(m); err != nil {
		return err
	}
	bp := uint32(m.CPU.R[dg.BP])
	if !g.RewardActive || !g.Captured || g.Committed || bp != uint32(g.RewardSP)-2 || m.Read16(0x1e880+bp) != g.RewardBP || m.Read16(0x1e880+bp+2) != 0x32aa || m.Read16(0x1e880+bp+4) != 0x110 {
		return errors.New("original guard reward frame")
	}
	return nil
}
func (g *originalBattleGuard) reward(m *dg.Machine, ip uint16) (bool, error) {
	if err := g.rewardFrame(m, ip); err != nil {
		return false, err
	}
	c := m.CPU
	length := uint16(4)
	region := uint64(g.Guard.Context.Region)
	switch ip {
	case 0x1b7b:
		if g.Rounds.Result != "win" || g.Monthly || uint64(c.R[dg.AX]) != 20*(region+1) {
			return false, errors.New("original guard salary award")
		}
		g.Expected[2] = min(uint64(30000), g.Expected[2]+20*(region+1))
		m.Write16(0x1e880+0x4f6, uint16(g.Expected[2]))
		g.Monthly = true
	case 0x1bd6:
		if g.Rounds.Result != "win" || !g.Monthly || g.Power || g.Guard.Context.Legacy26AA != 1 || m.Read16(0x1e880+0x26aa) != 1 || uint64(c.R[dg.AX]) != region+1 {
			return false, errors.New("original guard spell-power award")
		}
		g.Expected[5] = min(uint64(30000), g.Expected[5]+region+1)
		m.Write16(0x1e880+0x4fc, uint16(g.Expected[5]))
		g.Power = true
	case 0x1c7f:
		if g.Rounds.Result != "win" || !g.Monthly || !g.Guard.Context.Boss || g.Sword || c.R[dg.BX] != uint16(region*2) {
			return false, errors.New("original guard sword award")
		}
		m.Write16(0x1e880+0x275a+uint32(region*2), 1)
		binary.LittleEndian.PutUint16(g.Flags[region*2:], 1)
		g.Sword = true
		length = 6
	case 0x1cd8:
		if g.Rounds.Result == "win" {
			return false, errors.New("original guard wrong failure branch")
		}
		alive := uint16(0)
		if g.Projection.Remaining[0].Count > 0 {
			alive = 1
		}
		c.Flags = roundSubFlags(c.Flags, alive, 0)
		length = 5
	case 0x1d03:
		if g.Rounds.Result != "retreat" || g.Random != nil {
			return false, errors.New("original guard retreat RNG phase")
		}
		if err := checkOriginalRand(g.Engine.Oracle, g.Code); err != nil {
			return false, err
		}
		plan := planOriginalRand(originalSeed(g.Engine.Oracle))
		g.Random = &plan
		m.Write16(0x1e880+0x81bc, uint16(plan.After))
		m.Write16(0x1e880+0x81be, uint16(plan.After>>16))
		c.R[dg.AX] = plan.Value
		length = 5
	case 0x1d1c:
		if g.Rounds.Result != "retreat" || g.Random == nil {
			return false, errors.New("original guard retreat penalty phase")
		}
		n, err := retreatPenalty(g.Expected[3], uint32(g.Random.Value))
		if err != nil {
			return false, err
		}
		if uint64(c.R[dg.AX]) != n {
			return false, errors.New("original guard penalty amount")
		}
		g.Expected[3] -= n
		m.Write16(0x1e880+0x4f8, uint16(g.Expected[3]))
	default:
		return false, errors.New("original guard unknown reward operation")
	}
	c.IP += length
	c.Cycles++
	g.Events = append(g.Events, map[string]any{"event": "reward", "ip": ip, "resources": g.Expected})
	return true, nil
}
func (g *originalBattleGuard) finish(m *dg.Machine) (bool, error) {
	if g.Session != nil && !g.Captured {
		return g.Session.cancelFinish(m)
	}
	if err := g.frame(m, 0x32ad); err != nil {
		return false, err
	}
	if m.CPU.R[dg.SP] != g.Projection.EntrySP+4 || !g.RewardActive || !g.Captured {
		return false, errors.New("original guard final frame/phase")
	}
	if g.Committed {
		if g.Hold {
			return false, errOriginalGuardHeld
		}
		return false, nil
	}
	if g.Rounds.Result == "win" {
		if !g.Monthly || g.Power != (g.Guard.Context.Legacy26AA == 1) || g.Sword != g.Guard.Context.Boss {
			return false, errors.New("original guard missing award")
		}
	} else if g.Monthly || g.Power || g.Sword || (g.Rounds.Result == "retreat" && g.Random == nil) || (g.Rounds.Result == "loss" && (g.Choice < 1 || g.Choice > 2)) {
		return false, errors.New("original guard failure outcome")
	}
	return g.commitWorld()
}
func (g *originalBattleGuard) commitWorld() (bool, error) {
	w := cloneCampWorld(g.Before.World)
	if w.Revision == math.MaxUint64 {
		return false, errors.New("original guard revision")
	}
	w.Revision++
	w.Army.Slots = g.Projection.Remaining
	w.Army.Gold = g.Expected[3]
	w.Army.Leadership = g.Expected[4]
	w.Army.RecruitRank = uint32(g.Expected[0])
	w.Progress.Rank = uint32(g.Expected[0])
	w.Progress.Merit = g.Expected[1]
	w.Progress.Legacy04F6 = g.Expected[2]
	w.Progress.Legacy04FC = g.Expected[5]
	record := WorldEncounter{Enemy: g.Enemy, Cleared: g.Rounds.Result == "win"}
	if record.Cleared {
		record.Enemy = g.Guard.Rows
		if g.final() {
			var err error
			record.Enemy, err = originalEndingCheckpoint(g.Before.Bytes.Native)
			if err != nil {
				return false, err
			}
		}
	}
	w.Encounters[g.Guard.key()] = record
	s, err := g.Port.Store.Commit(g.Before.Token, w)
	if err != nil {
		return false, err
	}
	g.Port.Current = s
	g.Committed = true
	g.CommittedToken = s.Token
	g.Events = append(g.Events, map[string]any{"event": "committed", "key": g.Guard.key(), "token": s.Token, "resources": g.Expected})
	if g.Hold {
		return false, errOriginalGuardHeld
	}
	return false, nil
}
func installOriginalBattleGuard(e *game.Engine, p *worldArmyPort, x *originalArmyProjection, r *originalBattleRounds) (*originalBattleGuard, error) {
	return installOriginalBattleGuardMode(e, p, x, r, false)
}
func installOriginalBattleGuardMode(e *game.Engine, p *worldArmyPort, x *originalArmyProjection, r *originalBattleRounds, ending bool) (*originalBattleGuard, error) {
	if !e.PAMLoaded || p == nil || p.Store == nil || x == nil || r == nil || x.Rounds != r || x.Phase != "" || x.GuardOnly || r.Active || e.BattleRulesMode() != "native" {
		return nil, errors.New("original guard install lifecycle")
	}
	code, err := worldArmyCode(e.PAM)
	if err != nil {
		return nil, err
	}
	s, err := p.snapshot()
	if err != nil {
		return nil, err
	}
	if s.World.Battle != nil || s.World.Army.Slots != x.Input {
		return nil, errors.New("original guard install army")
	}
	overlay, err := originalGuardOverlayMode(s, ending)
	if err != nil {
		return nil, err
	}
	beforeNPC, err := originalGuardNPC(s.Bytes.Native)
	if err != nil {
		return nil, err
	}
	beforeFlags, err := originalGuardFlags(s.Bytes.Native)
	if err != nil {
		return nil, err
	}
	npc, err := originalGuardNPC(overlay)
	if err != nil {
		return nil, err
	}
	flags, err := originalGuardFlags(overlay)
	if err != nil {
		return nil, err
	}
	if !bytes.Equal(beforeNPC[:], e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)) || !bytes.Equal(beforeFlags[:], e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)) {
		return nil, errors.New("original guard cold native projection")
	}
	if guardedSignature(e.Oracle.Bytes(oracle.Far(0, 0), 1<<20)) != guardedCodeSHA {
		return nil, errors.New("original guard cold source")
	}
	for i := 0; i < 504; i++ {
		e.Oracle.WriteU16(oracle.Far(0x1e88, 0x365e+uint16(i*2)), binary.LittleEndian.Uint16(npc[i*2:]))
	}
	for i := 0; i < 8; i++ {
		e.Oracle.WriteU16(oracle.Far(0x1e88, 0x275a+uint16(i*2)), binary.LittleEndian.Uint16(flags[i*2:]))
	}
	x.GuardOnly = true
	r.AllowWorld = true
	g := &originalBattleGuard{Engine: e, Port: p, Projection: x, Rounds: r, Code: code, NPC: npc, Flags: flags, Ending: ending}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x2dde), g.begin)
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x3048), g.presence)
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x309e), g.afterBattle)
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x1abe), g.rewardBegin)
	for _, ip := range []uint16{0x1b7b, 0x1bd6, 0x1c7f, 0x1cd8, 0x1d03, 0x1d1c} {
		ip := ip
		swordOnHostInstruction(e.Oracle, oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return g.reward(m, ip) })
	}
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x1d48), func(m *dg.Machine) (bool, error) {
		if err := g.rewardFrame(m, 0x1d48); err != nil {
			return false, err
		}
		if g.Rounds.Result != "loss" || m.CPU.R[dg.AX] < 1 || m.CPU.R[dg.AX] > 2 {
			return false, errors.New("original guard defeat choice")
		}
		g.Choice = m.CPU.R[dg.AX]
		return false, nil
	})
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x32ad), g.finish)
	swordOnHostInstruction(e.Oracle, oracle.Far(0x110, 0x25ee), func(m *dg.Machine) (bool, error) {
		if g.Session != nil {
			return g.Session.mapReturn(m)
		}
		if !g.Committed {
			return false, nil
		}
		if err := g.source(m, 0x25ee); err != nil {
			return false, err
		}
		if err := g.data(m); err != nil {
			return false, err
		}
		if m.CPU.R[dg.SP] != g.EntrySP+4 || m.CPU.R[dg.BP] != g.EntryBP {
			return false, errors.New("original guard map return frame")
		}
		g.Returned = true
		return false, nil
	})
	if ending {
		installOriginalEndingHooks(g)
	}
	return g, nil
}
