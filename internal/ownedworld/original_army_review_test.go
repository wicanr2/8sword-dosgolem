package ownedworld

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalArmyReviewRuntime(t *testing.T) {
	work, root, assets := os.Getenv("EIGHTSWORD_ORIGINAL_REVIEW_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if work == "" || root == "" {
		t.Skip("real inputs required")
	}
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, v := range []struct {
		n   string
		dst any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		b, e := os.ReadFile(filepath.Join(work, "inputs", v.n))
		must(e)
		must(pairStrictJSON(b, v.dst))
	}
	base, err := os.ReadFile(filepath.Join(root, "GAMEDATA.AY"))
	must(err)
	for _, hd := range []bool{false, true} {
		t.Run(fmt.Sprintf("hd-%v", hd), func(t *testing.T) {
			folder := filepath.Join(work, fmt.Sprintf("runtime-hd-%v", hd))
			must(os.Mkdir(folder, 0700))
			session := filepath.Join(folder, "session")
			must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), c, cc))
			store, snap, err := openProgressPair(session, c, cc)
			must(err)
			defer store.Close()
			w := snap.World
			w.Army.Slots = [6]ArmyStack{{"native:01", 31}, {"native:21", 1}}
			w.Revision++
			snap, err = store.Commit(snap.Token, w)
			must(err)
			beforeNative, err := os.ReadFile(filepath.Join(session, "gamedata.ay"))
			must(err)
			beforeSide, err := os.ReadFile(filepath.Join(session, "gamedata.ay.army.json"))
			must(err)
			control := bytes.Clone(base)
			for i, s := range []struct{ k, n uint16 }{{1, 31}, {21, 1}, {}, {}, {}, {}} {
				off := 12 + i*4
				binary.LittleEndian.PutUint16(control[off:], s.k+uint16(off+3))
				binary.LittleEndian.PutUint16(control[off+2:], s.n+uint16(off+5))
			}
			var frames [2][]byte
			var report = map[string]any{"hd": hd, "controlled_army": true, "normal_keyboard_path": true, "go_rows": w.Army.Slots}
			for side := 0; side < 2; side++ {
				scratch := filepath.Join(folder, fmt.Sprintf("scratch-%d", side))
				must(os.Mkdir(scratch, 0700))
				raw := control
				if side == 1 {
					raw = base
				}
				must(os.WriteFile(filepath.Join(scratch, "gamedata.ay"), raw, 0600))
				e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: scratch, HD: hd})
				must(err)
				if hd && !e.HD {
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
				ready, mapReady, waits := false, false, 0
				e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { ready = e.PAMLoaded })
				e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
				e.Oracle.OnCall(oracle.Far(0x110, 0x844c), func(o *oracle.Oracle) {
					r := o.Regs()
					if r.SP <= 65531 && o.Word(oracle.Far(r.SS, r.SP)) == 0x3ed8 && o.Word(oracle.Far(r.SS, r.SP+2)) == 0x110 {
						waits++
					}
				})
				advance(1000)
				press(2)
				press(2)
				advance(1000)
				press(1)
				for n := 0; !ready && n < 2000; n++ {
					advance(10)
				}
				if !ready {
					t.Fatal("main menu not reached", e.Status())
				}
				press(0x1c)
				for n := 0; !mapReady && n < 2000; n++ {
					advance(10)
				}
				if !mapReady {
					t.Fatal("normal Continue did not reach map", e.Status())
				}
				var port *worldArmyPort
				var view *originalArmyReview
				if side == 1 {
					port = &worldArmyPort{Store: store, Current: snap}
					if hd {
						port, err = installWorldArmyPort(e, store, snap)
						must(err)
					}
					view, err = installOriginalArmyReview(e, port)
					must(err)
				}
				shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
				press(0x3c)
				for n := 0; waits == 0 && n < 500; n++ {
					advance(10)
				}
				if waits == 0 {
					t.Fatal("F2 wait not reached", e.Status())
				}
				advance(100)
				if side == 1 && !view.Ready {
					t.Fatal("F2 panel not committed")
				}
				frame := e.Frame()
				frames[side] = bytes.Clone(frame.Pix)
				if side == 1 {
					token := view.Token
					view.Token = "stale"
					if view.check() == nil {
						t.Fatal("stale snapshot accepted")
					}
					view.Token = token
					view.Code[0x75c6] ^= 1
					if view.check() == nil {
						t.Fatal("wrong source accepted")
					}
					view.Code[0x75c6] ^= 1
					report["stale_and_source_rejected"] = true
				}
				out, err := os.Create(filepath.Join(folder, fmt.Sprintf("side-%d.png", side)))
				must(err)
				must(png.Encode(out, frame))
				must(out.Close())
				press(1)
				advance(200)
				if side == 1 {
					if view.Active || view.Opens != 1 || view.Closes != 1 || view.Reads != [4]uint64{6, 2, 2, 2} {
						t.Fatal("Go review lifecycle", view.Opens, view.Closes, view.Reads)
					}
					press(0x3c)
					advance(200)
					press(1)
					if view.Active || view.Opens != 2 || view.Closes != 2 {
						t.Fatal("second F2 lifecycle")
					}
					if !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
						t.Fatal("shadow military mutated")
					}
					report["go_opens"] = view.Opens
					report["go_closes"] = view.Closes
					report["data_operations"] = view.Reads
					report["native_shadow_hex"] = fmt.Sprintf("%x", shadow)
					// If host operations are disabled, the post-operation sentinel
					// must stop before original UI can consume shadow army data.
					if hd {
						e.Oracle.OnHostInstruction(oracle.Far(0x110, 0x75fd), func(*dg.Machine) (bool, error) { return false, nil })
						must(e.Key(0x3c, true))
						var refused error
						for n := 0; n < 500 && refused == nil; n++ {
							refused = catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) })
						}
						if refused == nil {
							t.Fatal("disabled data hook fell back to native army")
						}
						report["disabled_data_hook_refused"] = refused.Error()
					}
				}
				e.Close()
			}
			if !bytes.Equal(frames[0], frames[1]) {
				t.Fatal("original F2 and Go data F2 frames differ")
			}
			after, err := os.ReadFile(filepath.Join(session, "gamedata.ay"))
			must(err)
			if !bytes.Equal(after, beforeNative) {
				t.Fatal("native progress changed")
			}
			after, err = os.ReadFile(filepath.Join(session, "gamedata.ay.army.json"))
			must(err)
			if !bytes.Equal(after, beforeSide) {
				t.Fatal("Go progress changed")
			}
			report["frame_sha256"] = contentSHA(frames[1])
			report["full_frame_equal"] = true
			report["wait_boundary"] = "0110:844C/return-3ED8"
			report["save_pair_unchanged"] = true
			b, err := json.MarshalIndent(report, "", "  ")
			must(err)
			must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
		})
	}
}

