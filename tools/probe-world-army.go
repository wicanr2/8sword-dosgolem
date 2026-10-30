//go:build ignore

// 030 DRAFT: ordinary map/shop inputs after an explicit Go wolf setup. No
// expanded unit ID is written to the guest. The formal Engine guard is intact.
package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"strings"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func waMust(e error) {
	if e != nil {
		panic(e)
	}
}
func waWrite(p string, v any) {
	raw, e := json.MarshalIndent(v, "", "  ")
	waMust(e)
	waMust(os.WriteFile(p, append(raw, '\n'), 0600))
}

func main() {
	root := flag.String("root", "", "original read-only")
	assets := flag.String("assets", "", "HD read-only")
	input := flag.String("input", "", "real catalogs")
	out := flag.String("out", "", "new directory")
	apply := flag.Bool("apply", false, "Go read/commit ports")
	flag.Parse()
	if os.Getuid() != 1000 || *out == "" {
		panic("UID1000 and paths required")
	}
	waMust(os.Mkdir(*out, 0755))
	var catalog ArmyCatalog
	var combat game.OwnedCombatCatalog
	raw, x := os.ReadFile(filepath.Join(*input, "army-catalog.json"))
	waMust(x)
	waMust(pairStrictJSON(raw, &catalog))
	raw, x = os.ReadFile(filepath.Join(*input, "combat-catalog.json"))
	waMust(x)
	waMust(pairStrictJSON(raw, &combat))
	e, x := game.Open(game.Options{Root: *root, Assets: *assets, Saves: filepath.Join(*out, "scratch"), HD: true})
	waMust(x)
	defer e.Close()
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	advance := func(ms int) {
		for n := 0; n < ms; n += 10 {
			waMust(catchWorldArmyFault(func() error { return e.AdvanceCycles(30000) }))
			e.RenderAudio()
			if n%100 == 0 {
				e.Frame()
			}
			if e.Exited {
				panic("unexpected exit")
			}
		}
	}
	keys := []map[string]any{}
	press := func(scan byte) {
		keys = append(keys, map[string]any{"step": e.Oracle.Steps(), "scan": scan})
		waMust(e.Key(scan, true))
		advance(100)
		waMust(e.Key(scan, false))
		advance(200)
	}
	word := func(off uint16) uint16 { return e.Oracle.Word(oracle.Far(0x1e88, off)) }
	capture := func(name string) {
		f, x := os.Create(filepath.Join(*out, name+".png"))
		waMust(x)
		waMust(png.Encode(f, e.Frame()))
		waMust(f.Close())
		waMust(e.Oracle.SaveStateFile(filepath.Join(*out, name+".state")))
	}
	advance(200)
	press(2)
	press(2)
	advance(500)
	if !e.PAMLoaded {
		press(1)
	}
	for n := 0; n < 300 && e.Tracker.VisibleScene != "main-menu"; n++ {
		advance(100)
	}
	if e.Tracker.VisibleScene != "main-menu" {
		panic("menu missing")
	}
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(3000)
	if e.Tracker.VisibleScene != "map" {
		panic("new map missing")
	}
	// Save the actual new game's opaque bytes before the controlled Go setup.
	press(0x41)
	advance(500)
	if e.Tracker.VisibleScene != "system-menu" {
		panic("F7 missing")
	}
	press(0x1c)
	advance(500)
	press(0x1c)
	advance(1500)
	if e.Tracker.VisibleScene != "map" {
		panic("F7 map return missing")
	}
	base, x := os.ReadFile(filepath.Join(*out, "scratch/gamedata.ay"))
	waMust(x)
	native, x := decodeNativeResources(nativeProgressSource, base)
	waMust(x)
	var a OwnedArmy
	a.Gold = native.Gold
	a.Leadership = native.Leadership
	a.RecruitRank = uint32(native.Rank)
	a.Rules = "tactics"
	a.Offers = map[string]ArmyOffer{"controlled-wolves": {Unit: "openkb:wolf", Stock: 1000}}
	for i := 0; i < 6; i++ {
		kind, count := word(0x54a+uint16(i*4)), word(0x54c+uint16(i*4))
		if kind != 0 {
			if kind > 25 || count == 0 {
				panic("native initial army")
			}
			a.Slots[i] = ArmyStack{fmt.Sprintf("native:%02d", kind), uint32(count)}
		}
	}
	var recruitment RecruitReceipt
	a, recruitment, x = a.recruit(catalog, "controlled-wolves", 5)
	waMust(x)
	w := OwnedWorld{Schema: "eightsword-owned-world/1", Army: a, Progress: WorldProgress{Rank: uint32(native.Rank), Merit: native.Merit, Legacy04F6: native.MonthlyPay, Legacy04FC: native.SpellPower}, Encounters: map[string]WorldEncounter{}}
	for i := range w.Progress.Thresholds {
		w.Progress.Thresholds[i] = uint64(word(0x5b2 + uint16(i*2)))
	}
	waMust(w.validate(catalog, combat))
	pairDir := filepath.Join(*out, "paired-save")
	waMust(initializeProgressPair(pairDir, base, catalog, combat, w))
	store, snap, x := openProgressPair(pairDir, catalog, combat)
	waMust(x)
	defer store.Close()
	for i, v := range pairWorldResources(w).words() {
		e.Oracle.WriteU16(oracle.Far(0x1e88, 0x4f2+uint16(i*2)), uint16(v))
	}
	initialArmy := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
	waMust(os.WriteFile(filepath.Join(*out, "native-army-before.bin"), initialArmy, 0600))
	waMust(os.WriteFile(filepath.Join(*out, "original-save.ay"), base, 0600))
	capture("projected-map")
	var port *worldArmyPort
	if *apply {
		port, x = installWorldArmyPort(e, store, snap)
		waMust(x)
	}
	var operandReads []map[string]any
	if !*apply {
		for _, ip := range worldArmyReadGuards {
			ip := ip
			e.Oracle.OnCall(oracle.Far(0x110, ip), func(o *oracle.Oracle) {
				if len(operandReads) > 256 {
					panic("operand observation limit")
				}
				r := o.Regs()
				operandReads = append(operandReads, map[string]any{"ip": ip, "step": o.Steps(), "registers": r})
			})
		}
	}
	var maximum uint16
	var offerKind, offerStock uint16
	var commits int
	e.Oracle.OnCall(oracle.Far(0x110, 0x54ea), func(o *oracle.Oracle) {
		r := o.Regs()
		offerKind = o.Word(oracle.Far(r.SS, r.SP+4))
		offerStock = o.Word(oracle.Far(r.SS, r.SP+6))
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x55dd), func(o *oracle.Oracle) { r := o.Regs(); maximum = o.Word(oracle.Far(r.SS, r.BP-6)) })
	e.Oracle.OnCall(oracle.Far(0x110, 0x56ec), func(o *oracle.Oracle) { commits++; waMust(o.SaveStateFile(filepath.Join(*out, "before-commit.state"))) })
	e.Oracle.OnCall(oracle.Far(0x110, 0x576b), func(o *oracle.Oracle) { waMust(o.SaveStateFile(filepath.Join(*out, "after-commit.state"))) })
	// Same ordinary movement and shop input as the preserved native control.
	for _, scan := range []byte{0x4b, 0x48} {
		press(scan)
		advance(500)
		press(0x3b)
		advance(400)
		press(1)
		advance(400)
	}
	press(0x48)
	advance(1000)
	if maximum == 0 || offerKind != 1 {
		waWrite(filepath.Join(*out, "incomplete.json"), e.Status())
		panic("verified militia shop absent")
	}
	capture("shop-maximum")
	// Original numeric editor starts at zero: enter 1 and confirm.
	press(2)
	press(0x1c)
	advance(1500)
	if commits != 1 || e.Tracker.VisibleScene != "map" {
		waWrite(filepath.Join(*out, "incomplete.json"), e.Status())
		panic("single purchase/map return missing")
	}
	capture("final-map")
	finalArmy := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
	waMust(os.WriteFile(filepath.Join(*out, "native-army-after.bin"), finalArmy, 0600))
	finalPair, x := store.Recover()
	waMust(x)
	waWrite(filepath.Join(*out, "pair-before.json"), snap)
	waWrite(filepath.Join(*out, "pair-after.json"), finalPair)
	var records []worldArmyPortRecord
	var calls, purchases uint64
	if port != nil {
		records = port.Records
		calls = port.NativeEntries
		purchases = port.Purchases
		if calls != 0 || purchases != 1 || len(records) != 4 || !bytes.Equal(initialArmy, finalArmy) {
			panic("Go port did not own all operations")
		}
	}
	blockedF2 := ""
	if port != nil {
		waMust(e.Key(0x3c, true))
		err := catchWorldArmyFault(func() error { return e.AdvanceCycles(3000000) })
		var fault *worldArmyPortFault
		if !errors.As(err, &fault) || !strings.Contains(fault.Reason, "unsupported world army operand") {
			panic(fmt.Sprintf("unimplemented army UI was not blocked: %v", err))
		}
		blockedF2 = fault.Reason
		waMust(e.Key(0x3c, false))
		if !bytes.Equal(finalArmy, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
			panic("blocked army UI wrote rows")
		}
	}
	store.Close()
	cold, coldSnap, x := openProgressPair(pairDir, catalog, combat)
	waMust(x)
	cold.Close()
	if coldSnap.Token != finalPair.Token {
		panic("cold pair mismatch")
	}
	guard, guardErr := game.Open(game.Options{Root: "/unmounted-original", Saves: pairDir, HD: true})
	if guard != nil || !errors.Is(guardErr, game.ErrOwnedArmyHandoffPending) {
		panic(fmt.Sprintf("formal guard: %v", guardErr))
	}
	waWrite(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-world-army-port-probe", "go_port": *apply, "controlled_setup": recruitment, "normal_new_game_and_native_save": true, "controlled_initial_wolves": 5, "projected_resources": pairWorldResources(w), "offer_kind": offerKind, "offer_stock": offerStock, "maximum": maximum, "purchase_count": commits, "guest_gold": word(0x4f8), "go_records": records, "native_helper_entries": calls, "go_purchases": purchases, "cold_pair_token": coldSnap.Token, "formal_guard": true, "blocked_f2": blockedF2, "original_operand_observations": operandReads, "keys": keys, "limits": []string{"Explicit five-wolf Go fixture and resource projection, not a natural expanded-army path.", "Only the one verified militia-shop caller is admitted; persistent map identity/stock, monthly consumers and other screens remain blocked.", "Go call replacements are not original CPU clock/step parity; screenshots are Engine Frame, not new Ebiten windows."}})
	fmt.Println("world army port passed", *apply, "maximum", maximum, "gold", word(0x4f8))
}
