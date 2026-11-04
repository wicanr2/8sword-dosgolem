package ownedworld

import (
	"errors"
	"fmt"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func TestOriginalBattleArtWorld(t *testing.T) {
	work, root, combat := setupInputs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("assets")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var catalog ArmyCatalog
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	must(err)
	must(pairStrictJSON(raw, &catalog))
	parent := filepath.Join(work, "art-world-r1", os.Getenv("EIGHTSWORD_ART_UNITS"), os.Getenv("EIGHTSWORD_ART_MODE"))
	must(os.MkdirAll(parent, 0700))
	name := os.Getenv("EIGHTSWORD_SESSION_CASE")
	if name == "" {
		name = "hd-native-go"
	}
	native := name == "hd-native-control"
	mixed := os.Getenv("EIGHTSWORD_ART_UNITS") != "native"
	dir := filepath.Join(parent, name)
	must(os.Mkdir(dir, 0700))
	session := filepath.Join(dir, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), catalog, combat))
	store, snap, err := openProgressPair(session, catalog, combat)
	must(err)
	defer store.Close()
	player := [6]ArmyStack{{"native:01", 1000}, {"native:03", 200}}
	if mixed {
		player[2] = ArmyStack{"openkb:wolf", 20}
		player[3] = ArmyStack{"openkb:arcr", 20}
	}
	if os.Getenv("EIGHTSWORD_ART_UNITS") == "fragile" {
		player = [6]ArmyStack{{"openkb:wolf", 1}, {"native:01", 1000}, {"native:03", 200}, {"openkb:arcr", 20}}
	}
	w := snap.World
	w.Revision++
	w.Army.Slots = player
	w.Army.Leadership = 30000
	w.Progress.Merit = 10000
	if mixed {
		w.Army.Rules = "formation"
	}
	snap, err = store.Commit(snap.Token, w)
	must(err)
	port := &worldArmyPort{Store: store, Current: snap}
	must(materializeNativeCheckpoint(root, filepath.Join(work, "inputs"), filepath.Join(dir, "scratch"), snap))
	e := setupCold(t, root, assets, dir, true)
	defer e.Close()
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e12), 6)
	e.Oracle.WriteU16(oracle.Far(0x1e88, 0x8e44), 4)
	var owner *originalBattleGuard
	var lifecycle *originalBattleSession
	var checkpoint *nativeCheckpointPort
	if !native {
		owner, _ = originalGuardControllers(t, e, port, player)
		lifecycle, err = installOriginalBattleSession(owner)
		must(err)
		checkpoint, err = installNativeCheckpoint(e, port, filepath.Join(dir, "scratch"))
		must(err)
	} else {
		injected := false
		e.Oracle.OnCall(oracle.Far(0x110, 0x32e0), func(o *oracle.Oracle) {
			if injected {
				return
			}
			injected = true
			for i, row := range player {
				p := combat.Profiles[row.Unit]
				o.WriteU16(oracle.Far(0x1e88, 0x54a+uint16(i*4)), p.NativeKind)
				o.WriteU16(oracle.Far(0x1e88, 0x54c+uint16(i*4)), uint16(row.Count))
			}
		})
	}

	var art *originalBattleArt
	if os.Getenv("EIGHTSWORD_ART_MODE") == "on" {
		art, err = installOriginalBattleArt(owner, filepath.Join(work, "ui-assets"))
		must(err)
	}
	captures := []map[string]any{}
	seen := map[string]bool{}
	e.Oracle.OnCall(oracle.Far(0xf67, 0x283e), func(o *oracle.Oracle) {
		state := owner.Rounds.Actions.rows()
		key := fmt.Sprint(state[0])
		if seen[key] {
			return
		}
		seen[key] = true
		n := len(captures)
		file := fmt.Sprintf("battle-%03d.png", n)
		endingFrame(t, e, filepath.Join(dir, file))
		captures = append(captures, map[string]any{"file": file, "rows": state, "slots": owner.Rounds.Actions.slots(), "coordinates_hex": fmt.Sprintf("%x", o.Bytes(oracle.Far(0x1e88, 0x703c), 12)), "step": o.Steps(), "art": e.OwnedBattleArtStatus()})
	})
	defer func() {
		events := []map[string]any{}
		if art != nil {
			events = art.Events
		}
		setupWrite(t, filepath.Join(dir, "art.json"), map[string]any{"captures": captures, "events": events, "status": e.OwnedBattleArtStatus(), "mode": os.Getenv("EIGHTSWORD_ART_MODE"), "units": os.Getenv("EIGHTSWORD_ART_UNITS")})
	}()
	rows := []map[string]any{}
	for i, phase := range []string{"cancel", "retreat", "win"} {
		if i > 0 {
			setupPress(t, e, 0x4d)
		}
		before, er := store.Recover()
		must(er)
		err = originalGuardRun(t, e, phase == "retreat", owner, 300000000, phase == "cancel")
		if !errors.Is(err, errOriginalGuardMapHeld) {
			must(e.Oracle.SaveStateFile(filepath.Join(dir, phase+"-failed.state")))
			d := map[string]any{"error": fmt.Sprint(err), "regs": e.Oracle.Regs()}
			if owner != nil {
				d["events"] = owner.Events
				d["rounds"] = owner.Rounds.Rows
				d["session"] = lifecycle.Last
			}
			setupWrite(t, filepath.Join(dir, phase+"-failed.json"), d)
			t.Fatal("session", phase, err)
		}
		e.ReleaseAll()
		setupAdvance(t, e, 500)
		endingFrame(t, e, filepath.Join(dir, phase+".png"))
		resources := [6]uint16{}
		for i := range resources {
			resources[i] = e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))
		}
		saved, er := store.Recover()
		must(er)
		row := map[string]any{"phase": phase, "resources": resources, "NPC_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x365e), 1008)), "swords_hex": fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x275a), 16)), "seed": originalSeed(e.Oracle), "frame_rgba_sha256": contentSHA(e.Frame().Pix)}
		if !native {
			if lifecycle.Returns != uint64(i+1) || lifecycle.Cancels != 1 || lifecycle.Last.Cancelled != (phase == "cancel") {
				t.Fatal("session counter", lifecycle.Last)
			}
			if phase == "cancel" && saved.Token != before.Token {
				t.Fatal("cancel committed")
			}
			if phase != "cancel" && saved.World.Revision != before.World.Revision+1 {
				t.Fatal("battle commit count")
			}
			row["outcome"] = lifecycle.Last
			row["events"] = owner.Events
			row["actions"] = len(owner.Rounds.History)
			row["world_sha256"] = worldDigest(saved.World)
		} else {
			row["native_army_hex"] = fmt.Sprintf("%x", e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))
		}
		rows = append(rows, row)
		must(e.Oracle.SaveStateFile(filepath.Join(dir, phase+".state")))
	}
	if !native {
		// Revisit the cleared map tile through its original empty-guard message.
		beforeVisit, er := store.Recover()
		must(er)
		setupPress(t, e, 0x4d)
		err = originalGuardRun(t, e, false, owner, 30000000, true)
		if !errors.Is(err, errOriginalGuardMapHeld) {
			t.Fatal("cleared visit", err)
		}
		e.ReleaseAll()
		setupAdvance(t, e, 500)
		afterVisit, er := store.Recover()
		must(er)
		if lifecycle.Returns != 4 || lifecycle.Visits != 1 || lifecycle.Cancels != 1 || !lifecycle.Last.ClearedVisit || afterVisit.Token != beforeVisit.Token || len(owner.Rounds.History) != 0 {
			t.Fatal("cleared guard reopened")
		}
		setupPress(t, e, 0x41)
		setupPress(t, e, 0x1c)
		setupPress(t, e, 0x1c)
		setupAdvance(t, e, 700)
		e.ReleaseAll()
		if checkpoint.Saves != 1 {
			t.Fatal("session F7", checkpoint.Saves)
		}
		saved, er := store.Recover()
		must(er)
		setupWrite(t, filepath.Join(dir, "saved.json"), map[string]any{"world_sha256": worldDigest(saved.World), "token": saved.Token, "saves": checkpoint.Saves, "army": saved.World.Army.Slots, "resources": pairWorldResources(saved.World), "location": checkpointLocation(e.Oracle), "cleared_revisit_no_battle": true})
	}
	setupWrite(t, filepath.Join(dir, "receipt.json"), map[string]any{"case": name, "phases": rows, "player": player, "controlled_position": [2]uint16{6, 4}, "same_engine": true, "native_guard_unmodified": true, "actual_window": false})
}

