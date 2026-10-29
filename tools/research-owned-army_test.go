//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func realCatalog(t *testing.T) ArmyCatalog {
	t.Helper()
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_OWNED_CATALOG"))
	if e != nil {
		t.Fatal(e)
	}
	var c ArmyCatalog
	if e = strictJSON(raw, &c); e != nil {
		t.Fatal(e)
	}
	if _, e = c.index(); e != nil {
		t.Fatal(e)
	}
	return c
}
func initial(c ArmyCatalog) OwnedArmy {
	a := OwnedArmy{Gold: 100000, Leadership: 10000, RecruitRank: 6, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	for _, p := range c.Profiles {
		a.Offers[p.ID] = ArmyOffer{Unit: p.ID, Stock: 100}
	}
	return a
}
func jsonBytes(v any) []byte { b, _ := json.Marshal(v); return b }

func TestOwnedRecruitmentAtomicAndLimits(t *testing.T) {
	c := realCatalog(t)
	for _, name := range []string{"zero", "stock", "gold", "leadership", "rank", "slots", "unknown", "duplicate", "invalid-profile"} {
		t.Run(name, func(t *testing.T) {
			a := initial(c)
			quantity := uint32(1)
			offer := "openkb:wolf"
			catalog := c
			switch name {
			case "zero":
				quantity = 0
			case "stock":
				quantity = 101
			case "gold":
				a.Gold = 0
			case "leadership":
				a.Leadership = 0
			case "rank":
				a.RecruitRank = 0
			case "slots":
				for i := range a.Slots {
					a.Slots[i] = ArmyStack{Unit: c.Profiles[i].ID, Count: 1}
				}
			case "unknown":
				offer = "missing"
			case "duplicate":
				a.Slots[0] = ArmyStack{Unit: "native:01", Count: 1}
				a.Slots[1] = a.Slots[0]
			case "invalid-profile":
				catalog.Profiles = append([]UnitProfile(nil), c.Profiles...)
				catalog.Profiles[0].Gold = 0
			}
			before := jsonBytes(a)
			result, _, err := a.recruit(catalog, offer, quantity)
			if err == nil || !bytes.Equal(before, jsonBytes(a)) || !bytes.Equal(before, jsonBytes(result)) {
				t.Fatal("failed recruitment changed state", err)
			}
		})
	}
	a := initial(c)
	for i := range a.Slots {
		a.Slots[i] = ArmyStack{Unit: c.Profiles[i].ID, Count: 1}
	}
	before := jsonBytes(a)
	next, r, err := a.recruit(c, "native:01", 2)
	if err != nil || r.Slot != 0 || next.Slots[0].Count != 3 || !bytes.Equal(before, jsonBytes(a)) {
		t.Fatal("full army must merge without changing input", r, err)
	}
	first, _, err := initial(c).recruit(c, "openkb:wolf", 2)
	if err != nil {
		t.Fatal(err)
	}
	split, _, err := first.recruit(c, "openkb:wolf", 3)
	if err != nil {
		t.Fatal(err)
	}
	combined, _, err := initial(c).recruit(c, "openkb:wolf", 5)
	if err != nil || !reflect.DeepEqual(split, combined) {
		t.Fatal("partitioned transaction differs")
	}
}

func TestOwnedSaveRoundtripAndBrokenBinding(t *testing.T) {
	c := realCatalog(t)
	a := initial(c)
	a, _, _ = a.recruit(c, "openkb:troll", 2)
	a, _, _ = a.recruit(c, "native:01", 3)
	dir := t.TempDir()
	original := bytes.Repeat([]byte{0x5a}, 2987)
	path := filepath.Join(dir, "gamedata.ay")
	if e := os.WriteFile(path, original, 0600); e != nil {
		t.Fatal(e)
	}
	if e := saveArmy(dir, c, a); e != nil {
		t.Fatal(e)
	}
	b, err := loadArmy(dir, c)
	if err != nil || !reflect.DeepEqual(a, b) {
		t.Fatal("sidecar round-trip", err)
	}
	actual, _ := os.ReadFile(path)
	if !bytes.Equal(actual, original) {
		t.Fatal("original save changed")
	}
	side := filepath.Join(dir, "gamedata.ay.army.json")
	valid, _ := os.ReadFile(side)
	for _, name := range []string{"schema", "catalog", "original", "unknown-unit", "unknown-rules", "short-slots", "long-slots", "missing-offers", "missing-count", "missing-stock", "duplicate-stock", "trailing", "unknown-field", "truncated", "oversized"} {
		t.Run(name, func(t *testing.T) {
			var doc map[string]any
			if e := json.Unmarshal(valid, &doc); e != nil {
				t.Fatal(e)
			}
			state := doc["army"].(map[string]any)
			raw := valid
			catalog := c
			switch name {
			case "schema":
				doc["schema"] = "future"
			case "catalog":
				catalog.Profiles = append([]UnitProfile(nil), c.Profiles...)
				catalog.Profiles[0].Gold++
			case "original":
				doc["original_sha256"] = "bad"
			case "unknown-unit":
				state["slots"].([]any)[0].(map[string]any)["unit"] = "missing"
			case "unknown-rules":
				state["rules"] = "future"
			case "short-slots":
				state["slots"] = state["slots"].([]any)[:5]
			case "long-slots":
				state["slots"] = append(state["slots"].([]any), map[string]any{"unit": "", "count": 0})
			case "missing-offers":
				delete(state, "offers")
			case "missing-count":
				delete(state["slots"].([]any)[0].(map[string]any), "count")
			case "missing-stock":
				for _, v := range state["offers"].(map[string]any) {
					delete(v.(map[string]any), "stock")
					break
				}
			case "unknown-field":
				state["discarded-state"] = true
			}
			if name != "trailing" && name != "truncated" && name != "oversized" {
				raw = jsonBytes(doc)
			}
			if name == "trailing" {
				raw = append(append([]byte{}, valid...), []byte("{}")...)
			}
			if name == "duplicate-stock" {
				raw = bytes.Replace(raw, []byte(`"stock":100`), []byte(`"stock":100,"stock":0`), 1)
			}
			if name == "truncated" {
				raw = valid[:len(valid)/2]
			}
			if name == "oversized" {
				raw = bytes.Repeat([]byte{' '}, 1<<20+1)
			}
			if e := os.WriteFile(side, raw, 0600); e != nil {
				t.Fatal(e)
			}
			if _, e := loadArmy(dir, catalog); e == nil {
				t.Fatal("accepted broken save")
			}
		})
	}
	if e := os.WriteFile(side, valid, 0600); e != nil {
		t.Fatal(e)
	}
	original[0]++
	if e := os.WriteFile(path, original, 0600); e != nil {
		t.Fatal(e)
	}
	if _, e := loadArmy(dir, c); e == nil {
		t.Fatal("accepted sidecar for another original save")
	}
	if _, e := os.Stat(filepath.Join(dir, ".owned-army.tmp")); !os.IsNotExist(e) {
		t.Fatal("unexpected fixed temp path")
	}
	left, _ := filepath.Glob(filepath.Join(dir, ".owned-army-*.tmp"))
	if len(left) > 0 {
		t.Fatal("temporary saves left behind")
	}
}

func TestOwnedNativeHelperControls(t *testing.T) {
	c := realCatalog(t)
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_OWNED_NATIVE"))
	if e != nil {
		t.Fatal(e)
	}
	var result struct {
		Cases []struct {
			Kind     uint16   `json:"kind"`
			Army     []uint16 `json:"army"`
			Weight   uint16   `json:"leadership_per_unit"`
			Capacity uint16   `json:"capacity"`
			Used     uint16   `json:"used_leadership"`
		} `json:"helper_cases"`
	}
	if e = json.Unmarshal(raw, &result); e != nil || len(result.Cases) != 75 {
		t.Fatal("missing native controls", e)
	}
	idx, _ := c.index()
	for _, v := range result.Cases {
		profile := idx["native:"+twoDigits(v.Kind)]
		if profile.Command != uint64(v.Weight) {
			t.Fatal("native weight differs", v.Kind)
		}
		capacity := false
		var used uint64
		for i := 0; i < 6; i++ {
			kind, count := v.Army[i*2], v.Army[i*2+1]
			capacity = capacity || kind == 0 || kind == v.Kind
			if kind != 0 {
				used += uint64(count) * idx["native:"+twoDigits(kind)].Command
			}
		}
		if capacity != (v.Capacity == 1) || uint16(used) != v.Used {
			t.Fatal("native capacity/leadership differs", v)
		}
	}
}
func TestOwnedNormalPurchaseAndOriginalSaveBinding(t *testing.T) {
	c := realCatalog(t)
	raw, e := os.ReadFile(os.Getenv("EIGHTSWORD_OWNED_NATIVE"))
	if e != nil {
		t.Fatal(e)
	}
	type frame struct {
		Army       []uint16 `json:"army"`
		Gold       uint64   `json:"gold"`
		Leadership uint64   `json:"leadership"`
	}
	var native struct {
		Before, After frame
		Records       []struct {
			Kind  uint16 `json:"kind"`
			Stock uint32 `json:"stock"`
		} `json:"normal_records"`
	}
	if e = json.Unmarshal(raw, &native); e != nil || len(native.Records) == 0 {
		t.Fatal("normal receipt", e)
	}
	a := OwnedArmy{Gold: native.Before.Gold, Leadership: native.Before.Leadership, RecruitRank: 6, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	for i := 0; i < 6; i++ {
		if kind := native.Before.Army[i*2]; kind != 0 {
			a.Slots[i] = ArmyStack{Unit: "native:" + twoDigits(kind), Count: uint32(native.Before.Army[i*2+1])}
		}
	}
	id := "native:" + twoDigits(native.Records[0].Kind)
	a.Offers[id] = ArmyOffer{Unit: id, Stock: native.Records[0].Stock}
	b, _, err := a.recruit(c, id, 1)
	if err != nil || b.Gold != native.After.Gold {
		t.Fatal("normal purchase balance differs", err)
	}
	for i, s := range b.Slots {
		if s.Count != uint32(native.After.Army[i*2+1]) {
			t.Fatal("normal purchase count differs")
		}
	}
	b.Offers["openkb:wolf"] = ArmyOffer{Unit: "openkb:wolf", Stock: 20}
	b, _, err = b.recruit(c, "openkb:wolf", 2)
	if err != nil {
		t.Fatal(err)
	}
	original, err := os.ReadFile(os.Getenv("EIGHTSWORD_OWNED_ORIGINAL_SAVE"))
	if err != nil || len(original) != 2987 {
		t.Fatal("actual original save required", err)
	}
	dir := t.TempDir()
	if err = os.WriteFile(filepath.Join(dir, "gamedata.ay"), original, 0600); err != nil {
		t.Fatal(err)
	}
	if err = saveArmy(dir, c, b); err != nil {
		t.Fatal(err)
	}
	loaded, err := loadArmy(dir, c)
	if err != nil || !reflect.DeepEqual(b, loaded) {
		t.Fatal("extended state not restored", err)
	}
	loaded.Rules = "native"
	if err = loaded.validate(c); err == nil {
		t.Fatal("silently downgraded an extended army")
	}
}
func twoDigits(n uint16) string { return string([]byte{'0' + byte(n/10), '0' + byte(n%10)}) }
