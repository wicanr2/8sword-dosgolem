package ownedworld

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

func TestNativeImport(t *testing.T) {
	work := os.Getenv("EIGHTSWORD_IMPORT_WORK")
	if work == "" {
		t.Skip("set EIGHTSWORD_IMPORT_WORK for real-data import checks")
	}
	root, input := os.Getenv("EIGHTSWORD_IMPORT_ROOT"), filepath.Join(work, "inputs")
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, item := range []struct {
		name string
		dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		raw, err := os.ReadFile(filepath.Join(input, item.name))
		must(err)
		must(pairStrictJSON(raw, item.dst))
	}
	before, err := os.ReadFile(filepath.Join(root, "GAMEDATA.AY"))
	must(err)
	out := filepath.Join(work, "import-tests")
	must(os.Mkdir(out, 0700))
	target := filepath.Join(out, "accepted")
	must(importNativeProgress(root, root, target, input, c, cc))
	native, err := os.ReadFile(filepath.Join(target, "gamedata.ay"))
	must(err)
	if !bytes.Equal(native, before) {
		t.Fatal("import changed original bytes")
	}
	saved, err := os.ReadFile(filepath.Join(target, "gamedata.ay.army.json"))
	must(err)
	pair, err := decodeProgressPair(progressPairBytes{native, saved}, c, cc)
	must(err)
	if pair.World.Army.Rules != "native" || pair.World.Army.Slots[0] != (ArmyStack{"native:01", 30}) ||
		pair.World.Army.Gold != 500 || pair.World.Army.Leadership != 100 || pair.World.Progress.Merit != 0 || len(pair.World.Army.Offers) != 0 {
		t.Fatal("import granted or dropped gameplay state")
	}
	if pair.World.Progress.Thresholds != [6]uint64{0, 2000, 5000, 8000, 12000, 30000} {
		t.Fatal("source thresholds")
	}
	if err = importNativeProgress(root, root, target, input, c, cc); err == nil {
		t.Fatal("overwrote target")
	}
	again, err := os.ReadFile(filepath.Join(target, "gamedata.ay.army.json"))
	must(err)
	if !bytes.Equal(saved, again) {
		t.Fatal("refusal changed target")
	}
	if armyReviewTitle != "神州八劍・軍隊試作・增援營地" {
		t.Fatal("factory initialization order")
	}
	refusals := []string{"existing-target"}
	setWord := func(b []byte, at int, n uint16) { binary.LittleEndian.PutUint16(b[at:], n+uint16(at+3)) }
	for _, item := range []struct {
		name string
		edit func([]byte)
	}{
		{"unknown-kind", func(b []byte) { setWord(b, 12, 26) }},
		{"empty-count", func(b []byte) { setWord(b, 14, 0) }},
		{"duplicate", func(b []byte) { setWord(b, 16, 1); setWord(b, 18, 1) }},
		{"over-leadership", func(b []byte) { setWord(b, 8, 1) }},
		{"bad-rank", func(b []byte) { setWord(b, 0, 0) }},
	} {
		source := filepath.Join(out, item.name)
		must(os.Mkdir(source, 0700))
		b := bytes.Clone(before)
		item.edit(b)
		must(os.WriteFile(filepath.Join(source, "gamedata.ay"), b, 0600))
		dest := filepath.Join(out, item.name+"-result")
		if err = importNativeProgress(root, source, dest, input, c, cc); err == nil {
			t.Fatal("accepted", item.name)
		}
		if _, err = os.Lstat(dest); !os.IsNotExist(err) {
			t.Fatal("published refused input", item.name)
		}
		refusals = append(refusals, item.name)
	}
	for _, name := range []string{"case-ambiguous", "sidecar", "symlink", "bad-map"} {
		source := filepath.Join(out, name)
		must(os.Mkdir(source, 0700))
		must(os.WriteFile(filepath.Join(source, "gamedata.ay"), before, 0600))
		switch name {
		case "case-ambiguous":
			must(os.WriteFile(filepath.Join(source, "GAMEDATA.AY"), before, 0600))
		case "sidecar":
			must(os.WriteFile(filepath.Join(source, "GAMEDATA.AY.ARMY.JSON"), []byte("{}"), 0600))
		case "symlink":
			must(os.Remove(filepath.Join(source, "gamedata.ay")))
			must(os.Symlink(filepath.Join(root, "GAMEDATA.AY"), filepath.Join(source, "gamedata.ay")))
		case "bad-map":
			must(os.WriteFile(filepath.Join(source, "map01.ay"), []byte("bad"), 0600))
		}
		dest := filepath.Join(out, name+"-result")
		if err = importNativeProgress(root, source, dest, input, c, cc); err == nil {
			t.Fatal("accepted", name)
		}
		if _, err = os.Lstat(dest); !os.IsNotExist(err) {
			t.Fatal("published refused input", name)
		}
		refusals = append(refusals, name)
	}
	source := filepath.Join(out, "map-overlay")
	must(os.Mkdir(source, 0700))
	must(os.WriteFile(filepath.Join(source, "gamedata.ay"), before, 0600))
	b, err := os.ReadFile(filepath.Join(root, "MAP01.AY"))
	must(err)
	b = bytes.Clone(b)
	b[0] ^= 1
	must(os.WriteFile(filepath.Join(source, "MaP01.Ay"), b, 0600))
	must(importNativeProgress(root, source, filepath.Join(out, "overlay-result"), input, c, cc))
	raw, err := os.ReadFile(filepath.Join(out, "overlay-result/gamedata.ay.army.json"))
	must(err)
	maps, err := decodeCheckpointMaps(raw)
	must(err)
	if !bytes.Equal(maps["map01.ay"], b) {
		t.Fatal("ignored saved map")
	}
	raw, err = json.MarshalIndent(map[string]any{"status": "passed-native-import", "refusals": refusals, "accepted": pair, "native_sha256": nativeSHA(before), "saved_map_preferred": true}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(work, "import-test-r1.json"), append(raw, '\n'), 0600))
}
