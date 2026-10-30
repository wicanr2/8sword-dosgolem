//go:build ignore

package main

import (
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func battleFixture(t *testing.T) (ArmyCatalog, game.OwnedCombatCatalog, OwnedWorld, string) {
	t.Helper()
	root := os.Getenv("EIGHTSWORD_BATTLE_UI_INPUT")
	if root == "" {
		t.Fatal("real inputs required")
	}
	var c ArmyCatalog
	var cc game.OwnedCombatCatalog
	var w OwnedWorld
	for _, v := range []struct {
		N string
		V any
	}{{"army-catalog.json", &c}, {"combat-catalog.json", &cc}, {"seed-world.json", &w}} {
		b, e := os.ReadFile(filepath.Join(root, v.N))
		if e != nil {
			t.Fatal(e)
		}
		if e = strictJSON(b, v.V); e != nil {
			t.Fatal(e)
		}
	}
	dir := t.TempDir()
	base, e := os.ReadFile(filepath.Join(root, "original-save.ay"))
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(dir, "gamedata.ay"), base, 0600); e != nil {
		t.Fatal(e)
	}
	return c, cc, w, dir
}
func TestBattleUIFullChainAndColdActions(t *testing.T) {
	c, cc, w, dir := battleFixture(t)
	u, e := openBattleUI(dir, c, cc, w)
	if e != nil {
		t.Fatal(e)
	}
	defer func() { u.Close() }()
	must := func(n string) {
		t.Helper()
		if e := u.action(n); e != nil {
			t.Fatalf("%s: %v", n, e)
		}
	}
	if e = u.action("begin"); e == nil {
		t.Fatal("empty army battle")
	}
	must("recruit")
	must("begin")
	if e = u.action("round"); e == nil {
		t.Fatal("early round")
	}
	must("enemy")
	saved := u.SavedSHA
	mid := u.World
	u.Close()
	u, e = openBattleUI(dir, c, cc, w)
	if e != nil {
		t.Fatal(e)
	}
	if !reflect.DeepEqual(mid, u.World) || saved != u.SavedSHA {
		t.Fatal("cold differs")
	}
	if e = u.action("enemy"); e == nil || u.SavedSHA != saved {
		t.Fatal("enemy repeated")
	}
	must("attack")
	for u.World.Battle.State.Result == "" && u.World.Battle.State.Round < 40 {
		must("round")
		must("enemy")
		if u.World.Battle.State.Result == "" {
			must("attack")
		}
	}
	if u.World.Battle.State.Result != "win" {
		t.Fatal("no victory")
	}
	must("settle")
	after := u.World
	if after.Army.Slots[0].Count != 29 || after.Army.Gold != 4400 || after.Progress.Merit != 2012 || after.Progress.Rank != 2 || after.Army.Leadership != 1100 || after.Army.Offers["wolf-camp"].Stock != 970 {
		t.Fatal(after)
	}
	saved = u.SavedSHA
	if e = u.action("settle"); e == nil || saved != u.SavedSHA {
		t.Fatal("double reward")
	}
	u.Close()
	u, e = openBattleUI(dir, c, cc, w)
	if e != nil || !reflect.DeepEqual(after, u.World) {
		t.Fatal("final cold", e)
	}
	if engine, e := game.Open(game.Options{Root: "/unmounted-original", Saves: dir, HD: true}); engine != nil || !errors.Is(e, game.ErrOwnedArmyHandoffPending) {
		t.Fatal("DOS guard bypassed", e)
	}
}
func TestBattleUIRejectsChangedSaveAndSecondWindow(t *testing.T) {
	c, cc, w, dir := battleFixture(t)
	u, e := openBattleUI(dir, c, cc, w)
	if e != nil {
		t.Fatal(e)
	}
	defer u.Close()
	if v, e := openBattleUI(dir, c, cc, w); e == nil {
		v.Close()
		t.Fatal("second UI")
	}
	before := worldDigest(u.World)
	p := filepath.Join(dir, "gamedata.ay.army.json")
	b, _ := os.ReadFile(p)
	os.WriteFile(p, append(b, ' '), 0600)
	if e = u.action("recruit"); e == nil || worldDigest(u.World) != before {
		t.Fatal("changed save accepted")
	}
	os.WriteFile(p, b, 0600)
	base := filepath.Join(dir, "gamedata.ay")
	raw, _ := os.ReadFile(base)
	raw[0] ^= 1
	os.WriteFile(base, raw, 0600)
	if e = u.action("recruit"); e == nil || worldDigest(u.World) != before {
		t.Fatal("changed base accepted")
	}
}
func TestBattleUISixSlotsAndRealGlyphBounds(t *testing.T) {
	c, cc, w, dir := battleFixture(t)
	u, e := openBattleUI(dir, c, cc, w)
	if e != nil {
		t.Fatal(e)
	}
	defer u.Close()
	if e = u.action("recruit"); e != nil {
		t.Fatal(e)
	}
	if e = u.action("begin"); e != nil {
		t.Fatal(e)
	}
	beforePass := u.SavedSHA
	if e = u.action("pass"); e == nil || beforePass != u.SavedSHA {
		t.Fatal("front-row pass accepted or saved")
	}
	f, e := loadArmyUIFonts(os.Getenv("EIGHTSWORD_BATTLE_UI_ASSETS"))
	if e != nil {
		t.Fatal(e)
	}
	u.Target = 5
	u.handle("attack")
	for _, ch := range u.Message {
		if _, ok := f.Glyphs[ch]; !ok {
			t.Fatalf("missing core error glyph %U", ch)
		}
	}
	u.Target = 0
	seen := map[string]bool{}
	for _, id := range []string{"noto", "lishu", "caoshu"} {
		u.Font = id
		im, fields := paintBattleUI(u, f)
		seen[contentSHA(im.Pix)] = true
		for _, v := range fields {
			if v.Ellipsized {
				t.Fatal("unexpected truncation", v)
			}
			if v.Ink[2] > v.Ink[0] && (v.Ink[0] < v.Rect[0] || v.Ink[2] > v.Rect[2] || v.Ink[1] < v.Rect[1] || v.Ink[3] > v.Rect[3]) {
				t.Fatal(v)
			}
		}
	}
	if len(seen) != 3 {
		t.Fatal("same fonts")
	}
	u.Message = "x 🧭"
	_, fields := paintBattleUI(u, f)
	for _, field := range fields {
		if field.Role == "message" && field.Text != "x ?" {
			t.Fatal("unknown error glyph fallback", field.Text)
		}
	}
	for side := 0; side < 2; side++ {
		for slot := 0; slot < 6; slot++ {
			r := battleCard(side, slot)
			action := battleHit(u, (r.Min.X+r.Max.X)/2, (r.Min.Y+r.Max.Y)/2)
			if action == "" {
				t.Fatal("card unreachable")
			}
		}
	}
	u.Source = 6
	if _, e = u.playerPlan(); e == nil {
		t.Fatal("source bounds")
	}
	u.Source = 0
	u.Target = 5
	if _, e = u.playerPlan(); e == nil {
		t.Fatal("empty target")
	}
	raw, _ := json.Marshal(u.World)
	var copy OwnedWorld
	if e = strictJSON(raw, &copy); e != nil {
		t.Fatal(e)
	}
}
