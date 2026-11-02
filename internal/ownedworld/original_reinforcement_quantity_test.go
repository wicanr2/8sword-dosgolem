package ownedworld

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
)

func TestOriginalReinforcementQuantityRuntime(t *testing.T) {
	work, root, c, cc := recruitQuantityCatalogs(t)
	assets := os.Getenv("EIGHTSWORD_TEST_SOURCE_ASSETS")
	if assets == "" {
		t.Skip("real HD assets required")
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	folder := filepath.Join(work, "reinforcement-runtime-r1")
	must(os.Mkdir(folder, 0700))
	session := filepath.Join(folder, "session")
	must(os.Mkdir(session, 0700))
	for _, n := range []string{"gamedata.ay", "gamedata.ay.army.json"} {
		b, err := os.ReadFile(filepath.Join(work, "initial-session", n))
		must(err)
		must(os.WriteFile(filepath.Join(session, n), b, 0600))
	}
	store, initial, err := openProgressPair(session, c, cc)
	must(err)
	defer func() { store.Close() }()
	scratch := filepath.Join(folder, "scratch")
	must(os.Mkdir(scratch, 0700))
	must(os.WriteFile(filepath.Join(scratch, "gamedata.ay"), initial.Bytes.Native, 0600))
	e, err := game.Open(game.Options{Root: root, Assets: assets, Saves: scratch, HD: true})
	must(err)
	defer e.Close()
	e.Oracle.SetClock(12, 0, 0, 0)
	e.EnableLiveClock(3000)
	var ui *reinforcementUI
	advance := func(ms int) {
		t.Helper()
		for n := 0; n < ms; n += 10 {
			if ui != nil {
				must(ui.quantity().advance(&armyReviewApp{Engine: e}))
			}
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
	ready, mapReady := false, false
	e.Oracle.OnCall(oracle.Far(0x110, 0x55a), func(*oracle.Oracle) { ready = e.PAMLoaded })
	e.Oracle.OnCall(oracle.Far(0x110, 0xb62), func(*oracle.Oracle) { mapReady = e.PAMLoaded })
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
		t.Fatal("Continue")
	}
	p, err := installWorldArmyPort(e, store, initial)
	must(err)
	q, err := installOriginalRecruitQuantity(e, p)
	must(err)
	v, err := installOriginalArmyReview(e, p)
	must(err)
	_, err = installOriginalArmyDismiss(e, p, v)
	must(err)
	fonts, err := loadArmyUIFonts(filepath.Join(work, "ui-assets"))
	must(err)
	hdUnitArt = loadHDUnitArtwork(e, filepath.Join(work, "ui-assets"), fonts.CatalogRawSHA)
	v.Fields = newOriginalArmyFields(v, fonts, hdUnitArt)
	must(installRecruitIcons(e))
	ui = &reinforcementUI{Engine: e, Port: p, Count: 1, Blocked: map[byte]bool{}}
	installOriginalReinforcementQuantity(ui)
	shadow := bytes.Clone(e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24))
	for _, movement := range []byte{0x4b, 0x48} {
		press(movement)
		e.Frame()
		advance(300)
		if ui.ready() {
			break
		}
		press(0x3b)
		e.Frame()
		advance(300)
		if ui.ready() {
			break
		}
		press(1)
		e.Frame()
		advance(300)
	}
	if !ui.ready() {
		press(0x48)
	}
	for n := 0; !ui.ready() && n < 500; n++ {
		advance(10)
	}
	if !ui.ready() {
		t.Fatal("normal camp entry")
	}
	models := []map[string]any{}
	modelArmy := p.Current.World.Army
	modelArmy.Gold = 30000
	modelArmy.Leadership = 30000
	modelArmy.RecruitRank = 5
	bound, err := bindReinforcementWorld(p.Current, c, p.ShopGroup, p.ShopRow)
	must(err)
	modelArmy.Offers = bound.Army.Offers
	for _, id := range openKBArtIDs {
		key := reinforcementKey(p.ShopGroup, p.ShopRow, p.ShopKind, id)
		plan, er := originalReinforcementPlanFor(c, modelArmy, key)
		must(er)
		if plan.Unit != id || plan.Preflight != 0x55f0 {
			t.Fatal("extension model", id, plan)
		}
		for _, n := range []uint32{0, 1, 2, 9999} {
			next, er := plan.result(n, modelArmy.Gold)
			must(er)
			want := uint16(0x56ec)
			switch {
			case n == 0:
				want = 0x555f
			case n > plan.Stock || uint64(n) > plan.Limit:
				want = 0x5699
			case uint64(n)*plan.Price > modelArmy.Gold:
				want = 0x55a0
			}
			if next != want {
				t.Fatal("extension route", id, n, next, want)
			}
		}
		models = append(models, map[string]any{"unit": id, "price": plan.Price, "command": plan.Command, "used": plan.Used, "limit": plan.Limit, "stock": plan.Stock})
	}
	for _, name := range []string{"native-rules", "native-product", "unknown-product"} {
		a := modelArmy
		key := reinforcementKey(p.ShopGroup, p.ShopRow, p.ShopKind, "openkb:wolf")
		switch name {
		case "native-rules":
			a.Rules = "native"
			a.Slots = [6]ArmyStack{{"native:01", 30}}
		case "native-product":
			key = p.ShopID
		case "unknown-product":
			key = "reinforce:00:01:01:unknown"
		}
		if _, er := originalReinforcementPlanFor(c, a, key); er == nil {
			t.Fatal("unsafe model accepted", name)
		}
	}
	for _, name := range []string{"rank", "slots", "gold", "leadership", "stock"} {
		a := modelArmy
		id := "openkb:wolf"
		if name == "rank" {
			id = "openkb:drag"
			a.RecruitRank = 0
		}
		key := reinforcementKey(p.ShopGroup, p.ShopRow, p.ShopKind, id)
		switch name {
		case "slots":
			a.Slots = [6]ArmyStack{{"native:01", 1}, {"native:02", 1}, {"native:03", 1}, {"native:04", 1}, {"native:05", 1}, {"native:06", 1}}
		case "gold":
			a.Gold = 0
		case "leadership":
			a.Leadership = 0
			a.Slots = [6]ArmyStack{}
		case "stock":
			a.Offers = map[string]ArmyOffer{key: {Unit: id, Stock: 0}}
		}
		plan, er := originalReinforcementPlanFor(c, a, key)
		must(er)
		want := map[string]uint16{"rank": 0x5533, "slots": 0x5574, "gold": 0x55a0, "leadership": 0x5774, "stock": 0x55f0}[name]
		if plan.Preflight != want {
			t.Fatal("extension preflight", name, plan)
		}
		if name == "stock" {
			next, er := plan.result(1, a.Gold)
			must(er)
			if next != 0x5699 {
				t.Fatal("extension stock gate")
			}
		}
	}
	start := func() {
		t.Helper()
		must(ui.open())
		ui.Paint(fonts, e.FontID())
		must(ui.buy())
		advance(500)
		if ui.quantity().Phase != "input" || !ui.quantity().Ready || !q.InputPending || q.Plan.Unit != "openkb:wolf" || q.Plan.Limit != 21 {
			t.Fatal("original editor restart", ui.State(), q.State())
		}
	}
	images := []string{}
	capture := func(name string) {
		t.Helper()
		im, texts := ui.Paint(fonts, e.FontID())
		for _, text := range texts {
			r := text.Rect
			if !image.Rect(r[0], r[1], r[2], r[3]).In(im.Bounds()) {
				t.Fatal("text outside canvas", text)
			}
		}
		f, er := os.OpenFile(filepath.Join(folder, name+".png"), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		must(er)
		must(png.Encode(f, im))
		must(f.Close())
		images = append(images, name)
	}
	revisit := func() {
		t.Helper()
		press(0x50)
		press(0x48)
		for n := 0; !ui.ready() && n < 500; n++ {
			advance(10)
		}
		if !ui.ready() {
			t.Fatal("revisit")
		}
	}
	start()
	capture("wolf-prompt")
	before := p.Current
	press(2)
	press(3)
	capture("wolf-12")
	press(0x0e)
	capture("wolf-1")
	press(3)
	press(4)
	press(5)
	capture("wolf-1234")
	press(6)
	capture("wolf-ignore-fifth")
	if got := e.Oracle.Bytes(oracle.Far(0x1e88, 0x8dbc), 5); !bytes.Equal(got, []byte{'1', '2', '3', '4', 0}) {
		t.Fatal("four digit editor", got)
	}
	press(1)
	advance(400)
	if p.Current.Token != before.Token || ui.quantity().Purchases != 0 {
		t.Fatal("cancel changed save")
	}
	revisit()
	start()
	for i := 0; i < 4; i++ {
		press(10)
	}
	press(0x1c)
	capture("wolf-too-many")
	if p.Current.Token != before.Token || ui.quantity().Purchases != 0 {
		t.Fatal("invalid quantity changed save")
	}
	press(0x1c)
	advance(300)
	revisit()
	start()
	must(e.SetFont("lishu"))
	capture("wolf-lishu")
	press(3)
	capture("wolf-confirm-2")
	x := ui.quantity()
	token := x.Token
	x.Token = "stale"
	if _, er := x.plan(p.Current); er == nil {
		t.Fatal("stale accepted")
	}
	x.Token = token
	press(0x1c)
	advance(500)
	if x.Purchases != 1 || p.Purchases != 0 || p.Current.World.Army.Gold != 420 || p.Current.World.Army.Slots[0] != (ArmyStack{"native:01", 30}) || p.Current.World.Army.Slots[1] != (ArmyStack{"openkb:wolf", 4}) {
		t.Fatal("extension purchase", p.Current.World.Army, x.Events)
	}
	if !bytes.Equal(shadow, e.Oracle.Bytes(oracle.Far(0x1e88, 0x54a), 24)) {
		t.Fatal("native army written")
	}
	rec, err := decodeCampRecord(p.Current.Bytes.Native, 0, 1)
	must(err)
	if rec.Words[4] != 3000 {
		t.Fatal("native stock consumed")
	}
	key := reinforcementKey(0, 1, 1, "openkb:wolf")
	if p.Current.World.Army.Offers[key].Stock != 73 {
		t.Fatal("independent stock")
	}
	if _, er := x.plan(p.Current); er == nil {
		t.Fatal("committed transaction reused")
	}
	for i, n := range pairWorldResources(p.Current.World).words() {
		if uint64(e.Oracle.Word(oracle.Far(0x1e88, 0x4f2+uint16(i*2)))) != n {
			t.Fatal("projected resource")
		}
	}
	final, err := store.Recover()
	must(err)
	store.Close()
	store, cold, err := openProgressPair(session, c, cc)
	must(err)
	if worldDigest(cold.World) != worldDigest(final.World) {
		t.Fatal("cold world")
	}
	write := func(name string, value any) {
		b, er := json.MarshalIndent(value, "", "  ")
		must(er)
		must(os.WriteFile(filepath.Join(folder, name), append(b, '\n'), 0600))
	}
	write("receipt.json", map[string]any{"status": "passed-original-reinforcement-quantity-runtime", "controlled_army": true, "normal_camp_entry": true, "models": models, "images": images, "initial_world": initial.World, "before_purchase_world": before.World, "final_world": cold.World, "cancel_unchanged": true, "invalid_unchanged": true, "cold_world_equal": true, "native_stock": rec.Words[4], "native_shadow_hex": fmt.Sprintf("%x", shadow), "events": x.Events, "native_purchases": p.Purchases})
}
