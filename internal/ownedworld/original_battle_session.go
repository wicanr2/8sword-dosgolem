package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"math"

	dg "github.com/wicanr2/dosgolem"
)

type originalGuardOutcome struct {
	Sequence     uint64       `json:"sequence"`
	Key          string       `json:"key"`
	Cancelled    bool         `json:"cancelled"`
	ClearedVisit bool         `json:"cleared_visit"`
	Result       string       `json:"result"`
	Token        string       `json:"token"`
	Army         [6]ArmyStack `json:"army"`
	Enemy        [6]ArmyStack `json:"enemy"`
}

// All hooks retain their original pointers. Rearming changes state in place,
// only after the preceding far return and a fresh paired-store/RAM check.
type originalBattleSession struct {
	Guard                    *originalBattleGuard
	Returns, Cancels, Visits uint64
	Last                     originalGuardOutcome
}

func installOriginalBattleSession(g *originalBattleGuard) (*originalBattleSession, error) {
	if g == nil || g.Session != nil || g.Active || g.Projection == nil || g.Rounds == nil || g.Projection.Phase != "" || g.Rounds.Active || g.Rounds.Spells == nil || g.Rounds.Spells.Support == nil || g.Rounds.EnemySpells == nil {
		return nil, errors.New("guard session install lifecycle")
	}
	s := &originalBattleSession{Guard: g}
	g.Session = s
	return s, nil
}

func (s *originalBattleSession) idle() error {
	g := s.Guard
	r := g.Rounds
	a := r.Actions
	c := a.Casualties
	p := r.Spells
	e := r.EnemySpells
	if r.Active || a.Active || c.Started || a.Target != nil || r.Sorting != -1 || p.Active || p.Current != nil || e.Active || e.Current != nil || p.Support.Clone != nil {
		return errors.New("guard session has unfinished action")
	}
	if g.Captured {
		if !g.Committed || !r.Done || !r.Released || g.Projection.Phase != "captured" || g.Projection.Captures != 1 {
			return errors.New("guard session incomplete battle return")
		}
	} else if g.Committed || r.Done || r.Released || a.Setup.Phase != "" || g.Projection.Phase != "" || g.Projection.Entries != 0 {
		return errors.New("guard session unbound cancellation")
	}
	return nil
}

func (s *originalBattleSession) cancelFinish(m *dg.Machine) (bool, error) {
	g := s.Guard
	if err := g.frame(m, 0x32ad); err != nil {
		return false, err
	}
	if err := s.idle(); err != nil {
		return false, err
	}
	if g.Captured || g.RewardActive {
		return false, errors.New("guard session invalid cancel epilogue")
	}
	return false, nil
}

func (s *originalBattleSession) mapReturn(m *dg.Machine) (bool, error) {
	g := s.Guard
	if err := g.source(m, 0x25ee); err != nil {
		return false, err
	}
	if !g.Active || m.CPU.R[dg.SP] != g.EntrySP+4 || m.CPU.R[dg.BP] != g.EntryBP {
		return false, errors.New("guard session map return frame")
	}
	if err := g.data(m); err != nil {
		return false, err
	}
	if err := s.idle(); err != nil {
		return false, err
	}
	if g.Returned {
		return false, nil
	}
	snap, err := g.Port.snapshot()
	if err != nil {
		return false, err
	}
	token := g.CommittedToken
	if !g.Captured {
		token = g.Before.Token
	}
	if snap.Token != token || s.Returns == math.MaxUint64 {
		return false, errors.New("guard session return token/sequence")
	}
	s.Returns++
	cancelled := !g.Captured && !g.ClearedVisit
	if cancelled {
		s.Cancels++
	}
	if g.ClearedVisit {
		s.Visits++
	}
	s.Last = originalGuardOutcome{Sequence: s.Returns, Key: g.Guard.key(), Cancelled: cancelled, ClearedVisit: g.ClearedVisit, Result: g.Rounds.Result, Token: token, Army: snap.World.Army.Slots, Enemy: g.Enemy}
	g.Returned = true
	g.Events = append(g.Events, map[string]any{"event": "session-return", "sequence": s.Returns, "cancelled": cancelled, "token": token})
	return false, nil
}

