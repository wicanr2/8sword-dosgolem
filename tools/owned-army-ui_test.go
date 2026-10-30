package main

import (
	"encoding/json"
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"image"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func uiFixture(t *testing.T) (ArmyCatalog, *armyUIStore, *armyUI) {
	t.Helper()
	raw, e := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_ARMY_UI_INPUT"), "army-catalog.json"))
	if e != nil {
		t.Fatal(e)
	}
	var c ArmyCatalog
	if e = strictJSON(raw, &c); e != nil {
		t.Fatal(e)
	}
	dir := t.TempDir()
	raw, e = os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_ARMY_UI_INPUT"), "original-save.ay"))
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(dir, "gamedata.ay"), raw, 0600); e != nil {
		t.Fatal(e)
	}
	s, a, e := openArmyUIStore(dir, c, freshArmyUI(c))
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(s.Close)
	u, e := newArmyUI(c, s, a)
	if e != nil {
		t.Fatal(e)
	}
	return c, s, u
}
func TestArmyUIRecruitPersistsAndColdLoads(t *testing.T) {
	c, s, u := uiFixture(t)
	u.handle("select:offer:openkb:wolf")
	u.handle("quantity")
	u.text("30")
	if !u.canRecruit() {
		t.Fatal("wolf recruitment disabled")
	}
	if e := u.recruit(); e != nil {
		t.Fatal(e)
	}
	if u.Army.Gold != 3800 || u.Army.Slots[0] != (ArmyStack{Unit: "openkb:wolf", Count: 30}) || u.Army.Offers[u.Selected].Stock != 970 {
		t.Fatal("transaction differs")
	}
	q, e := u.quote()
	if e != nil || q.Maximum != 95 {
		t.Fatal("current gold limit", q, e)
	}
	before := worldUIHash(u.Army)
	saved := s.SavedSHA
	u.Quantity = "96"
	if e = u.recruit(); e == nil || worldUIHash(u.Army) != before || s.SavedSHA != saved {
		t.Fatal("over-limit transaction")
	}
	u.Quantity = "0"
	if u.canRecruit() {
		t.Fatal("zero quantity")
	}
	u.Quantity = "4294967296"
	if u.canRecruit() {
		t.Fatal("overflow quantity")
	}
	if e = u.setRules("native"); e == nil || u.Army.Rules != "tactics" || s.SavedSHA != saved {
		t.Fatal("new unit silently entered native rules")
	}
	if e = u.setRules("formation"); e != nil {
		t.Fatal(e)
	}
	if _, _, e = openArmyUIStore(s.Dir, c, freshArmyUI(c)); e == nil {
		t.Fatal("second window accepted")
	}
	if engine, e := game.Open(game.Options{Root: "/unmounted-original", Saves: s.Dir, HD: true}); engine != nil || !errors.Is(e, game.ErrOwnedArmyHandoffPending) {
		t.Fatal("formal Engine did not isolate UI progress", e)
	}
	before = worldUIHash(u.Army)
	s.Close()
	s2, a, e := openArmyUIStore(s.Dir, c, freshArmyUI(c))
	if e != nil {
		t.Fatal(e)
	}
	defer s2.Close()
	if worldUIHash(a) != before {
		t.Fatal("cold load differs")
	}
}
func worldUIHash(v any) string { raw, _ := json.Marshal(v); return contentSHA(raw) }

func TestArmyUISixSlotsAndInputRules(t *testing.T) {
	c, s, u := uiFixture(t)
	u.handle("all")
	used := map[string]bool{}
	for _, p := range c.Profiles {
		if len(used) == 6 {
			break
		}
		u.Selected = "offer:" + p.ID
		u.Quantity = "1"
		q, e := u.quote()
		if e != nil {
			t.Fatal(e)
		}
		if q.Maximum == 0 {
			continue
		}
		if e = u.recruit(); e != nil {
			t.Fatal(e)
		}
		used[p.ID] = true
	}
	if len(used) != 6 {
		t.Fatal("fixture did not fill six slots")
	}
	before := worldUIHash(u.Army)
	saved := s.SavedSHA
	for _, p := range c.Profiles {
		if used[p.ID] || p.Rank > u.Army.RecruitRank {
			continue
		}
		u.Selected = "offer:" + p.ID
		q, e := u.quote()
		if e != nil || q.Reason != "slots" || q.Maximum != 0 {
			t.Fatal(q, e)
		}
		if e = u.recruit(); e == nil || worldUIHash(u.Army) != before || saved != s.SavedSHA {
			t.Fatal("seventh stack accepted")
		}
		break
	}
	u.Quantity = "1"
	u.handle("quantity")
	u.text("0030abc")
	if u.Quantity != "0030" {
		t.Fatal("numeric edit")
	}
	u.handle("backspace")
	if u.Quantity != "003" {
		t.Fatal("backspace")
	}
	u.handle("clear")
	u.text("4294967295123")
	if len(u.Quantity) != 10 {
		t.Fatal("unbounded input")
	}
	u.NewOnly = true
	u.selectFirst()
	u.handle("next")
	if u.Page != 1 || len(u.pageOffers()) != 2 {
		t.Fatal("new-unit paging")
	}
	u.handle("next")
	if u.Page != 1 {
		t.Fatal("page bound")
	}
	u.handle("prev")
	if u.Page != 0 {
		t.Fatal("page previous")
	}
	if uiHit(u, 1190, 320) != "select:"+u.pageOffers()[0] {
		t.Fatal("hit mapping")
	}
}

