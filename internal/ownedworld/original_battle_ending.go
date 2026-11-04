package ownedworld

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"

	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

// A cleared final record is a replay receipt. Its opaque native checkpoint
// deliberately retains the prebattle roster and the original confirmation UI.
func originalEndingRecord(p progressPairSnapshot, rec WorldEncounter) error {
	flags, err := savedSwords(p.Bytes.Native)
	if err != nil {
		return err
	}
	// Boss records can own swords earned since the last opaque F7 checkpoint.
	for region, index := range swordBossIndex {
		if boss, ok := p.World.Encounters[fmt.Sprintf("guarded:%02d:%02d", region, index)]; ok && boss.Cleared {
			flags[region] = true
		}
	}
	for _, v := range flags {
		if !v {
			return errors.New("ending record without eight swords")
		}
	}
	if rec.Cleared {
		rows, err := originalEndingCheckpoint(p.Bytes.Native)
		if err != nil {
			return err
		}
		if rows != rec.Enemy {
			return errors.New("ending replay checkpoint roster")
		}
	}
	return nil
}

func originalEndingCheckpoint(native []byte) ([6]ArmyStack, error) {
	var rows [6]ArmyStack
	empty, alive := false, false
	for i := range rows {
		kind, err := guardSavedWord(native, guardNPCAt(0, 4)+i*4)
		if err != nil {
			return rows, err
		}
		count, err := guardSavedWord(native, guardNPCAt(0, 4)+i*4+2)
		if err != nil {
			return rows, err
		}
		if kind == 0 && count == 0 {
			empty = true
			continue
		}
		if empty || kind < 1 || kind > 25 || count == 0 || count > 32767 {
			return rows, errors.New("ending checkpoint row bounds/packing")
		}
		rows[i] = ArmyStack{fmt.Sprintf("native:%02d", kind), uint32(count)}
		alive = true
	}
	if !alive {
		return rows, errors.New("ending checkpoint has no living guard")
	}
	return rows, nil
}

func (g *originalBattleGuard) final() bool {
	return g.Ending && g.Guard != nil && g.Guard.key() == "guarded:00:04"
}

func (g *originalBattleGuard) replay(m *dg.Machine) (bool, error) {
	if !g.final() || !g.Committed || g.Captured || !g.Replay {
		return false, errors.New("ending replay phase")
	}
	rec, ok := g.Before.World.Encounters[g.Guard.key()]
	if !ok || !rec.Cleared || rec.Enemy != g.Guard.Rows {
		return false, errors.New("ending replay receipt")
	}
	if err := originalEndingRecord(g.Before, rec); err != nil {
		return false, err
	}
	offset := guardNPCAt(0, 4) - 0x365e
	clear(g.NPC[offset : offset+24])
	clear(m.Mem[0x1e880+0x36be : 0x1e880+0x36d6])
	m.Write16(0x1e880+uint32(m.CPU.R[dg.BP])-14, 0)
	g.Captured = true
	m.CPU.IP = 0x326e
	m.CPU.Cycles++
	g.Events = append(g.Events, map[string]any{"event": "ending-replay", "token": g.Before.Token})
	return true, nil
}

func (g *originalBattleGuard) endingPrepare(m *dg.Machine) (bool, error) {
	if err := g.frame(m, 0x329b); err != nil {
		return false, err
	}
	if !g.final() || !g.Captured || g.RewardActive || g.Monthly || g.Power || g.Sword || m.Read16(0x1e880+0x56e2) != 1 {
		return false, errors.New("ending handoff result/awards")
	}
	for i := 0; i < 8; i++ {
		if binary.LittleEndian.Uint16(g.Flags[i*2:]) != 1 {
			return false, errors.New("ending handoff swords")
		}
	}
	if !bytes.Equal(g.NPC[96:120], make([]byte, 24)) || g.Enemy != [6]ArmyStack{} {
		return false, errors.New("ending handoff enemy alive")
	}
	if g.Replay {
		if !g.Committed || g.Projection.Phase != "" || g.Rounds.Active {
			return false, errors.New("ending replay entered battle")
		}
	} else if !g.Rounds.Done || !g.Rounds.Released || g.Rounds.Result != "win" || g.Projection.Result != 0 || g.Projection.Captures != 1 || m.CPU.R[dg.SP] != g.Projection.EntrySP+4 {
		return false, errors.New("ending handoff battle phase")
	}
	if !g.Committed {
		if _, err := g.commitWorld(); err != nil {
			return false, err
		}
	}
	s, err := g.Port.snapshot()
	if err != nil {
		return false, err
	}
	if s.Token != g.CommittedToken || !s.World.Encounters[g.Guard.key()].Cleared || s.World.Army.Slots != g.Projection.Input && g.Replay || s.World.Army.Slots != g.Projection.Remaining && !g.Replay {
		return false, errors.New("ending handoff durable receipt")
	}
	g.EndingSP = m.CPU.R[dg.SP]
	g.EndingPrepared = true
	return false, nil // Original push CS/call sub_1020E builds the far frame.
}

func (g *originalBattleGuard) endingHandoff(m *dg.Machine) (bool, error) {
	if err := g.source(m, 0x020e); err != nil {
		return false, err
	}
	if err := g.data(m); err != nil {
		return false, err
	}
	if !g.final() || !g.EndingPrepared || !g.Committed || m.CPU.R[dg.SP] != g.EndingSP-4 || m.CPU.R[dg.BP] != g.EntrySP-2 || m.Read16(0x1e880+uint32(m.CPU.R[dg.SP])) != 0x329f || m.Read16(0x1e880+uint32(m.CPU.R[dg.SP])+2) != 0x110 || m.Read16(0x1e880+0x56e2) != 1 || !bytes.Equal(g.Code[0x20e:0x22e], m.Mem[0x130e:0x132e]) {
		return false, errors.New("ending playback frame/source")
	}
	g.EndingHandoff = true
	g.Events = append(g.Events, map[string]any{"event": "ending-handoff", "token": g.Port.Current.Token, "replay": g.Replay})
	swordGameplayEnded = true
	return false, nil
}

func installOriginalEndingHooks(g *originalBattleGuard) {
	swordOnHostInstruction(g.Engine.Oracle, oracle.Far(0x110, 0x329b), g.endingPrepare)
	swordOnHostInstruction(g.Engine.Oracle, oracle.Far(0x110, 0x020e), g.endingHandoff)
}