func TestOriginalBattleArtTiles(t *testing.T) {
	work, _, _ := setupInputs(t)
	raw, err := os.ReadFile(filepath.Join(work, "inputs/army-catalog.json"))
	if err != nil {
		t.Fatal(err)
	}
	pack := loadHDUnitArtwork(nil, filepath.Join(work, "ui-assets"), contentSHA(raw))
	if len(pack.Failures) != 0 {
		t.Fatal(pack.Failures)
	}
	tiles := []map[string]any{}
	dir := filepath.Join(work, "art-tiles")
	if err = os.Mkdir(dir, 0700); err != nil {
		t.Fatal(err)
	}
	for _, id := range openKBArtIDs {
		im, err := originalBattleArtTile(pack.Images[id])
		if err != nil {
			t.Fatal(err)
		}
		zero, opaque := 0, 0
		for at := 0; at < len(im.Pix); at += 4 {
			if im.Pix[at+3] == 0 {
				zero++
			}
			if im.Pix[at+3] == 255 {
				opaque++
			}
		}
		if zero == 0 || opaque == 0 {
			t.Fatal("alpha", id)
		}
		file := fmt.Sprintf("%s.rgba", id[7:])
		if err = os.WriteFile(filepath.Join(dir, file), im.Pix, 0600); err != nil {
			t.Fatal(err)
		}
		tiles = append(tiles, map[string]any{"id": id, "file": file, "sha256": contentSHA(im.Pix), "zero_pixels": zero, "opaque_pixels": opaque})
	}
	for _, im := range []*image.RGBA{nil, image.NewRGBA(image.Rect(0, 0, 3, 3)), image.NewRGBA(image.Rect(0, 0, 512, 512))} {
		if _, err = originalBattleArtTile(im); err == nil {
			t.Fatal("unsafe tile")
		}
	}
	setupWrite(t, filepath.Join(work, "art-tile-models.json"), map[string]any{"tiles": tiles, "refusals": 3})
}

