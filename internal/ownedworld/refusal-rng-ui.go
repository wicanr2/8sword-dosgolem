package ownedworld

import (
	"errors"
	"flag"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

var refusalTestSeed = flag.Uint64("refusal-seed", 0, "明示測試seed，僅在seed-set啟用")
var refusalSeedSet = flag.Bool("seed-set", false, "明示在受控快照設定RNG狀態")
var currentRefusal *refusalGate
var refusalReturned bool

func injectRefusalSeed(m *dg.Machine) error {
	if !*refusalSeedSet {
		return nil
	}
	if *refusalTestSeed > 0xffffffff {
		return errors.New("seed range")
	}
	m.Write16(0x26a3c, uint16(*refusalTestSeed))
	m.Write16(0x26a3e, uint16(*refusalTestSeed>>16))
	return nil
}
func installRefusalUI(x *encounterExtra) {
	o := x.Engine.Oracle
	g := &refusalGate{Code: x.Bridge.Code}
	g.Guard = func(m *dg.Machine) error {
		g.BP = x.Presence.BP
		g.SP = x.Presence.SP
		_, e := x.Presence.machineCheck(m, 0x173a)
		return e
	}
	g.Decision = func(p originalRandPlan, pursued bool) {
		if pursued {
			x.Confirmed = true
			runtimeEnemyCurrent.Modifier = 1
		}
		x.Events = append(x.Events, map[string]any{"command": "refusal", "rng": p, "pursued": pursued})
	}
	// Bind the original frame immediately before the host gate is checked.
	swordOnHostInstruction(o, oracle.Far(0x110, 0x173a), func(m *dg.Machine) (bool, error) {
		g.BP = x.Presence.BP
		g.SP = x.Presence.SP
		if *refusalSeedSet && !g.Applied {
			if e := g.Guard(m); e != nil {
				return false, e
			}
			if e := checkOriginalRand(o, g.Code); e != nil {
				return false, e
			}
			if e := saveEncounterState(o, "before-seed.state"); e != nil {
				return false, e
			}
			if e := injectRefusalSeed(m); e != nil {
				return false, e
			}
			if e := saveEncounterState(o, "after-seed.state"); e != nil {
				return false, e
			}
		}
		done, e := g.execute(m)
		if e == nil {
			e = saveEncounterState(o, "decision.state")
		}
		return done, e
	})
	swordOnCall(o, oracle.Far(0x110, 0xbd3), func(o *oracle.Oracle) {
		if !g.Applied || g.Pursued || refusalReturned {
			return
		}
		s, e := x.Port.snapshot()
		if e != nil || s.Token != x.Presence.Token || s.World.Battle != nil {
			panic(&worldArmyPortFault{"refusal return binding"})
		}
		for i, n := range pairWorldResources(s.World).words() {
			if uint64(o.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
				panic(&worldArmyPortFault{"refusal return resources"})
			}
		}
		x.Presence.Active = false
		x.Presence.Prompt = false
		x.Presence.Completed++
		x.Finished = true
		refusalReturned = true
		x.Events = append(x.Events, map[string]any{"command": "refusal-return", "ip": o.Regs().IP, "world": s.World})
	})
	currentRefusal = g
}
func refusalState(v map[string]any) {
	if g := currentRefusal; g != nil {
		v["refusal_applied"], v["refusal_pursued"], v["refusal_rng"], v["refusal_returned"] = g.Applied, g.Pursued, g.Plan, refusalReturned
	}
	v["retreat_rng"] = lastRetreatRand
	if runtimeEnemyCurrent != nil {
		v["pursuit_modifier"] = runtimeEnemyCurrent.Modifier
	}
}
func pursuitOpening(x *encounterExtra) error {
	if runtimeEnemyCurrent.Modifier != 1 {
		return nil
	}
	// Reuse the admitted ordinary/ranged Go phase. Unimplemented rear special
	// actions remain outside this candidate; no native unit-table fallback.
	for n := 0; n < 6; n++ {
		state, _ := x.UI.state()
		if state.Result != "" {
			break
		}
		p, e := x.UI.enemyPlan()
		if e != nil {
			break
		}
		if e = x.UI.apply(p); e != nil {
			return e
		}
	}
	x.Events = append(x.Events, map[string]any{"command": "pursuit-opening", "world": x.UI.World})
	return nil
}
