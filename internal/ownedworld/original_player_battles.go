package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

// Spec030: one original battlefield, two original world-return protocols.
// All per-action callbacks retain their pointers across both encounter kinds.
type originalPlayerBattles struct {
	Guard            *originalBattleGuard
	World            *originalBattleWorld
	Presence         *armyPresence
	Mode             string
	Sequence         uint64
	RandomReturned   bool
	EntrySP, EntryBP uint16
	EntryToken       string
	Events           []map[string]any
}

func installOriginalPlayerBattles(e *game.Engine, p *worldArmyPort, artDir string) (*originalPlayerBattles, error) {
	if p == nil || p.PlayerBattles != nil {
		return nil, errors.New("player battle install binding")
	}
	army := p.Current.World.Army.Slots
	x, err := installOriginalArmyProjectionAdmission(e, p.Store.Combat, army, true, true)
	if err != nil {
		return nil, err
	}
	setup, err := installOriginalBattleSetup(e, p.Store.Combat, &army)
	if err != nil {
		return nil, err
	}
	a, err := installOriginalBattleActions(e, setup, true)
	if err != nil {
		return nil, err
	}
	r, err := installOriginalBattleRounds(e, a)
	if err != nil {
		return nil, err
	}
	x.Rounds = r
	sp, err := installOriginalBattleSpells(e, r)
	if err != nil {
		return nil, err
	}
	if _, err = installOriginalBattleSupport(e, sp); err != nil {
		return nil, err
	}
	if _, err = installOriginalBattleEnemy(e, r); err != nil {
		return nil, err
	}
	g, err := installOriginalBattleGuardMode(e, p, x, r, true)
	if err != nil {
		return nil, err
	}
	if _, err = installOriginalBattleSession(g); err != nil {
		return nil, err
	}
	w, err := installOriginalBattleWorld(e, p, x, r)
	if err != nil {
		return nil, err
	}
	presence, err := installArmyPresence(e, p)
	if err != nil {
		return nil, err
	}
	s := &originalPlayerBattles{Guard: g, World: w, Presence: presence}
	if artDir != "" {
		if _, err = installOriginalBattleArt(g, artDir); err != nil {
			return nil, err
		}
	}
	p.PlayerBattles = s
	for _, item := range []struct {
		ip   uint16
		mode string
	}{{0x1650, "random"}, {0x2dde, "guard"}} {
		item := item
		swordOnCall(e.Oracle, oracle.Far(0x110, item.ip), func(o *oracle.Oracle) {
			if err := s.prepare(o, item.mode); err != nil {
				panic(&worldArmyPortFault{err.Error()})
			}
		})
	}
	swordOnCall(e.Oracle, oracle.Far(0x110, 0xbd3), func(o *oracle.Oracle) {
		if s.Mode == "random" {
			if err := s.randomReturn(o); err != nil {
				panic(&worldArmyPortFault{err.Error()})
			}
		}
	})
	return s, nil
}

func (s *originalPlayerBattles) returned() bool {
	if s.Mode == "guard" {
		return s.Guard.Returned
	}
	if s.Mode == "random" {
		return s.RandomReturned && (!s.World.Active || s.World.Committed)
	}
	return true
}

func (s *originalPlayerBattles) idle() error {
	g := s.Guard
	r := g.Rounds
	a := r.Actions
	c := a.Casualties
	p := r.Spells
	enemy := r.EnemySpells
	if r.Active || a.Active || c.Started || a.Target != nil || r.Sorting != -1 || p.Active || p.Current != nil || enemy.Active || enemy.Current != nil || p.Support.Clone != nil {
		return errors.New("player battle has unfinished action")
	}
	if s.Mode == "" {
		if g.Projection.Phase != "" || r.Done {
			return errors.New("player battle initial state")
		}
		return nil
	}
	if !s.returned() {
		return errors.New("player battle has not returned")
	}
	if s.Mode == "guard" {
		return g.Session.idle()
	}
	if g.Projection.Phase == "" {
		if r.Done || s.World.Active || s.World.Committed {
			return errors.New("player random cancellation state")
		}
		return nil
	}
	if g.Projection.Phase != "captured" || !r.Done || !r.Released || !s.World.Committed || !s.World.Returned || g.Projection.Captures != 1 {
		return errors.New("player random incomplete result")
	}
	return nil
}