func TestOriginalArmyReviewScopeRefusals(t *testing.T) {
	work, root := os.Getenv("EIGHTSWORD_ORIGINAL_REVIEW_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if work == "" {
		t.Skip("real catalog required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, v := range []struct {
		n   string
		dst any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		b, e := os.ReadFile(filepath.Join(work, "inputs", v.n))
		if e != nil {
			t.Fatal(e)
		}
		if e = pairStrictJSON(b, v.dst); e != nil {
			t.Fatal(e)
		}
	}
	dir := filepath.Join(t.TempDir(), "import")
	if e := importNativeProgress(root, root, dir, filepath.Join(work, "inputs"), c, cc); e != nil {
		t.Fatal(e)
	}
	store, snap, e := openProgressPair(dir, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	defer store.Close()
	for _, name := range []string{"extended", "hole", "count-range", "monthly-range"} {
		t.Run(name, func(t *testing.T) {
			w := snap.World
			w.Army.Leadership = 10000000
			switch name {
			case "extended":
				w.Army.Rules = "tactics"
				w.Army.Slots[1] = ArmyStack{"openkb:wolf", 1}
			case "hole":
				w.Army.Slots[2] = ArmyStack{"native:21", 1}
			case "count-range":
				w.Army.Slots[0].Count = 32768
			case "monthly-range":
				w.Army.Slots = [6]ArmyStack{{"native:25", 30000}}
			}
			if _, err := originalReviewRows(c, w); err == nil {
				t.Fatal("unsafe original presentation accepted")
			}
		})
	}
}
