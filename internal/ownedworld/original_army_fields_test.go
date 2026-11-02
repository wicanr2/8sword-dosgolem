package ownedworld

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"math"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalArmyFieldsRuntime(t *testing.T) {
	work, root, assets := os.Getenv("EIGHTSWORD_ORIGINAL_FIELDS_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if work == "" || root == "" {
		t.Skip("real inputs required")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, x := range []struct {
		Name  string
		Value any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		b, e := os.ReadFile(filepath.Join(work, "inputs", x.Name))
		must(e)
		must(pairStrictJSON(b, x.Value))
	}
	folder := filepath.Join(work, "runtime-r1")
	must(os.Mkdir(folder, 0700))
	session := filepath.Join(folder, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), c, cc))
	store, snap, err := openProgressPair(session, c, cc)
	must(err)
	w := snap.World
	w.Army.Rules = "tactics"
	w.Army.Leadership = 30000
	w.Army.Slots = [6]ArmyStack{{"native:01", 31}, {"openkb:wolf", 2}, {"openkb:drag", 1}, {"openkb:drui", 1}, {"openkb:troll", 1}, {"openkb:arcr", 1}}
	w.Revision++
	snap, err = store.Commit(snap.Token, w)
	must(err)
	must(os.Mkdir(filepath.Join(folder, "initial-session"), 0700))
	for _, n := range []string{"gamedata.ay", "gamedata.ay.army.json"} {
		b, e := os.ReadFile(filepath.Join(session, n))
		must(e)
		must(os.WriteFile(filepath.Join(folder, "initial-session", n), b, 0600))
	}
	nativeBefore, err := os.ReadFile(filepath.Join(session, "gamedata.ay"))
	must(err)
	scratch := filepath.Join(folder, "scratch")
	must(os.Mkdir(scratch, 0700))
	must(os.WriteFile(filepath.Join(scratch, "gamedata.ay"), nativeBefore, 0600))
	e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: scratch, HD: true})
	must(err)
	defer e.Close()
	if !e.HD {
		t.Fatal(e.Status())
	}
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		t.Helper()
		for n := 0; n < ms; n += 10 {
			must(catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) }))
			e.RenderAudio()
		}
	}
	press := func(scan byte) {
		t.Helper()
		must(e.Key(scan, true))
		advance(100)
		must(e.Key(scan, false))
		advance(300)
	}
	mainReady, mapReady := false, false
	e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { mainReady = e.PAMLoaded })
	e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
	advance(1000)
	press(2)
	press(2)
	advance(1000)
	press(1)
	for n := 0; !mainReady && n < 2000; n++ {
		advance(10)
	}
	if !mainReady {
		t.Fatal("main menu")
	}
	press(0x1c)
	for n := 0; !mapReady && n < 2000; n++ {
		advance(10)
	}
	if !mapReady {
		t.Fatal("Continue map")
	}
	p, err := installWorldArmyPort(e, store, snap)
	must(err)
	v, err := installOriginalArmyReview(e, p)
	must(err)
	d, err := installOriginalArmyDismiss(e, p, v)
	must(err)
	fonts, err := loadArmyUIFonts(filepath.Join(work, "ui-assets"))
	must(err)
	art := loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), fonts.CatalogRawSHA)
	v.Fields = newOriginalArmyFields(v, fonts, art)
	shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
	wait := func(active bool) {
		t.Helper()
		for n := 0; n < 500; n++ {
			if active && v.Ready || !active && v.ReturnReady {
				return
			}
			advance(10)
		}
		t.Fatal("army/map boundary", active)
	}
	shots := []map[string]any{}
	capture := func(name string) {
		t.Helper()
		base := e.Frame()
		out, texts := composeOriginalArmyFields(v, base)
		if !v.Ready || out == base {
			t.Fatal("host fields absent", name)
		}
		for _, x := range texts {
			if x.Ellipsized || !(image.Rect(x.Ink[0], x.Ink[1], x.Ink[2], x.Ink[3])).In(image.Rect(x.Rect[0], x.Rect[1], x.Rect[2], x.Rect[3])) {
				t.Fatal("text geometry", x)
			}
		}
		for suffix, im := range map[string]*image.RGBA{"base": base, "frame": out} {
			f, er := os.Create(filepath.Join(folder, name+"-"+suffix+".png"))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
		}
		b, er := json.MarshalIndent(texts, "", "  ")
		must(er)
		must(os.WriteFile(filepath.Join(folder, name+"-texts.json"), append(b, '\n'), 0600))
		shots = append(shots, map[string]any{"name": name, "font": e.FontID(), "rows": v.Rows, "selected": d.State()["original_dismiss_selected"], "frame_sha256": contentSHA(out.Pix), "base_sha256": contentSHA(base.Pix)})
		// During original redraw and map restoration, retain the complete page.
		v.Ready = false
		held, _ := composeOriginalArmyFields(v, base)
		if held != out {
			t.Fatal("incomplete redraw exposed")
		}
		v.Ready = true
	}
	press(0x3c)
	wait(true)
	capture("f2-noto")
	press(1)
	wait(false)
	press(0x3d)
	wait(true)
	press(0x50)
	wait(true)
	if d.State()["original_dismiss_selected"] != 1 {
		t.Fatal("original Down did not select wolf", d.State())
	}
	capture("f3-wolf-noto")
	press(0x4d)
	wait(true)
	if d.State()["original_dismiss_selected"] != 4 {
		t.Fatal("original Right did not select troll", d.State())
	}
	capture("f3-troll-noto")
	press(1)
	wait(false)
	unchanged, err := os.ReadFile(filepath.Join(session, "gamedata.ay.army.json"))
	must(err)
	original, err := os.ReadFile(filepath.Join(folder, "initial-session/gamedata.ay.army.json"))
	must(err)
	if !bytes.Equal(unchanged, original) {
		t.Fatal("cancel changed pair")
	}
	press(0x3d)
	wait(true)
	press(0x50)
	wait(true)
	press(0x1c)
	wait(true)
	if d.Transactions != 1 || p.Current.World.Army.Slots[1].Unit != "openkb:drag" {
		t.Fatal("wolf transaction", d.State(), p.Current.World.Army.Slots)
	}
	capture("f3-after-wolf")
	press(1)
	wait(false)
	must(e.SetFont("lishu"))
	press(0x3c)
	wait(true)
	capture("f2-lishu")
	press(1)
	wait(false)
	must(e.SetFont("caoshu"))
	press(0x3c)
	wait(true)
	capture("f2-caoshu")
	press(1)
	wait(false)
	// All eight names and maximum numeric widths use the same admitted fields.
	models := []map[string]any{}
	for _, id := range openKBArtIDs {
		model := p.Current.World
		model.Army.Leadership = math.MaxUint64
		model.Army.Slots = [6]ArmyStack{{id, math.MaxUint32}}
		rows, er := originalReviewRowsWithFields(c, model, true)
		must(er)
		must(v.Fields.validate(rows))
		model.Army.Slots = [6]ArmyStack{{"native:01", 1}, {"native:02", 1}, {"native:03", 1}, {"native:04", 1}, {"native:05", 1}, {id, math.MaxUint32}}
		rows, er = originalReviewRowsWithFields(c, model, true)
		must(er)
		must(v.Fields.validate(rows))
		saved := v.Rows
		v.Rows = rows
		for _, font := range []string{"noto", "lishu", "caoshu"} {
			must(e.SetFont(font))
			v.Active = true
			v.Ready = true
			v.Mode = 1
			v.Token = p.Current.Token
			v.Rows = rows
			out, _ := composeOriginalArmyFields(v, e.Frame())
			if out == nil {
				t.Fatal("model frame")
			}
			for _, x := range v.Fields.Texts {
				if x.Ellipsized {
					t.Fatal("truncated number")
				}
			}
		}
		v.Rows = saved
		v.Active = false
		v.Ready = false
		models = append(models, map[string]any{"unit": id, "count": rows[5].Count, "monthly": rows[5].Monthly, "name": rows[5].Name})
		if _, er = originalReviewRows(c, model); er == nil {
			t.Fatal("new unit entered native mode")
		}
	}
	// Missing art must reject before any native row/table operation.
	saved := art.Images["openkb:drag"]
	delete(art.Images, "openkb:drag")
	if _, er := v.rows(p.Current.World); er == nil {
		t.Fatal("missing art accepted")
	}
	art.Images["openkb:drag"] = saved
	after, err := os.ReadFile(filepath.Join(session, "gamedata.ay"))
	must(err)
	if !bytes.Equal(after, nativeBefore) || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		t.Fatal("native data changed")
	}
	final := p.Current.World
	store.Close()
	store, cold, err := openProgressPair(session, c, cc)
	must(err)
	defer store.Close()
	a, _ := json.Marshal(final)
	b, _ := json.Marshal(cold.World)
	if !bytes.Equal(a, b) {
		t.Fatal("cold world")
	}
	report := map[string]any{"status": "passed-original-army-host-fields", "controlled_army": true, "shots": shots, "models": models, "transactions": d.Transactions, "initial_world": snap.World, "final_world": final, "native_shadow_hex": fmt.Sprintf("%x", shadow), "native_progress_unchanged": true, "cold_world_equal": true, "missing_art_rejected": true, "native_extended_rejected": true, "source_skipped_rows": v.Fields.SkippedRows, "source_skipped_names": v.Fields.SkippedNames, "held_frames": v.Fields.Held, "original_art_parity_claimed": false}
	b, err = json.MarshalIndent(report, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
}
