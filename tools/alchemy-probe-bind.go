//go:build ignore

package main

import (
	"bytes"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
)

type alchemyProbeBinding struct {
	Port           *alchemyPort
	FaultRecovered bool
	RepeatRejected bool
}

func (p *alchemyProbeBinding) Report() map[string]any {
	return map[string]any{"amount": p.Port.Amount, "award": p.Port.Award, "casts": p.Port.Casts, "fault_intent_durable": p.FaultRecovered, "repeat_rejected": p.RepeatRejected}
}
func (p *alchemyProbeBinding) Finish(root, input, scratch string) error {
	v := p.Port
	if e := v.Complete(root, input, scratch, ""); e != nil {
		return e
	}
	if v.Complete(root, input, scratch, "") == nil {
		return errors.New("duplicate completion accepted")
	}
	current := v.Army.Current
	var envelope checkpointSave
	if e := pairStrictJSON(current.Bytes.World, &envelope); e != nil {
		return e
	}
	if _, e := v.Army.Store.CommitAlchemy(current.Token, v.Award, current.Bytes.Native, envelope.NativeFiles); e == nil {
		return errors.New("old cast replay accepted")
	}
	b, e := v.Army.Store.readBytes()
	if e != nil {
		return e
	}
	if !bytes.Equal(b.Native, current.Bytes.Native) || !bytes.Equal(b.World, current.Bytes.World) {
		return errors.New("refusal changed pair")
	}
	p.RepeatRejected = true
	if !v.Award.Bonus {
		dir := v.Army.Store.Dir + "-fault"
		if e = os.Mkdir(dir, 0700); e != nil {
			return e
		}
		if e = os.WriteFile(filepath.Join(dir, "gamedata.ay"), v.Before.Bytes.Native, 0600); e != nil {
			return e
		}
		if e = os.WriteFile(filepath.Join(dir, "gamedata.ay.army.json"), v.Before.Bytes.World, 0600); e != nil {
			return e
		}
		s, start, e := openProgressPair(dir, v.Army.Store.Catalog, v.Army.Store.Combat)
		if e != nil {
			return e
		}
		s.Fault = func(phase string) error {
			if phase == "intent-durable" {
				return errors.New("injected alchemy interruption")
			}
			return nil
		}
		_, e = s.CommitAlchemy(start.Token, v.Award, current.Bytes.Native, envelope.NativeFiles)
		if e == nil {
			s.Close()
			return errors.New("fault missing")
		}
		s.Close()
		s, got, e := openProgressPair(dir, v.Army.Store.Catalog, v.Army.Store.Combat)
		if e != nil {
			return e
		}
		defer s.Close()
		again, e := s.Recover()
		if e != nil {
			return e
		}
		if got.Token != current.Token || again.Token != got.Token {
			return errors.New("partial/repeated alchemy recovery")
		}
		p.FaultRecovered = true
	}
	return nil
}
func init() {
	alchemyProbeYield = errAlchemyYield
	alchemyProbeInstall = func(e *game.Engine, p *worldArmyPort) (alchemyProbeSession, error) {
		v, x := installAlchemyPort(e, p)
		return &alchemyProbeBinding{Port: v}, x
	}
}