func TestOriginalBattleArtCommandBindings(t *testing.T) {
	work, _, _ := setupInputs(t)
	v := &originalBattleArt{Context: originalBattleArtContext{Active: true, Unit: "openkb:wolf", X: 23, Y: 100}}
	base := game.OwnedBattleArtRequest{Entry: 0x423, Destination: 0xa000, Mode: 1, CallerCS: 0xf67, CallerIP: 0x2c8a, XByte: 23, Y: 100, WidthBytes: 11, Height: 50}
	if key, err := v.resolve(base); err != nil || key.Unit != "openkb:wolf" || key.Clear {
		t.Fatal(key, err)
	}
	bitmap := base
	bitmap.Entry = 0x626
	bitmap.CallerIP = 0x2c50
	if key, err := v.resolve(bitmap); err != nil || key.Unit != "openkb:wolf" || key.Clear {
		t.Fatal(key, err)
	}
	refusals := 0
	for _, name := range []string{"entry", "caller", "CS", "destination", "mode", "x", "y", "width", "height"} {
		r := base
		switch name {
		case "entry":
			r.Entry++
		case "caller":
			r.CallerIP++
		case "CS":
			r.CallerCS++
		case "destination":
			r.Destination++
		case "mode":
			r.Mode++
		case "x":
			r.XByte++
		case "y":
			r.Y++
		case "width":
			r.WidthBytes++
		case "height":
			r.Height++
		}
		before := len(v.Events)
		if _, err := v.resolve(r); err == nil || len(v.Events) != before {
			t.Fatal("unbound command", name)
		}
		refusals++
	}
	small := base
	small.WidthBytes = 8
	small.Height = 25
	if key, err := v.resolve(small); err != nil || key.Unit != "openkb:wolf" {
		t.Fatal("initial small restore", key, err)
	}
	v.Context.Clear = true
	if key, err := v.resolve(small); err != nil || !key.Clear || key.Unit != "" {
		t.Fatal("dead unit not cleared", key, err)
	}
	if _, err := v.resolve(bitmap); err == nil {
		t.Fatal("dead unit drew bitmap")
	}
	v.Context = originalBattleArtContext{}
	if key, err := v.resolve(base); err != nil || key.Unit != "" || key.Clear || len(key.Retire) != 0 {
		t.Fatal("unbound wrapper selected art")
	}
	setupWrite(t, filepath.Join(work, "art-binding-models.json"), map[string]any{"paired_commands": 3, "refusals": refusals + 1, "small_restore_and_death_clear": true, "unbound_background_unchanged": true})
}
