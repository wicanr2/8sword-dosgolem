//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"reflect"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func checkpointMust(e error) {
	if e != nil {
		panic(e)
	}
}
func checkpointWrite(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	checkpointMust(e)
	checkpointMust(os.WriteFile(p, append(b, '\n'), 0600))
}
func checkpointInputs(input string) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld, []byte) {
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		N string
		V any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &w}} {
		b, e := os.ReadFile(filepath.Join(input, v.N))
		checkpointMust(e)
		checkpointMust(pairStrictJSON(b, v.V))
	}
	b, e := os.ReadFile(filepath.Join(input, "original-save.ay"))
	checkpointMust(e)
	return c, cc, w, b
}
func main() {
	root := flag.String("root", "", "read-only original")
	assets := flag.String("assets", "", "HD assets")
	input := flag.String("input", "", "fixed input")
	out := flag.String("out", "", "new output")
	session := flag.String("session", "", "paired directory")
	mode := flag.String("mode", "probe", "init/read/probe")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	c, cc, w, base := checkpointInputs(*input)
	if *mode == "init" {
		checkpointMust(initializeProgressPair(*session, base, c, cc, w))
		return
	}
	if *mode == "read" {
		s, snap, e := openProgressPair(*session, c, cc)
		checkpointMust(e)
		defer s.Close()
		checkpointWrite(*out, snap)
		return
	}
	checkpointMust(os.Mkdir(*out, 0700))
	dir := filepath.Join(*out, "session")
	checkpointMust(initializeProgressPair(dir, base, c, cc, w))
	store, snap, e := openProgressPair(dir, c, cc)
	checkpointMust(e)
	scratch := filepath.Join(*out, "scratch")
	checkpointMust(materializeNativeCheckpoint(*root, *input, scratch, snap))
	engine, e := game.Open(game.Options{Root: *root, Assets: *assets, Saves: scratch, HD: true})
	checkpointMust(e)
	defer func() {
		if engine != nil {
			engine.Close()
		}
		if store != nil {
			store.Close()
		}
	}()
	setup := func() { engine.Oracle.SetClock(12, 0, 0, 0); engine.EnableLiveClock(3000) }
	setup()
	advance := func(ms int) {
		for n := 0; n < ms; n += 10 {
			checkpointMust(catchWorldArmyFault(func() error { return engine.AdvanceCycles(30000) }))
			engine.RenderAudio()
			if n%100 == 0 {
				engine.Frame()
			}
		}
	}
	press := func(k byte) {
		checkpointMust(engine.Key(k, true))
		advance(100)
		checkpointMust(engine.Key(k, false))
		advance(200)
	}
	boot := func() {
		advance(200)
		press(2)
		press(2)
		advance(500)
		if !engine.PAMLoaded {
			press(1)
		}
		for n := 0; n < 300 && engine.Tracker.VisibleScene != "main-menu"; n++ {
			advance(100)
		}
		if engine.Tracker.VisibleScene != "main-menu" {
			panic("main menu")
		}
		press(0x1c)
		advance(2000)
		if engine.Tracker.VisibleScene != "map" {
			panic("continued map")
		}
	}
	capture := func(name string) {
		checkpointMust(engine.Oracle.SaveStateFile(filepath.Join(*out, name+".state")))
		f, e := os.Create(filepath.Join(*out, name+".png"))
		checkpointMust(e)
		checkpointMust(png.Encode(f, engine.Frame()))
		checkpointMust(f.Close())
	}
	boot()
	port, e := installWorldArmyPort(engine, store, snap)
	checkpointMust(e)
	cp, e := installNativeCheckpoint(engine, port, scratch)
	checkpointMust(e)
	initial := checkpointLocation(engine.Oracle)
	army := bytes.Clone(engine.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))
	capture("initial")
	press(0x50)
	press(0x50)
	advance(500)
	moved := checkpointLocation(engine.Oracle)
	if reflect.DeepEqual(initial["raw_words"], moved["raw_words"]) {
		panic("movement did not change native location")
	}
	// Diagnostic map progress, explicitly allowed by the user: copy one existing
	// source tile value into a distant cell. No position, RNG or unit data changes.
	mapBefore := bytes.Clone(engine.Oracle.Bytes(oracle.Far(0x9c00, 0), 5761))
	target := 4000
	source := -1
	for i := 100; i < 5600; i++ {
		if mapBefore[i] != mapBefore[target] && mapBefore[i] != 100 {
			source = i
			break
		}
	}
	if source < 0 {
		panic("no source tile marker")
	}
	engine.Oracle.WriteU8(oracle.Far(0x9c00, uint16(target)), mapBefore[source])
	patched := bytes.Clone(engine.Oracle.Bytes(oracle.Far(0x9c00, 0), 5761))
	checkpointMust(os.WriteFile(filepath.Join(*out, "map-before-patch.bin"), mapBefore, 0600))
	checkpointMust(os.WriteFile(filepath.Join(*out, "map-before-save.bin"), patched, 0600))
	press(0x41)
	advance(500)
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(1000)
	if cp.Saves != 1 {
		panic(fmt.Sprintf("F7 checkpoints %d", cp.Saves))
	}
	saved := port.Current
	location := checkpointLocation(engine.Oracle)
	savedMap := bytes.Clone(engine.Oracle.Bytes(oracle.Far(0x9c00, 0), 5761))
	savedBuffer := bytes.Clone(engine.Oracle.Bytes(oracle.Far(0x9e00, 0), 2987))
	checkpointWrite(filepath.Join(*out, "saved.json"), map[string]any{"snapshot": saved, "location": location, "events": cp.Events})
	checkpointMust(os.WriteFile(filepath.Join(*out, "native-saved.ay"), saved.Bytes.Native, 0600))
	checkpointMust(os.WriteFile(filepath.Join(*out, "saved-map.bin"), savedMap, 0600))
	capture("saved")
	engine.Close()
	engine = nil
	store.Close()
	store = nil
	store, cold, e := openProgressPair(dir, c, cc)
	checkpointMust(e)
	coldScratch := filepath.Join(*out, "cold-scratch")
	checkpointMust(materializeNativeCheckpoint(*root, *input, coldScratch, cold))
	engine, e = game.Open(game.Options{Root: *root, Assets: *assets, Saves: coldScratch, HD: true})
	checkpointMust(e)
	setup()
	boot()
	coldLocation := checkpointLocation(engine.Oracle)
	coldMap := engine.Oracle.Bytes(oracle.Far(0x9c00, 0), 5761)
	if !reflect.DeepEqual(location, coldLocation) {
		checkpointWrite(filepath.Join(*out, "location-mismatch.json"), map[string]any{"saved": location, "cold": coldLocation})
		panic("cold native location")
	}
	if !bytes.Equal(savedMap, coldMap) || !bytes.Equal(savedBuffer, engine.Oracle.Bytes(oracle.Far(0x9e00, 0), 2987)) || !bytes.Equal(saved.Bytes.Native, cold.Bytes.Native) {
		panic("cold map/progress bytes")
	}
	if !bytes.Equal(army, engine.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		panic("native army changed")
	}
	capture("cold")
	checkpointWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-native-checkpoint-cold-engine", "initial_location": initial, "moved_location": moved, "saved_location": location, "cold_location": coldLocation, "saved_map_sha256": nativeSHA(savedMap), "cold_map_sha256": nativeSHA(coldMap), "saved_native_sha256": saved.NativeSHA, "world_cold_equal": worldDigest(saved.World) == worldDigest(cold.World), "native_army_unchanged": true, "world": cold.World, "controlled_map_write": map[string]any{"target": target, "source": source, "before": mapBefore[target], "after": mapBefore[source]}, "file_events": cp.Events, "snapshot_loaded": false, "test_seed_set": false, "format_promoted": false})
}
