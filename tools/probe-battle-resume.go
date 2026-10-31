//go:build ignore

package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"image/png"
	"os"
	"path/filepath"
	"reflect"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

func mustResume(e error) {
	if e != nil {
		panic(e)
	}
}
func writeResume(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	mustResume(e)
	f, e := os.OpenFile(p, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
	mustResume(e)
	_, e = f.Write(append(b, '\n'))
	mustResume(e)
	mustResume(f.Close())
}
func main() {
	root := flag.String("root", "", "read-only original")
	assets := flag.String("assets", "", "HD assets")
	input := flag.String("input", "", "fixed inputs")
	out := flag.String("out", "", "new output")
	mode := flag.String("mode", "probe", "probe/init")
	session := flag.String("session", "", "new UI session")
	flag.Parse()
	if os.Getuid() != 1000 {
		panic("UID1000 required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		Name string
		Dst  any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"world-normal.json", &w}} {
		b, e := os.ReadFile(filepath.Join(*input, v.Name))
		mustResume(e)
		mustResume(pairStrictJSON(b, v.Dst))
	}
	base, e := os.ReadFile(filepath.Join(*input, "original-save.ay"))
	mustResume(e)
	if *mode == "init" {
		mustResume(initializeProgressPair(*session, base, c, cc, w))
		return
	}
	mustResume(os.Mkdir(*out, 0700))
	pam, e := os.ReadFile(filepath.Join(*input, "PAM.AY"))
	mustResume(e)
	code, e := worldArmyCode(pam)
	mustResume(e)
	files := map[string][]byte{}
	for i := 0; i < 9; i++ {
		n := fmt.Sprintf("map%02d.ay", i)
		files[n], e = os.ReadFile(filepath.Join(*input, "maps", n))
		mustResume(e)
	}
	dir := filepath.Join(*out, "session")
	mustResume(initializeProgressPair(dir, base, c, cc, w))
	store, snap, e := openProgressPair(dir, c, cc)
	mustResume(e)
	defer func() {
		if store != nil {
			store.Close()
		}
	}()
	scratch := filepath.Join(*out, "warm-shadow")
	mustResume(materializeNativeCheckpoint(*root, *input, scratch, snap))
	eng, e := game.Open(game.Options{Root: *root, Assets: *assets, Saves: scratch, HD: true})
	mustResume(e)
	defer func() {
		if eng != nil {
			eng.Close()
		}
	}()
	// Explicit diagnostic starting state, as authorized. It is never a default
	// player path or a substitute for the separate UI close/reopen sample.
	mustResume(eng.Oracle.LoadStateFile(filepath.Join(*input, "battle-before.state")))
	o := eng.Oracle
	o.OnHostInstruction(oracle.Far(0x110, 0x3733), func(m *dg.Machine) (bool, error) {
		cpu := m.CPU
		ds := uint32(0x1e880)
		bp := cpu.R[dg.BP]
		if bp < 32 || m.Read16(ds+uint32(bp)+2) != 0x171d || m.Read16(ds+uint32(bp)+4) != 0x110 {
			return false, errors.New("fixed source frame")
		}
		cpu.R[dg.SI] = m.Read16(ds + uint32(bp) - 0x12)
		cpu.R[dg.DI] = m.Read16(ds + uint32(bp) - 0x10)
		cpu.R[dg.SP] = bp + 2
		cpu.R[dg.BP] = m.Read16(ds + uint32(bp))
		cpu.IP = 0x32e0
		for i, n := range pairWorldResources(w).words() {
			m.Write16(ds+0x4f2+uint32(i*2), uint16(n))
		}
		for i := 0; i < 12; i++ {
			off := 12 + i*2
			m.Write16(ds+0x54a+uint32(i*2), binary.LittleEndian.Uint16(snap.Bytes.Native[off:])-uint16(off+3))
		}
		cpu.Cycles++
		return true, nil
	})
	mustResume(o.RunUntil(oracle.At(oracle.Far(0x110, 0x32e0)), oracle.Budget(100000)))
	bridge := installRuntimeEnemyBattle(o, store, snap, code)
	if e = o.Run(4000000); !errors.Is(e, errControlledBattleYield) {
		panic(fmt.Sprintf("initial yield %v", e))
	}
	if bridge.Staged == nil {
		panic("missing staged world")
	}
	staged := *bridge.Staged
	beforeCapture, e := store.Recover()
	mustResume(e)
	if beforeCapture.Token != snap.Token || beforeCapture.World.Battle != nil {
		panic("enemy generation committed without a snapshot")
	}
	eng.ReleaseAll()
	held := filepath.Join(*out, "held.state")
	mustResume(o.SaveStateFile(held))
	raw, e := os.ReadFile(held)
	mustResume(e)
	image, e := decodeResumeImage(raw)
	mustResume(e)
	fmt.Println("held snapshot accepted", len(raw), "bytes")
	// The live current map is retained with the VM. All nine maps are embedded.
	files["map01.ay"] = append([]byte(nil), o.Bytes(oracle.Far(0x9c00, 0), 5761)...)
	snap, e = store.CommitSuspendedBattle(snap.Token, staged, raw, files)
	mustResume(e)
	bridge.Current = snap
	bridge.Staged = nil
	begin := snap
	// One real Go action, then close both executor and store. The action must
	// survive in the new executor without regenerating enemies or opening moves.
	action, e := bridge.Current.World.Battle.State.Choose(cc, 0, 0, "normal", 0, -1)
	mustResume(e)
	event, e := bridge.apply(action.Action)
	mustResume(e)
	saved := bridge.Current
	writeResume(filepath.Join(*out, "battle-saved.json"), saved)
	beforeSeed := originalSeed(o)
	beforeRows := append([]byte(nil), o.Bytes(oracle.Far(0x1e88, 0x54a), 24)...)
	eng.Close()
	eng = nil
	store.Close()
	store = nil
	store, cold, e := openProgressPair(dir, c, cc)
	mustResume(e)
	if worldDigest(cold.World) != worldDigest(saved.World) {
		panic("cold Go world changed")
	}
	coldShadow := filepath.Join(*out, "cold-shadow")
	copy := cold
	copy.World.Battle = nil
	mustResume(materializeNativeCheckpoint(*root, *input, coldShadow, copy))
	eng, e = game.Open(game.Options{Root: *root, Assets: *assets, Saves: coldShadow, HD: true})
	mustResume(e)
	b := installControlledBattle(eng.Oracle, store, cold, code)
	ref, e := loadResumeInto(eng.Oracle, store, cold, b)
	mustResume(e)
	if ref.Phase != "battle" || originalSeed(eng.Oracle) != beforeSeed || !bytes.Equal(beforeRows, eng.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		panic("cold native/seed binding")
	}
	if e = eng.Oracle.Run(100); !errors.Is(e, errControlledBattleYield) {
		panic(fmt.Sprintf("cold yield %v", e))
	}
	mustResume(eng.Oracle.SaveStateFile(filepath.Join(*out, "cold-held.state")))
	// Commit retreat while the VM is still held. Capture the persisted return
	// marker before the original caller executes, then kill this executor.
	mustResume(settleRuntimeRetreat(b, eng.Oracle))
	returned := b.Current
	writeResume(filepath.Join(*out, "return-pending.json"), returned)
	if e = settleRuntimeRetreat(b, eng.Oracle); e == nil {
		panic("double settlement accepted")
	}
	expectedSeed := originalSeed(eng.Oracle)
	gold := returned.World.Army.Gold
	mustResume(eng.Oracle.RunUntil(oracle.At(oracle.Far(0x110, 0xbd3)), oracle.Budget(20000000)))
	if !b.Returned || b.NativeCalls != 0 {
		panic("cold battle escaped to native")
	}
	warmReturnSeed := originalSeed(eng.Oracle)
	mustResume(eng.Oracle.SaveStateFile(filepath.Join(*out, "first-return.state")))
	firstWords := []uint16{}
	for _, off := range []uint16{0x56c4, 0x56ca, 0x56cc, 0x56ce, 0x56d0, 0x56d2, 0x56d6, 0x56dc, 0x8e12, 0x8e44} {
		firstWords = append(firstWords, eng.Oracle.Word(oracle.Far(0x1e88, off)))
	}
	eng.Close()
	eng = nil
	store.Close()
	store = nil
	store, coldReturn, e := openProgressPair(dir, c, cc)
	mustResume(e)
	finalShadow := filepath.Join(*out, "return-shadow")
	mustResume(materializeNativeCheckpoint(*root, *input, finalShadow, coldReturn))
	eng, e = game.Open(game.Options{Root: *root, Assets: *assets, Saves: finalShadow, HD: true})
	mustResume(e)
	b = installControlledBattle(eng.Oracle, store, coldReturn, code)
	ref, e = loadResumeInto(eng.Oracle, store, coldReturn, b)
	mustResume(e)
	if ref.Phase != "return" || !b.Settled || originalSeed(eng.Oracle) != expectedSeed {
		panic("return marker/RNG lost")
	}
	mustResume(eng.Oracle.RunUntil(oracle.At(oracle.Far(0x110, 0xbd3)), oracle.Budget(20000000)))
	if !b.Returned || b.NativeCalls != 0 || originalSeed(eng.Oracle) != warmReturnSeed {
		panic("return replay mismatch")
	}
	last, e := store.Recover()
	mustResume(e)
	if last.Token != returned.Token || last.World.Army.Gold != gold {
		panic("replayed return changed reward/penalty")
	}
	coldWords := []uint16{}
	for _, off := range []uint16{0x56c4, 0x56ca, 0x56cc, 0x56ce, 0x56d0, 0x56d2, 0x56d6, 0x56dc, 0x8e12, 0x8e44} {
		coldWords = append(coldWords, eng.Oracle.Word(oracle.Far(0x1e88, off)))
	}
	if !reflect.DeepEqual(firstWords, coldWords) {
		panic("cold return native location")
	}
	mustResume(eng.Oracle.SaveStateFile(filepath.Join(*out, "cold-return.state")))
	f, e := os.Create(filepath.Join(*out, "cold-return.png"))
	mustResume(e)
	mustResume(png.Encode(f, eng.Frame()))
	mustResume(f.Close())
	// Journal interruptions, absent objects and codec corruption are scoped to
	// fresh independent directories; the successful player's pair stays intact.
	faults := []map[string]any{}
	for _, phase := range []string{"resume-object-durable", "intent-durable", "world-durable"} {
		fd := filepath.Join(*out, "fault-"+phase)
		mustResume(initializeProgressPair(fd, base, c, cc, w))
		fs, bs, e := openProgressPair(fd, c, cc)
		mustResume(e)
		fs.Fault = func(p string) error {
			if p == phase {
				return errors.New("controlled interruption")
			}
			return nil
		}
		_, e = fs.CommitSuspendedBattle(bs.Token, staged, raw, files)
		if e == nil {
			panic("missing interruption " + phase)
		}
		fs.Close()
		fs, recovered, e := openProgressPair(fd, c, cc)
		mustResume(e)
		active := recovered.World.Battle != nil
		if active != (phase != "resume-object-durable") {
			panic("half-activated battle")
		}
		fs.Close()
		faults = append(faults, map[string]any{"phase": phase, "active_battle": active, "recovered": true})
	}
	// The native payload is unchanged at battle entry. Exercise its durable
	// boundary on the actual retreat resource change instead.
	fd := filepath.Join(*out, "fault-settlement-native")
	mustResume(initializeProgressPair(fd, base, c, cc, w))
	fs, bs, e := openProgressPair(fd, c, cc)
	mustResume(e)
	bs, e = fs.CommitSuspendedBattle(bs.Token, staged, raw, files)
	mustResume(e)
	plan := planOriginalRand(resumeImageSeed(image))
	value := uint32(plan.Value)
	settlement, e := bs.World.resolveEncounter(c, cc, EncounterContext{Kind: "random"}, DefeatInput{Reason: "retreat", Random: &value})
	mustResume(e)
	fs.Fault = func(p string) error {
		if p == "native-durable" {
			return errors.New("controlled settlement interruption")
		}
		return nil
	}
	_, e = fs.Commit(bs.Token, settlement.After)
	if e == nil {
		panic("missing native settlement interruption")
	}
	fs.Close()
	fs, recovered, e := openProgressPair(fd, c, cc)
	mustResume(e)
	if worldDigest(recovered.World) != worldDigest(settlement.After) {
		panic("native settlement recovery")
	}
	fs.Close()
	faults = append(faults, map[string]any{"phase": "settlement-native-durable", "active_battle": false, "recovered": true})
	r0, e := savedResume(begin.Bytes.World)
	mustResume(e)
	od := filepath.Join(*out, "missing-object")
	mustResume(initializeProgressPair(od, base, c, cc, w))
	ms, bs, e := openProgressPair(od, c, cc)
	mustResume(e)
	bs, e = ms.CommitSuspendedBattle(bs.Token, staged, raw, files)
	mustResume(e)
	ms.Close()
	object := resumeObjectPath(od, r0)
	mustResume(os.Rename(object, object+".missing"))
	_, _, e = openProgressPair(od, c, cc)
	if e == nil {
		panic("missing object accepted")
	}
	if !bytes.Equal(bs.Bytes.World, mustReadResume(filepath.Join(od, "gamedata.ay.army.json"))) {
		panic("missing object rejection changed progress")
	}
	bad := bytes.Clone(raw)
	bad[len(bad)/2] ^= 0x80
	if _, e = decodeResumeImage(bad); e == nil {
		panic("corrupt gzip accepted")
	}
	writeResume(filepath.Join(*out, "receipt.json"), map[string]any{"status": "passed-battle-resume-cold-engine", "controlled_start": true, "normal_player_path": false, "begin_world": begin.World, "saved_world": saved.World, "cold_world": cold.World, "return_world": last.World, "action": event, "native_steps": image.M.Steps, "object_sha256": r0.SHA, "object_bytes": len(raw), "core_sha256": resumeCoreSHA, "seed_before_retreat": beforeSeed, "seed_after_retreat": expectedSeed, "warm_return_seed": warmReturnSeed, "cold_return_seed": originalSeed(eng.Oracle), "native_location": coldWords, "native_calls": b.NativeCalls, "faults": faults, "missing_object_rejected": true, "corrupt_codec_rejected": true, "double_settlement_rejected": true, "formal_changed": false, "gui_verified": false})
	fmt.Println("passed: cold Go action, retreat, idempotent return, atomic activation and rejection")
}
func mustReadResume(p string) []byte { b, e := os.ReadFile(p); mustResume(e); return b }
