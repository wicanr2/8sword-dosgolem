//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
)

func tfMust(e error) {
	if e != nil {
		panic(e)
	}
}
func tfRead(p string, v any) { b, e := os.ReadFile(p); tfMust(e); tfMust(pairStrictJSON(b, v)) }
func main() {
	input := flag.String("input", "", "input")
	candidate := flag.String("candidate", "", "passed candidate")
	out := flag.String("out", "", "new output")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	tfMust(os.Mkdir(*out, 0700))
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var before progressPairSnapshot
	var after checkpointSave
	tfRead(filepath.Join(*input, "army-catalog.json"), &c)
	tfRead(filepath.Join(*input, "combat-catalog.json"), &cc)
	tfRead(filepath.Join(*candidate, "gold/before-pair.json"), &before)
	tfRead(filepath.Join(*candidate, "gold/session/gamedata.ay.army.json"), &after)
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	tfMust(e)
	tfMust(writeTreasureAmount(base, 0, 0, 500))
	native, e := os.ReadFile(filepath.Join(*candidate, "gold/after-native.ay"))
	tfMust(e)
	award := treasureAward{0, 0, 1, 500}
	rows := []map[string]any{}
	for i, phase := range []string{"before-intent", "intent-durable", "native-durable", "world-durable"} {
		dir := filepath.Join(*out, fmt.Sprintf("fault-%d", i))
		tfMust(initializeProgressPair(dir, base, c, cc, before.World))
		s, b, e := openProgressPair(dir, c, cc)
		tfMust(e)
		s.Fault = func(p string) error {
			if p == phase {
				return errors.New("injected treasure interruption")
			}
			return nil
		}
		if _, e = s.CommitTreasure(b.Token, award, native, after.NativeFiles); e == nil {
			panic("fault not reached")
		}
		s.Close()
		s, got, e := openProgressPair(dir, c, cc)
		tfMust(e)
		gold := uint64(1000)
		amount := uint16(0)
		if i == 0 {
			gold = 500
			amount = 500
		}
		v, e := treasureAmount(got.Bytes.Native, 0, 0)
		tfMust(e)
		if got.World.Army.Gold != gold || v != amount {
			panic("partial treasure recovery")
		}
		again, e := s.Recover()
		tfMust(e)
		if got.Token != again.Token {
			panic("double treasure recovery")
		}
		if i != 0 {
			if _, e = s.CommitTreasure(got.Token, award, native, after.NativeFiles); e == nil {
				panic("claimed chest paid again")
			}
			current, e := s.readBytes()
			tfMust(e)
			if !bytes.Equal(current.Native, got.Bytes.Native) || !bytes.Equal(current.World, got.Bytes.World) {
				panic("refusal changed pair")
			}
		}
		s.Close()
		rows = append(rows, map[string]any{"phase": phase, "gold": gold, "amount": amount, "token": got.Token})
	}
	dir := filepath.Join(*out, "refusals")
	tfMust(initializeProgressPair(dir, base, c, cc, before.World))
	s, b, e := openProgressPair(dir, c, cc)
	tfMust(e)
	bad := 0
	for _, a := range []treasureAward{{0, 0, 1, 501}, {0, 0, 3, 500}, {8, 0, 1, 500}, {0, 10, 1, 500}} {
		if _, e = buildTreasurePair(b, c, cc, a, native, after.NativeFiles); e == nil {
			panic("bad treasure descriptor accepted")
		}
		bad++
	}
	for _, at := range []int{12, 36, 1350} {
		n := bytes.Clone(native)
		n[at] ^= 1
		if _, e = buildTreasurePair(b, c, cc, award, n, after.NativeFiles); e == nil {
			panic("foreign bytes accepted")
		}
		bad++
	}
	if _, e = s.CommitTreasure("stale-token", award, native, after.NativeFiles); e == nil {
		panic("stale treasure token accepted")
	}
	bad++
	s.Close()
	result := map[string]any{"status": "passed-treasure-faults", "faults": rows, "refusals": bad, "formal_changed": false}
	raw, e := json.MarshalIndent(result, "", "  ")
	tfMust(e)
	tfMust(os.WriteFile(filepath.Join(*out, "receipt.json"), append(raw, '\n'), 0600))
}