func TestArmyUIStaleFilesDoNotCommit(t *testing.T) {
	_, s, u := uiFixture(t)
	u.Selected = "offer:openkb:wolf"
	u.Quantity = "30"
	before := worldUIHash(u.Army)
	target := filepath.Join(s.Dir, "gamedata.ay.army.json")
	saved, e := os.ReadFile(target)
	if e != nil {
		t.Fatal(e)
	}
	basePath := filepath.Join(s.Dir, "gamedata.ay")
	base, e := os.ReadFile(basePath)
	if e != nil {
		t.Fatal(e)
	}
	changed := append([]byte(nil), base...)
	changed[0] ^= 1
	os.WriteFile(basePath, changed, 0600)
	if e = u.recruit(); e == nil || worldUIHash(u.Army) != before {
		t.Fatal("changed base accepted")
	}
	actual, _ := os.ReadFile(target)
	if !reflect.DeepEqual(saved, actual) {
		t.Fatal("base failure changed sidecar")
	}
	os.WriteFile(basePath, base, 0600)
	other := []byte(`{"schema":"eightsword-owned-encounter-save/1"}`)
	os.WriteFile(target, other, 0600)
	if e = u.recruit(); e == nil || worldUIHash(u.Army) != before {
		t.Fatal("stale file accepted")
	}
	actual, _ = os.ReadFile(target)
	if !reflect.DeepEqual(other, actual) {
		t.Fatal("foreign schema overwritten")
	}
	s.Close()
	if _, _, e = openArmyUIStore(s.Dir, u.Catalog, freshArmyUI(u.Catalog)); e == nil {
		t.Fatal("foreign schema loaded as roster")
	}
	if _, e = os.Stat(filepath.Join(s.Dir, ".owned-army-ui.lock")); !os.IsNotExist(e) {
		t.Fatal("failed constructor leaked lock")
	}
}

func TestArmyUIActualFontsAndTextBounds(t *testing.T) {
	c, _, _ := uiFixture(t)
	fonts, e := loadArmyUIFonts(os.Getenv("EIGHTSWORD_ARMY_UI_ASSETS"))
	if e != nil {
		t.Fatal(e)
	}
	c.Profiles = append([]UnitProfile(nil), c.Profiles...)
	c.Profiles[0].Name = strings.Repeat(c.Profiles[0].Name, 40)
	a := freshArmyUI(c)
	a.Gold = math.MaxUint64
	a.Leadership = math.MaxUint64
	a.Slots[0] = ArmyStack{Unit: "native:01", Count: math.MaxUint32}
	u, e := newArmyUI(c, nil, a)
	if e != nil {
		t.Fatal(e)
	}
	seen := map[string]bool{}
	for _, id := range []string{"noto", "lishu", "caoshu"} {
		u.Font = id
		frame, fields := paintArmyUI(u, fonts)
		if frame.Bounds() != image.Rect(0, 0, 1920, 1200) {
			t.Fatal("canvas")
		}
		digest := contentSHA(frame.Pix)
		if seen[digest] {
			t.Fatal("fonts did not change actual frame")
		}
		seen[digest] = true
		longName := false
		fullCount := false
		for _, f := range fields {
			r := image.Rect(f.Rect[0], f.Rect[1], f.Rect[2], f.Rect[3])
			ink := image.Rect(f.Ink[0], f.Ink[1], f.Ink[2], f.Ink[3])
			if !r.In(frame.Bounds()) || (!ink.Empty() && !ink.In(r)) {
				t.Fatal(id, f)
			}
			if f.Role == "slot-0-name" {
				longName = f.Ellipsized
			}
			if f.Role == "slot-0-count" {
				fullCount = strings.Contains(f.Text, "4294967295") && !f.Ellipsized
			}
			if (f.Role == "gold" || f.Role == "leadership") && f.Ellipsized {
				t.Fatal("full numeric value truncated")
			}
		}
		if !longName || !fullCount {
			t.Fatal("name/count policies not exercised", id)
		}
	}
}

func TestArmyUIExistingOfferIDsAndEmptyMarket(t *testing.T) {
	c, _, _ := uiFixture(t)
	a := freshArmyUI(c)
	a.Offers = map[string]ArmyOffer{"next": {Unit: "openkb:wolf", Stock: 10}}
	u, e := newArmyUI(c, nil, a)
	if e != nil {
		t.Fatal(e)
	}
	u.handle("select:next")
	if u.Selected != "next" {
		t.Fatal("offer ID collided with UI action")
	}
	q, e := u.quote()
	if e != nil || q.Maximum != 10 {
		t.Fatal(q, e)
	}
	a.Offers = map[string]ArmyOffer{}
	u, e = newArmyUI(c, nil, a)
	if e != nil || u.canRecruit() {
		t.Fatal("empty market", e)
	}
	fonts, e := loadArmyUIFonts(os.Getenv("EIGHTSWORD_ARMY_UI_ASSETS"))
	if e != nil {
		t.Fatal(e)
	}
	paintArmyUI(u, fonts)
}
