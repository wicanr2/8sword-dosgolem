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

func TestOriginalDismissZeroFlags(t *testing.T) {
	for kind := uint16(0); kind <= 25; kind++ {
		m := dg.New()
		m.CPU.Seg[dg.CS] = 0x100
		m.CPU.Seg[dg.DS] = 0x2000
		m.CPU.IP = 0x200
		m.CPU.Flags = 0xad7
		copy(m.Mem[0x1200:], []byte{0x83, 0xbf, 0x4a, 0x05, 0})
		m.Write16(0x2054a, kind)
		if err := m.Step(); err != nil {
			t.Fatal(err)
		}
		if got := originalKindZeroFlags(0xad7, kind); got != m.CPU.Flags {
			t.Fatalf("kind %d flags Go=%04x original=%04x", kind, got, m.CPU.Flags)
		}
	}
}

func TestOriginalDismissRuntime(t *testing.T) {
	work, root, assets := os.Getenv("EIGHTSWORD_ORIGINAL_DISMISS_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG"), os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
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
			seed := filepath.Join(folder, "initial-session")
			must(os.Mkdir(seed, 0700))
			must(os.WriteFile(filepath.Join(seed, "gamedata.ay"), snap.Bytes.Native, 0600))
			must(os.WriteFile(filepath.Join(seed, "gamedata.ay.army.json"), snap.Bytes.World, 0600))
			nativeBefore := bytes.Clone(snap.Bytes.Native)
			initialToken := snap.Token
			initialRevision := snap.World.Revision
			control := bytes.Clone(base)
			for i, s := range []struct{ k, n uint16 }{{1, 31}, {21, 1}, {}, {}, {}, {}} {
				off := 12 + i*4
				binary.LittleEndian.PutUint16(control[off:], s.k+uint16(off+3))
				binary.LittleEndian.PutUint16(control[off+2:], s.n+uint16(off+5))
			}
			frames := [2]map[string][]byte{}
			report := map[string]any{"hd": hd, "controlled_army": true, "normal_keyboard_path": true, "initial_go_rows": w.Army.Slots, "full_guest_state_parity_claimed": false}
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
				await := func(test func() bool) {
					t.Helper()
					for n := 0; !test() && n < 1500; n++ {
						advance(10)
					}
					if !test() {
						t.Fatal("original UI boundary timeout", e.Status())
					}
					advance(100)
				}
				menu, mapReady, waits, f2waits, returns := false, false, 0, 0, 0
				e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { menu = e.PAMLoaded })
				e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
				e.Oracle.OnCall(oracle.Far(0x110, 0x779e), func(*oracle.Oracle) { waits++ })
				e.Oracle.OnCall(oracle.Far(0x110, 0x3e91), func(*oracle.Oracle) { returns++ })
				e.Oracle.OnCall(oracle.Far(0x110, 0x844c), func(o *oracle.Oracle) {
					r := o.Regs()
					if r.SP <= 65531 && o.Word(oracle.Far(r.SS, r.SP)) == 0x3ed8 {
						f2waits++
					}
				})
				advance(1000)
				press(2)
				press(2)
				advance(1000)
				press(1)
				await(func() bool { return menu })
				press(0x1c)
				await(func() bool { return mapReady })
				var view *originalArmyReview
				var dismiss *originalArmyDismiss
				var port *worldArmyPort
				if side == 1 {
					port = &worldArmyPort{Store: store, Current: snap}
					if hd {
						port, err = installWorldArmyPort(e, store, snap)
						must(err)
					}
					view, err = installOriginalArmyReview(e, port)
					must(err)
					dismiss, err = installOriginalArmyDismiss(e, port, view)
					must(err)
				}
				shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
				frames[side] = map[string][]byte{}
				snapshot := func(name string) {
					t.Helper()
					im := e.Frame()
					frames[side][name] = bytes.Clone(im.Pix)
					out, er := os.Create(filepath.Join(folder, fmt.Sprintf("side-%d-%s.png", side, name)))
					must(er)
					must(png.Encode(out, im))
					must(out.Close())
				}
				open := func() {
					t.Helper()
					old := waits
					press(0x3d)
					await(func() bool { return waits > old })
					if side == 1 && (!view.Ready || view.Mode != 2) {
						t.Fatal("F3 not committed")
					}
				}
				close := func() {
					t.Helper()
					old := returns
					press(1)
					await(func() bool { return returns > old })
					if side == 1 && (view.Active || !view.ReturnReady) {
						t.Fatal("F3 map return not committed")
					}
				}
				open()
				snapshot("opened")
				old := waits
				press(0x50)
				await(func() bool { return waits > old })
				snapshot("selected-second")
				if side == 1 && dismiss.State()["original_dismiss_selected"] != 1 {
					t.Fatal("original down navigation")
				}
				close()
				if side == 1 {
					after, er := store.Recover()
					must(er)
					if after.Token != initialToken || dismiss.Transactions != 0 {
						t.Fatal("cancel committed")
					}
				}
				open()
				for _, key := range []byte{0x4b, 0x4d, 0x50, 0x48} {
					old = waits
					press(key)
					await(func() bool { return waits > old })
				}
				if side == 1 && dismiss.State()["original_dismiss_selected"] != 0 {
					t.Fatal("original direction navigation")
				}
				old = waits
				if side == 1 {
					must(e.Key(0x1c, true))
					advance(1000)
					must(e.Key(0x1c, false))
					advance(300)
				} else {
					press(0x1c)
				}
				await(func() bool { return waits > old })
				snapshot("after-dismiss")
				if side == 1 {
					after, er := store.Recover()
					must(er)
					if dismiss.Transactions != 1 || after.World.Army.Slots[0] != (ArmyStack{"native:21", 1}) || after.World.Army.Slots[1].Count != 0 {
						t.Fatal("Go removal/held Enter", dismiss.State(), after.World.Army.Slots)
					}
					report["held_enter_transactions"] = dismiss.Transactions
					report["ignored_enter"] = dismiss.IgnoredEnter
				}
				close()
				old = f2waits
				press(0x3c)
				await(func() bool { return f2waits > old })
				snapshot("f2-remaining")
				old = returns
				press(1)
				await(func() bool { return returns > old })
				open()
				old = waits
				press(0x1c)
				await(func() bool { return waits > old })
				snapshot("empty")
				if side == 1 {
					for _, key := range []byte{0x48, 0x4d, 0x1c} {
						old = waits
						press(key)
						await(func() bool { return waits > old })
					}
					after, er := store.Recover()
					must(er)
					if dismiss.Transactions != 2 || after.World.Revision != initialRevision+2 || after.World.Army.Slots != ([6]ArmyStack{}) {
						t.Fatal("empty army transaction", dismiss.State())
					}
					if !bytes.Equal(nativeBefore, after.Bytes.Native) || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
						t.Fatal("shadow or native progress changed")
					}
					report["final_world"] = after.World
					report["transactions"] = dismiss.Transactions
					report["native_shadow_hex"] = fmt.Sprintf("%x", shadow)
				}
				close()
				e.Close()
			}
			for name, frame := range frames[0] {
				if !bytes.Equal(frame, frames[1][name]) {
					t.Fatal("original / Go F3 frame differs", name)
				}
			}
			store.Close()
			cold, after, er := openProgressPair(session, c, cc)
			must(er)
			if after.World.Army.Slots != ([6]ArmyStack{}) || after.World.Revision != initialRevision+2 {
				t.Fatal("cold pair lost dismissal")
			}
			cold.Close()
			report["full_frames_equal"] = true
			report["cold_pair_passed"] = true
			report["native_progress_unchanged"] = true
			b, er := json.MarshalIndent(report, "", "  ")
			must(er)
			must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
		})
	}
}

