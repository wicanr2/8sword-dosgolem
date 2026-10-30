//go:build ignore

// 030 DRAFT: separate-process initialization, deliberate crash and cold recovery.
package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
)

func pairedMust(e error) {
	if e != nil {
		panic(e)
	}
}
func main() {
	input := flag.String("input", "", "fixed input directory")
	dir := flag.String("dir", "", "paired save directory")
	mode := flag.String("mode", "read", "init|commit|read|busy")
	stop := flag.String("stop", "", "deliberate exit checkpoint")
	world := flag.String("world", "before-world.json", "world fixture for init/commit")
	out := flag.String("out", "", "new receipt path")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {*world, &w}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		pairedMust(e)
		pairedMust(pairStrictJSON(b, v.Dst))
	}
	if *mode == "init" {
		b, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
		pairedMust(e)
		pairedMust(initializeProgressPair(*dir, b, c, cc, w))
		return
	}
	s, snap, e := openProgressPair(*dir, c, cc)
	if *mode == "busy" {
		if e == nil {
			s.Close()
			panic("second process opened active pair")
		}
		if !errors.Is(e, errPairBusy) {
			panic(e)
		}
		fmt.Println("paired reader refused while writer owns lock")
		return
	}
	pairedMust(e)
	defer s.Close()
	if *mode == "commit" {
		s.Fault = func(phase string) error {
			if phase == *stop {
				os.Exit(91)
			}
			return nil
		}
		snap, e = s.Commit(snap.Token, w)
		pairedMust(e)
	} else if *mode != "read" {
		panic("bad mode")
	}
	if engine, e := game.Open(game.Options{Root: "/unmounted-original", Saves: *dir, HD: true}); engine != nil || !errors.Is(e, game.ErrOwnedArmyHandoffPending) {
		panic(fmt.Sprint("missing engine guard: ", e))
	}
	if *out != "" {
		raw, e := json.MarshalIndent(map[string]any{"status": "passed-paired-progress-process", "snapshot": snap, "journal_present": false, "engine_guard": true}, "", "  ")
		pairedMust(e)
		f, e := os.OpenFile(*out, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		pairedMust(e)
		_, e = f.Write(append(raw, '\n'))
		pairedMust(e)
		pairedMust(f.Close())
	}
}