func (s *originalBattleSession) rearm(m *dg.Machine) error {
	g := s.Guard
	if err := g.source(m, 0x2dde); err != nil {
		return err
	}
	sp := uint32(m.CPU.R[dg.SP])
	if sp > 65520 || m.Read16(0x1e880+sp) != 0x25ee || m.Read16(0x1e880+sp+2) != 0x110 || !g.Returned || g.EndingHandoff || g.Replay {
		return errors.New("guard session next entry frame/phase")
	}
	if err := s.idle(); err != nil {
		return err
	}
	snap, err := g.Port.snapshot()
	if err != nil {
		return err
	}
	if snap.World.Battle != nil {
		return errors.New("guard session persisted battle")
	}
	overlay, err := originalGuardOverlayMode(snap, g.Ending)
	if err != nil {
		return err
	}
	npc, err := originalGuardNPC(overlay)
	if err != nil {
		return err
	}
	flags, err := originalGuardFlags(overlay)
	if err != nil {
		return err
	}
	if !bytes.Equal(npc[:], m.Mem[0x1e880+0x365e:0x1e880+0x3a4e]) || !bytes.Equal(flags[:], m.Mem[0x1e880+0x275a:0x1e880+0x276a]) {
		return errors.New("guard session next NPC/swords")
	}
	for i, v := range pairWorldResources(snap.World).words() {
		if uint64(m.Read16(0x1e880+0x4f2+uint32(i*2))) != v {
			return errors.New("guard session next resources")
		}
	}
	for i := 0; i < 12; i++ {
		at := 12 + i*2
		if m.Read16(0x1e880+0x54a+uint32(i*2)) != binary.LittleEndian.Uint16(snap.Bytes.Native[at:])-uint16(at+3) {
			return errors.New("guard session native army shadow")
		}
	}
	bound, err := bindGuard(m.Mem, g.Port.Store.Catalog, g.Port.Store.Combat)
	if err != nil {
		return err
	}
	if bound.key() == "guarded:00:04" && !g.Ending {
		return errors.New("guard session ending not installed")
	}
	if rec, ok := snap.World.Encounters[bound.key()]; ok && (rec.Cleared || rec.Enemy != bound.Rows) && !(rec.Cleared && bound.key() != "guarded:00:04" && bound.Rows == [6]ArmyStack{}) {
		return errors.New("guard session cleared/changed next guard")
	}
	x, r := g.Projection, g.Rounds
	a := r.Actions
	setup, c := a.Setup, a.Casualties
	p, e := r.Spells, r.EnemySpells
	u := p.Support
	encoded, err := originalArmyProjectionBytes(snap.World.Army.Slots, x.Catalog)
	if x.HeldPreview {
		encoded, err = originalHeldProjectionBytes(snap.World.Army.Slots, x.Catalog)
	}
	if err != nil {
		return err
	}
	if setup.Override == nil {
		return errors.New("guard session missing Go army override")
	}
	// Nothing above changes Go or guest state. Commit the new runtime generation.
	*x = originalArmyProjection{GuardOnly: true, Rounds: r, Code: x.Code, Catalog: x.Catalog, Input: snap.World.Army.Slots, Encoded: encoded, HeldPreview: x.HeldPreview}
	*setup.Override = x.Input
	*setup = originalBattleSetup{Code: setup.Code, Catalog: setup.Catalog, Override: setup.Override, Actions: a}
	*a = originalBattleActions{Setup: setup, Casualties: c, Rounds: r}
	*c = originalBattleCasualties{Actions: a}
	*r = originalBattleRounds{Actions: a, Spells: p, EnemySpells: e, AllowWorld: true, Sorting: -1}
	*p = originalBattleSpells{Support: u, Engine: p.Engine, Rounds: r, Selector: -1}
	*u = originalBattleSupport{Spells: p}
	*e = originalBattleEnemy{Engine: e.Engine, Rounds: r}
	*g = originalBattleGuard{Session: s, Engine: g.Engine, Port: g.Port, Projection: x, Rounds: r, Code: g.Code, Ending: g.Ending, NPC: npc, Flags: flags}
	return nil
}