func (s *originalPlayerBattles) prepare(o *oracle.Oracle, mode string) error {
	g := s.Guard
	regs := o.Regs()
	if regs.CS != 0x110 || regs.DS != 0x1e88 || regs.SS != 0x1e88 {
		return errors.New("player encounter segments")
	}
	if mode == "guard" {
		if regs.IP != 0x2dde || regs.SP > 65520 || o.Word(oracle.Far(regs.SS, regs.SP)) != 0x25ee || o.Word(oracle.Far(regs.SS, regs.SP+2)) != 0x110 {
			return errors.New("player guard caller")
		}
	} else if mode == "random" {
		if regs.IP != 0x1650 || regs.BP < 32 || regs.BP > 65520 || regs.SP > regs.BP || o.Word(oracle.Far(regs.SS, regs.BP+2)) != 0xbd3 || o.Word(oracle.Far(regs.SS, regs.BP+4)) != 0x110 {
			return errors.New("player random caller")
		}
	} else {
		return errors.New("player encounter kind")
	}
	for _, span := range [][2]int{{0x151c, 0x1daa}, {0x2446, 0x3774}} {
		if !bytes.Equal(g.Code[span[0]:span[1]], o.Bytes(oracle.Far(0x110, uint16(span[0])), span[1]-span[0])) {
			return errors.New("player encounter source")
		}
	}
	snap, err := g.Port.snapshot()
	if err != nil {
		return err
	}
	// A hook notification may repeat before its original host instruction runs.
	if s.Mode == mode && !s.returned() && regs.SP == s.EntrySP && regs.BP == s.EntryBP && snap.Token == s.EntryToken && g.Projection.Phase == "" && !g.Active && !s.Presence.Active {
		return nil
	}
	if err = s.idle(); err != nil {
		return err
	}
	if s.Presence.Active {
		return errors.New("player presence not returned")
	}
	overlay, err := originalGuardOverlayMode(snap, true)
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
	if !bytes.Equal(npc[:], o.Bytes(oracle.Far(0x1e88, 0x365e), 1008)) || !bytes.Equal(flags[:], o.Bytes(oracle.Far(0x1e88, 0x275a), 16)) {
		return errors.New("player encounter NPC/swords")
	}
	for i, n := range pairWorldResources(snap.World).words() {
		if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return errors.New("player encounter resources")
		}
	}
	for i := 0; i < 12; i++ {
		at := 12 + i*2
		if o.Word(oracle.Far(0x1e88, 0x54a+uint16(i*2))) != binary.LittleEndian.Uint16(snap.Bytes.Native[at:])-uint16(at+3) {
			return errors.New("player encounter original shadow")
		}
	}
	encoded, err := originalHeldProjectionBytes(snap.World.Army.Slots, g.Port.Store.Combat)
	if snap.World.Army.Slots == ([6]ArmyStack{}) {
		encoded = [24]byte{}
		err = nil
	}
	if err != nil {
		return err
	}
	// Validation above is read-only. Reset exactly the existing eight objects.
	x, r := g.Projection, g.Rounds
	a := r.Actions
	setup, c := a.Setup, a.Casualties
	p, enemy := r.Spells, r.EnemySpells
	support := p.Support
	*x = originalArmyProjection{GuardOnly: mode == "guard", Rounds: r, Code: x.Code, Catalog: x.Catalog, Input: snap.World.Army.Slots, Encoded: encoded, HeldPreview: true}
	*setup.Override = x.Input
	*setup = originalBattleSetup{Code: setup.Code, Catalog: setup.Catalog, Override: setup.Override, Actions: a}
	*a = originalBattleActions{Setup: setup, Casualties: c, Rounds: r}
	*c = originalBattleCasualties{Actions: a}
	*r = originalBattleRounds{Actions: a, Spells: p, EnemySpells: enemy, AllowWorld: true, Sorting: -1}
	*p = originalBattleSpells{Support: support, Engine: p.Engine, Rounds: r, Selector: -1}
	*support = originalBattleSupport{Spells: p}
	*enemy = originalBattleEnemy{Engine: enemy.Engine, Rounds: r}
	*g = originalBattleGuard{Session: g.Session, Engine: g.Engine, Port: g.Port, Projection: x, Rounds: r, Code: g.Code, Ending: true, NPC: npc, Flags: flags}
	w := s.World
	*w = originalBattleWorld{Engine: w.Engine, Port: w.Port, Projection: x, Rounds: r, Code: w.Code}
	s.Mode = mode
	s.Sequence++
	s.RandomReturned = false
	s.EntrySP, s.EntryBP = regs.SP, regs.BP
	s.EntryToken = snap.Token
	s.Events = append(s.Events, map[string]any{"event": "prepare", "mode": mode, "sequence": s.Sequence, "army": x.Input, "token": snap.Token})
	return nil
}

func (s *originalPlayerBattles) randomReturn(o *oracle.Oracle) error {
	if s.RandomReturned {
		return nil
	}
	p := s.Presence
	r := o.Regs()
	if r.CS != 0x110 || r.IP != 0xbd3 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP != p.BP+6 {
		return errors.New("player random return frame")
	}
	if s.Guard.Projection.Phase != "" && (!s.World.Committed || !s.Guard.Rounds.Done || !s.Guard.Rounds.Released) {
		return errors.New("player random return incomplete")
	}
	snap, err := s.Guard.Port.snapshot()
	if err != nil {
		return err
	}
	for i, n := range pairWorldResources(snap.World).words() {
		if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			return fmt.Errorf("player random return resource %d", i)
		}
	}
	if !bytes.Equal(p.NativeRows, o.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		return errors.New("player random return shadow")
	}
	if p.Active {
		p.Active = false
		p.Prompt = false
		p.Token = snap.Token
		p.Completed++
	}
	s.RandomReturned = true
	s.Events = append(s.Events, map[string]any{"event": "return", "mode": "random", "sequence": s.Sequence, "token": snap.Token})
	return nil
}

func (s *originalPlayerBattles) acceptsRead(ip uint16) bool {
	if s == nil {
		return false
	}
	return ip == 0x1900 && s.Mode == "random" && s.World.Active && !s.World.Committed || ip == 0x1cd8 && s.Mode == "guard" && s.Guard.RewardActive && !s.Guard.Committed
}
