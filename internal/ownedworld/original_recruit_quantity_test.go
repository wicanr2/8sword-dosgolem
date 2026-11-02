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

func recruitQuantityCatalogs(t *testing.T) (string, string, ArmyCatalog, game.OwnedCombatCatalog) {
	t.Helper()
	work, root := os.Getenv("EIGHTSWORD_ORIGINAL_QUANTITY_WORK"), os.Getenv("EIGHTSWORD_TEST_ORIG")
	if work == "" || root == "" {
		t.Skip("real inputs required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	for _, x := range []struct {
		Name  string
		Value any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}} {
		b, err := os.ReadFile(filepath.Join(work, "inputs", x.Name))
		if err != nil {
			t.Fatal(err)
		}
		if err = pairStrictJSON(b, x.Value); err != nil {
			t.Fatal(err)
		}
	}
	return work, root, c, cc
}

func TestOriginalRecruitQuantityPlansAndGates(t *testing.T) {
	work, root, c, cc := recruitQuantityCatalogs(t)
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "models-r1")
	must(os.Mkdir(folder, 0700))
	input := filepath.Join(folder, "source")
	must(os.Mkdir(input, 0700))
	raw, err := os.ReadFile(filepath.Join(root, "GAMEDATA.AY"))
	must(err)
	word := func(off int, n uint16) { binary.LittleEndian.PutUint16(raw[off:], n+uint16(off+3)) }
	word(0, 5)
	word(6, 30000)
	word(8, 30000)
	for off := 12; off < 36; off += 2 {
		word(off, 0)
	}
	word(campOffset(0, 1, 3), 20)
	word(campOffset(0, 1, 4), 8000)
	must(os.WriteFile(filepath.Join(input, "GAMEDATA.AY"), raw, 0600))
	session := filepath.Join(folder, "session")
	must(importNativeProgress(root, input, session, filepath.Join(work, "inputs"), c, cc))
	store, snap, err := openProgressPair(session, c, cc)
	must(err)
	defer store.Close()
	maps, err := decodeCheckpointMaps(snap.Bytes.World)
	must(err)
	snap, err = store.BindCamp(snap.Token, 0, 1, maps)
	must(err)
	codeRaw, err := os.ReadFile(filepath.Join(work, "inputs/PAM.AY"))
	must(err)
	code, err := worldArmyCode(codeRaw)
	must(err)
	p := &worldArmyPort{Store: store, Current: snap, ShopID: campKey(0, 1), ShopUnit: "native:20", ShopKind: 20, ShopStock: 8000, ShopGroup: 0, ShopRow: 1, ShopOpen: true, ShopSP: 0xff00, Expected: map[uint16][]byte{0x54ea: code[0x54ea:0x58f0]}}
	x := &originalRecruitQuantity{Port: p, Code: code}
	makeMachine := func(ip uint16, count uint16) *dg.Machine {
		m := dg.New()
		copy(m.Mem[0x1100:], code)
		m.CPU.Seg[dg.CS] = 0x110
		m.CPU.Seg[dg.DS] = 0x1e88
		m.CPU.Seg[dg.SS] = 0x1e88
		m.CPU.IP = ip
		m.CPU.R[dg.BP] = 0xfefe
		m.CPU.R[dg.SP] = 0xfef0
		m.CPU.R[dg.AX] = count
		base := uint32(0x1e880)
		m.Write16(base+0xff00, 0x5a21)
		m.Write16(base+0xff02, 0x110)
		m.Write16(base+0xff04, 20)
		m.Write16(base+0xff06, 8000)
		m.Write16(base+0xfefc, count)
		for i, n := range pairWorldResources(p.Current.World).words() {
			m.Write16(base+0x4f2+uint32(i*2), uint16(n))
		}
		x.InputPending = ip == 0x5689
		x.Returned = x.InputPending
		x.Value = count
		x.InputParent = 0xfefe
		x.Text = fmt.Sprint(count)
		return m
	}
	idx, err := c.index()
	must(err)
	models := []map[string]any{}
	for kind := uint16(1); kind <= 25; kind++ {
		a := snap.World.Army
		id := fmt.Sprintf("native:%02d", kind)
		a.Offers = map[string]ArmyOffer{"model": {id, 8000}}
		plan, er := originalRecruitPlanFor(c, a, "model")
		must(er)
		if plan.Limit != 30000/idx[id].Command || plan.Price != idx[id].Gold || plan.Preflight != 0x55f0 {
			t.Fatal("native plan", kind, plan)
		}
		for _, n := range []uint32{0, 1, 2500, 6000, 9999} {
			next, er := plan.result(n, a.Gold)
			must(er)
			want := uint16(0x56ec)
			switch {
			case n == 0:
				want = 0x555f
			case uint64(n) > plan.Limit || n > plan.Stock:
				want = 0x5699
			case uint64(n)*plan.Price > a.Gold:
				want = 0x55a0
			}
			if next != want {
				t.Fatal("plan route", kind, n, next, want)
			}
		}
		models = append(models, map[string]any{"kind": kind, "price": plan.Price, "command": plan.Command, "limit": plan.Limit})
	}
	baseArmy := snap.World.Army
	baseArmy.Offers = map[string]ArmyOffer{"model": {"native:20", 8000}}
	for _, name := range []string{"rank", "slots", "gold", "leadership", "stock"} {
		a := baseArmy
		switch name {
		case "rank":
			a.RecruitRank = 0
		case "slots":
			a.Slots = [6]ArmyStack{{"native:01", 1}, {"native:02", 1}, {"native:03", 1}, {"native:04", 1}, {"native:05", 1}, {"native:06", 1}}
		case "gold":
			a.Gold = 0
		case "leadership":
			a.Leadership = 0
		case "stock":
			a.Offers = map[string]ArmyOffer{"model": {"native:20", 0}}
		}
		plan, er := originalRecruitPlanFor(c, a, "model")
		must(er)
		want := map[string]uint16{"rank": 0x5533, "slots": 0x5574, "gold": 0x55a0, "leadership": 0x5774, "stock": 0x55f0}[name]
		if plan.Preflight != want {
			t.Fatal("preflight", name, plan)
		}
		if name == "stock" {
			route, er := plan.result(1, a.Gold)
			must(er)
			if route != 0x5699 {
				t.Fatal("stock")
			}
		}
	}
	m := makeMachine(0x5523, 0)
	_, err = x.execute(m, 0x5523)
	must(err)
	if m.CPU.IP != 0x55f0 || m.Read16(0x1e880+0xfef8) != 6000 {
		t.Fatal("Go max/ABI")
	}
	beforeToken := p.Current.Token
	beforeNative := bytes.Clone(p.Current.Bytes.Native)
	m = makeMachine(0x5689, 6000)
	_, err = x.execute(m, 0x5689)
	must(err)
	if m.CPU.IP != 0x55a0 || p.Current.Token != beforeToken {
		t.Fatal("wide price did not reject before commit")
	}
	for _, name := range []string{"code", "resource", "stock", "result", "four-digits"} {
		m = makeMachine(0x5689, 2500)
		switch name {
		case "code":
			m.Mem[0x1100+0x5523] ^= 1
		case "resource":
			m.Write16(0x1e880+0x4f8, 1)
		case "stock":
			m.Write16(0x1e880+0xff06, 7999)
		case "result":
			x.Value = 2499
		case "four-digits":
			m.Write16(0x1e880+0xfefc, 10000)
			m.CPU.R[dg.AX] = 10000
			x.Value = 10000
		}
		if _, er := x.execute(m, 0x5689); er == nil {
			t.Fatal("unsafe quantity accepted", name)
		}
		if p.Current.Token != beforeToken || !bytes.Equal(p.Current.Bytes.Native, beforeNative) {
			t.Fatal("rejection wrote save")
		}
	}
	m = makeMachine(0x5689, 2500)
	shadow := bytes.Clone(m.Mem[0x1edca:0x1ede2])
	_, err = x.execute(m, 0x5689)
	must(err)
	must(p.execute(m, 0x56ec, "commit"))
	if p.Purchases != 1 || p.Current.World.Army.Gold != 0 || p.Current.World.Army.Slots[0] != (ArmyStack{"native:20", 2500}) || !bytes.Equal(shadow, m.Mem[0x1edca:0x1ede2]) {
		t.Fatal("safe commit")
	}
	m.CPU.IP = 0x56ec
	if er := p.execute(m, 0x56ec, "commit"); er == nil {
		t.Fatal("duplicate commit accepted")
	}
	write := func(n string, v any) {
		b, er := json.MarshalIndent(v, "", "  ")
		must(er)
		must(os.WriteFile(filepath.Join(folder, n), append(b, '\n'), 0600))
	}
	write("receipt.json", map[string]any{"status": "passed-original-recruit-models", "models": models, "overflow_price": 12, "overflow_count": 6000, "true_cost": 72000, "native_low_word": uint16(72000 % 65536), "overflow_route": 0x55a0, "boundary_commit_count": 2500, "boundary_gold_after": 0, "rejections": []string{"rank", "slots", "gold", "leadership", "stock", "code", "resource", "result", "four-digits"}, "original_graphical_oracle": false})
}

