//go:build ignore

// Spec030 DRAFT. Read-only actor-call inventory, kept outside production.
package ownedworld
import("encoding/binary";"errors";"fmt";"os";"path/filepath";"testing";"github.com/wicanr2/dosgolem/oracle")
func TestResearchOwnedBattleArt(t *testing.T) {
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
	parent := filepath.Join(work, "sessions-r1")
	must(os.MkdirAll(parent, 0700))
	name := os.Getenv("EIGHTSWORD_SESSION_CASE")
	if name == "" {
		name = "hd-native-go"
	}
	native := name == "hd-native-control"
	mixed := name == "hd-mixed-go"
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

 trace:=[]map[string]any{}
 rawdir:=filepath.Join(work,"art-probe-raw");must(os.Mkdir(rawdir,0700))
 e.Oracle.OnCall(oracle.Far(0x14d2,0x626),func(o *oracle.Oracle){
  rr:=o.Regs();ptr:=oracle.Far(o.Arg(1),o.Arg(0));head:=o.Bytes(ptr,4)
  if len(trace)>=4096||binary.LittleEndian.Uint16(head)!=11||binary.LittleEndian.Uint16(head[2:])!=50{return}
  raw:=o.Bytes(ptr,3304);digest:=contentSHA(raw);path:=filepath.Join(rawdir,digest+".bin");if _,er:=os.Stat(path);os.IsNotExist(er){must(os.WriteFile(path,raw,0600))}
  words:=[]uint16{};for i:=-8;i<14;i++{words=append(words,o.Word(oracle.Far(rr.SS,uint16(int(rr.BP)+i*2))))}
  trace=append(trace,map[string]any{"step":o.Steps(),"regs":rr,"pointer":ptr,"caller_ip":o.Word(oracle.Far(rr.SS,rr.SP)),"caller_cs":o.Word(oracle.Far(rr.SS,rr.SP+2)),"x":o.Arg(2),"y":o.Arg(3),"frame_words_bp_minus16":words,"source_sha256":digest,"rows":owner.Rounds.Actions.rows(),"slots":owner.Rounds.Actions.slots(),"coordinates_player_hex":fmt.Sprintf("%x",o.Bytes(oracle.Far(0x1e88,0x703c),12)),"projection_phase":owner.Projection.Phase,"round_active":owner.Rounds.Active})
 })
 defer func(){setupWrite(t,filepath.Join(work,"art-probe.json"),map[string]any{"calls":trace,"observation_only":true})}()
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