func TestOriginalDismissWriteIsolation(t *testing.T) {
	work, root := os.Getenv("EIGHTSWORD_ORIGINAL_DISMISS_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if work == "" {
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
	for _, route := range []string{"read", "commit"} {
		t.Run(route, func(t *testing.T) {
			folder := filepath.Join(work, "fault-"+route)
			must(os.Mkdir(folder, 0700))
			session := filepath.Join(folder, "session")
			must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), c, cc))
			store, snap, err := openProgressPair(session, c, cc)
			must(err)
			defer store.Close()
			beforeToken := snap.Token
			scratch := filepath.Join(folder, "scratch")
			must(os.Mkdir(scratch, 0700))
			must(os.WriteFile(filepath.Join(scratch, "gamedata.ay"), base, 0600))
			e, err := game.Open(game.Options{Root: root, Saves: scratch, HD: false})
			must(err)
			defer e.Close()
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
			menu, mapReady := false, false
			e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { menu = e.PAMLoaded })
			e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
			advance(1000)
			press(2)
			press(2)
			advance(1000)
			press(1)
			for n := 0; !menu && n < 1500; n++ {
				advance(10)
			}
			if !menu {
				t.Fatal("menu")
			}
			press(0x1c)
			for n := 0; !mapReady && n < 1500; n++ {
				advance(10)
			}
			if !mapReady {
				t.Fatal("Continue")
			}
			p := &worldArmyPort{Store: store, Current: snap}
			v, err := installOriginalArmyReview(e, p)
			must(err)
			d, err := installOriginalArmyDismiss(e, p, v)
			must(err)
			native := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
			disabled := uint16(0x7b2e)
			if route == "read" {
				disabled = 0x7baf
			}
			e.Oracle.OnHostInstruction(oracle.Far(0x110, disabled), func(*dg.Machine) (bool, error) { return false, nil })
			must(e.Key(0x3d, true))
			var refused error
			for n := 0; n < 1500; n++ {
				refused = catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) })
				if refused != nil || v.Ready {
					break
				}
			}
			if route == "commit" {
				must(e.Key(0x3d, false))
				if !v.Ready {
					t.Fatal("F3 not ready")
				}
				must(e.Key(0x1c, true))
				for n := 0; n < 1500 && refused == nil; n++ {
					refused = catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) })
				}
			}
			if refused == nil {
				t.Fatal("disabled host operation escaped")
			}
			after, err := store.Recover()
			must(err)
			if after.Token != beforeToken || d.Transactions != 0 || !bytes.Equal(native, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
				t.Fatal("refusal changed Go or shadow army")
			}
			b, _ := json.MarshalIndent(map[string]any{"route": route, "rejected": refused.Error(), "pair_unchanged": true, "native_shadow_unchanged": true, "transactions": d.Transactions}, "", "  ")
			must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
		})
	}
}