func TestOriginalRecruitQuantityRuntime(t *testing.T) {
	work, root, c, cc := recruitQuantityCatalogs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("HD assets required")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "runtime-r1")
	must(os.Mkdir(folder, 0700))
	session := filepath.Join(folder, "session")
	must(importNativeProgress(root, root, session, filepath.Join(work, "inputs"), c, cc))
	store, snap, err := openProgressPair(session, c, cc)
	must(err)
	defer func() { store.Close() }()
	w := snap.World
	w.Army.Rules = "tactics"
	w.Army.Slots = [6]ArmyStack{{"native:01", 30}, {"openkb:wolf", 2}}
	w.Revision++
	snap, err = store.Commit(snap.Token, w)
	must(err)
	must(os.Mkdir(filepath.Join(folder, "initial-session"), 0700))
	for _, n := range []string{"gamedata.ay", "gamedata.ay.army.json"} {
		b, er := os.ReadFile(filepath.Join(session, n))
		must(er)
		must(os.WriteFile(filepath.Join(folder, "initial-session", n), b, 0600))
	}
	control := bytes.Clone(snap.Bytes.Native)
	for i := 0; i < 6; i++ {
		off := 12 + i*4
		kind, count := uint16(0), uint16(0)
		if i == 0 {
			kind = 1
			count = 36
		}
		binary.LittleEndian.PutUint16(control[off:], kind+uint16(off+3))
		binary.LittleEndian.PutUint16(control[off+2:], count+uint16(off+5))
	}
	frames := map[string][]byte{}
	reports := []map[string]any{}
	for side := 0; side < 2; side++ {
		scratch := filepath.Join(folder, fmt.Sprintf("scratch-%d", side))
		must(os.Mkdir(scratch, 0700))
		raw := control
		if side == 1 {
			raw = snap.Bytes.Native
		}
		must(os.WriteFile(filepath.Join(scratch, "gamedata.ay"), raw, 0600))
		e, er := game.Open(game.Options{Root: root, Assets: assets, Saves: scratch, HD: true})
		must(er)
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
		ready, mapReady, shopReady := false, false, false
		e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { ready = e.PAMLoaded })
		e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
		e.Oracle.OnCall(oracle.Far(0x110, 0x4ea6), func(*oracle.Oracle) { shopReady = true })
		advance(1000)
		press(2)
		press(2)
		advance(1000)
		press(1)
		for n := 0; !ready && n < 2000; n++ {
			advance(10)
		}
		if !ready {
			t.Fatal("main menu")
		}
		press(0x1c)
		for n := 0; !mapReady && n < 2000; n++ {
			advance(10)
		}
		if !mapReady {
			t.Fatal("Continue map")
		}
		var p *worldArmyPort
		var x *originalRecruitQuantity
		if side == 1 {
			p, err = installWorldArmyPort(e, store, snap)
			must(err)
			x, err = installOriginalRecruitQuantity(e, p)
			must(err)
		}
		shadow := e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		// Reuse the already verified GUI route, including its ordinary F1/Esc
		// return boundaries. Two early movement pulses alone are insufficient.
		for _, movement := range []byte{0x4b, 0x48} {
			press(movement)
			e.Frame()
			advance(300)
			if shopReady {
				break
			}
			press(0x3b)
			e.Frame()
			advance(300)
			if shopReady {
				break
			}
			press(1)
			e.Frame()
			advance(300)
		}
		if !shopReady {
			press(0x48)
		}
		for n := 0; !shopReady && n < 500; n++ {
			advance(10)
		}
		if !shopReady {
			f, _ := os.Create(filepath.Join(folder, fmt.Sprintf("side-%d-entry-failed.png", side)))
			png.Encode(f, e.Frame())
			f.Close()
			t.Fatal("normal camp entry", e.Oracle.Regs(), e.Oracle.Word(oracle.Far(0x1e88, 0x8e12)), e.Oracle.Word(oracle.Far(0x1e88, 0x8e44)))
		}
		capture := func(name string) {
			t.Helper()
			advance(100)
			im := e.Frame()
			if side == 0 {
				frames[name] = bytes.Clone(im.Pix)
			} else if !bytes.Equal(frames[name], im.Pix) {
				t.Fatal("original shop frame differs", name)
			}
			f, er := os.Create(filepath.Join(folder, fmt.Sprintf("side-%d-%s.png", side, name)))
			must(er)
			must(png.Encode(f, im))
			must(f.Close())
		}
		capture("prompt")
		press(2)
		press(3)
		capture("editing-12")
		press(0x0e)
		capture("editing-1")
		press(3)
		press(4)
		press(5)
		capture("editing-1234")
		press(6)
		capture("ignored-fifth")
		press(1)
		advance(300)
		if side == 1 && p.Purchases != 0 {
			t.Fatal("cancel purchased")
		}
		// Walk away and enter the same native camp again; no IP/RAM injection.
		shopReady = false
		press(0x50)
		press(0x48)
		for n := 0; !shopReady && n < 500; n++ {
			advance(10)
		}
		if !shopReady {
			t.Fatal("revisit camp")
		}
		capture("reopened")
		press(2)
		capture("confirm-1")
		press(0x1c)
		advance(500)
		if side == 1 {
			if p.Purchases != 1 || p.Current.World.Army.Slots[0] != (ArmyStack{"native:01", 31}) || p.Current.World.Army.Slots[1] != (ArmyStack{"openkb:wolf", 2}) || p.Current.World.Army.Gold != 499 || !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
				t.Fatal("Go purchase/shadow", p.Current.World.Army)
			}
			rec, er := decodeCampRecord(p.Current.Bytes.Native, 0, 1)
			must(er)
			if rec.Words[4] != 2999 {
				t.Fatal("stock", rec)
			}
			reports = append(reports, map[string]any{"state": x.State(), "world": p.Current.World, "native_shadow_hex": fmt.Sprintf("%x", shadow)})
		}
		e.Close()
	}
	finalSnap, err := store.Recover()
	must(err)
	store.Close()
	reopened, cold, err := openProgressPair(session, c, cc)
	must(err)
	store = reopened
	if worldDigest(cold.World) != worldDigest(finalSnap.World) {
		t.Fatal("cold world")
	}
	b, err := json.MarshalIndent(map[string]any{"status": "passed-original-recruit-quantity-runtime", "controlled_army": true, "control_equivalent_used_leadership": 36, "go_initial_army": snap.World.Army, "frames_equal": len(frames), "reports": reports, "cold_world_equal": true, "initial_world": snap.World, "final_world": cold.World, "full_guest_state_parity_claimed": false}, "", "  ")
	must(err)
	must(os.WriteFile(filepath.Join(folder, "receipt.json"), append(b, '\n'), 0600))
}
