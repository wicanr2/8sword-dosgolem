package eightsword

import (
	"bytes"
	"encoding/json"
	"math"
	"os"
	"reflect"
	"testing"
)

func ownedCombatFixture(t *testing.T) (OwnedCombatCatalog, OwnedCombatState) {
	t.Helper()
	c := OwnedCombatCatalog{Schema: "eightsword-owned-combat-catalog/1", Profiles: map[string]OwnedCombatProfile{}}
	for _, p := range []OwnedCombatProfile{
		{ID: "native:01", NativeKind: 1, Attack: 30, HP: 25},
		{ID: "native:03", NativeKind: 3, Attack: 40, HP: 40, Ranged: true},
		{ID: "native:25", NativeKind: 25, Attack: 60, HP: 120},
		{ID: "openkb:wolf", Attack: 1, HP: 3}, {ID: "openkb:skel", Attack: 1, HP: 3},
	} {
		c.Profiles[p.ID] = p
	}
	var rows [2][6]OwnedCombatStack
	rows[0][0] = OwnedCombatStack{Unit: "openkb:wolf", Count: 30}
	rows[1][0] = OwnedCombatStack{Unit: "openkb:skel", Count: 15}
	s, err := NewOwnedCombat(c, rows, OwnedCombatConfig{Rules: "tactics", Divisors: [2]uint32{5, 5}, Multipliers: [2]uint32{1, 1}}, hash([]byte("army")))
	if err != nil {
		t.Fatal(err)
	}
	return c, s
}
func TestOwnedCombatIndependentIDCountsAndWriteback(t *testing.T) {
	c, s := ownedCombatFixture(t)
	before := s
	s, v, err := s.Apply(c, OwnedCombatAction{Side: 1, Source: 0, Target: 0, Kind: "normal"})
	if err != nil || v.Loss != 1 || s.Rows[0][0].Count != 29 {
		t.Fatal(v, err)
	}
	if before.Rows[0][0].Count != 30 {
		t.Fatal("input mutated")
	}
	for s.Result == "" && s.Round < 40 {
		if !s.Acted[0][0] {
			a, e := s.Choose(c, 0, 0, "normal", 0, 0)
			if e != nil {
				t.Fatal(e)
			}
			s, _, err = s.Apply(c, a.Action)
			if err != nil {
				t.Fatal(err)
			}
		}
		if s.Result != "" {
			break
		}
		if !s.Acted[1][0] {
			s, _, err = s.Apply(c, OwnedCombatAction{Side: 1, Source: 0, Target: 0, Kind: "normal"})
			if err != nil {
				t.Fatal(err)
			}
		}
		if s.Result == "" {
			s, err = s.NextRound(c)
			if err != nil {
				t.Fatal(err)
			}
		}
	}
	if s.Result != "win" || s.Rows[0][0].Count != 29 {
		t.Fatal("wrong complete combat", s)
	}
	if _, _, err = s.Commit(c, hash([]byte("another army"))); err == nil {
		t.Fatal("stale army accepted")
	}
	done, survivors, err := s.Commit(c, s.ArmySHA)
	if err != nil || survivors[0].Unit != "openkb:wolf" || survivors[0].Count != 29 {
		t.Fatal(err, survivors)
	}
	if _, _, err = done.Commit(c, s.ArmySHA); err == nil {
		t.Fatal("duplicate battle writeback accepted")
	}
	strength, err := done.Strength(c, 0)
	if err != nil || strength.Units != 29 || strength.BaseHP != 87 {
		t.Fatal(strength, err)
	}
}
func TestOwnedCombatRejectsBeforeMutation(t *testing.T) {
	c, s := ownedCombatFixture(t)
	for _, slot := range []int{-1, 0, 5, 6, 25, 65535} {
		for _, field := range []string{"source", "target", "side"} {
			a := OwnedCombatAction{Side: 0, Source: 0, Target: 0, Kind: "normal"}
			switch field {
			case "source":
				a.Source = slot
			case "target":
				a.Target = slot
			case "side":
				a.Side = slot
			}
			input := s
			after, _, err := s.Apply(c, a)
			if slot == 0 {
				if err != nil {
					t.Fatal("valid zero slot rejected", field, err)
				}
				continue
			}
			if field == "side" && slot == 1 {
				continue
			}
			if err == nil || after != input {
				t.Fatal("invalid action mutated state", field, slot, err)
			}
		}
	}
	for _, name := range []string{"unknown", "zero-hp", "zero-power", "kind-26", "zero-divisor", "zero-multiplier", "bad-schema", "bad-source", "bad-initial", "invented-count", "unknown-action"} {
		t.Run(name, func(t *testing.T) {
			c, s := ownedCombatFixture(t)
			profiles := map[string]OwnedCombatProfile{}
			for k, v := range c.Profiles {
				profiles[k] = v
			}
			c.Profiles = profiles
			a := OwnedCombatAction{Side: 0, Source: 0, Target: 0, Kind: "normal"}
			switch name {
			case "unknown":
				s.Rows[0][0].Unit = "missing"
				s.Initial[0][0].Unit = "missing"
			case "zero-hp", "zero-power", "kind-26":
				p := c.Profiles["openkb:wolf"]
				if name == "zero-hp" {
					p.HP = 0
				} else if name == "zero-power" {
					p.Attack = 0
				} else {
					p.NativeKind = 26
				}
				c.Profiles[p.ID] = p
				s.CatalogSHA = c.Digest()
			case "zero-divisor":
				s.Config.Divisors[0] = 0
			case "zero-multiplier":
				s.Config.Multipliers[0] = 0
			case "bad-schema":
				s.Schema = "future"
			case "bad-source":
				s.CatalogSHA = hash([]byte("another catalog"))
			case "bad-initial":
				s.Initial[0][0].Unit = "native:01"
			case "invented-count":
				s.Rows[0][0].Count++
			case "unknown-action":
				a.Kind = "spell-unowned"
			}
			before := s
			after, _, err := s.Apply(c, a)
			if err == nil || after != before {
				t.Fatal("invalid state/action accepted or changed", err)
			}
		})
	}
	a := OwnedCombatAction{Side: 0, Source: 0, Target: 0, Kind: "normal"}
	once, _, err := s.Apply(c, a)
	if err != nil {
		t.Fatal(err)
	}
	if twice, _, err := once.Apply(c, a); err == nil || twice != once {
		t.Fatal("duplicate action changed state")
	}
	if _, err = s.NextRound(c); err == nil {
		t.Fatal("unfinished round advanced")
	}
}
func TestOwnedCombatLargeCountsAndOverflow(t *testing.T) {
	c, s := ownedCombatFixture(t)
	s.Rows[0][0].Count = 1000000
	s.Initial = s.Rows
	next, v, err := s.Apply(c, OwnedCombatAction{Side: 0, Source: 0, Target: 0, Kind: "normal"})
	if err != nil || v.Damage != 200000 || v.Loss != 15 || next.Rows[0][0].Count != 1000000 {
		t.Fatal("large count truncated", v, err)
	}
	for _, percent := range []uint64{75, 80} {
		got := ownedScale(math.MaxUint64, percent)
		want := (math.MaxUint64/100)*percent + (math.MaxUint64%100)*percent/100
		if got != want || got == 0 {
			t.Fatal("wide scaling overflow")
		}
	}
	c, s = ownedCombatFixture(t)
	p := c.Profiles["openkb:wolf"]
	p.Attack = math.MaxUint32
	p.HP = math.MaxUint32
	c.Profiles[p.ID] = p
	s.CatalogSHA = c.Digest()
	for i := range s.Rows[0] {
		s.Rows[0][i] = OwnedCombatStack{Unit: p.ID, Count: math.MaxUint32}
	}
	s.Initial = s.Rows
	if err = s.Validate(c); err == nil {
		t.Fatal("overflowing aggregate accepted")
	}
}
func TestOwnedCombatSnapshotShapes(t *testing.T) {
	c, s := ownedCombatFixture(t)
	raw, err := json.Marshal(s)
	if err != nil {
		t.Fatal(err)
	}
	loaded, err := DecodeOwnedCombatState(raw)
	if err != nil || loaded != s || loaded.Validate(c) != nil {
		t.Fatal("snapshot round-trip", err)
	}
	for _, name := range []string{"short", "long", "side25", "missing", "missing-count", "null-acted", "duplicate", "unknown-field", "trailing"} {
		var doc map[string]any
		if err = json.Unmarshal(raw, &doc); err != nil {
			t.Fatal(err)
		}
		switch name {
		case "short":
			doc["rows"].([]any)[0] = doc["rows"].([]any)[0].([]any)[:5]
		case "long":
			doc["rows"].([]any)[0] = append(doc["rows"].([]any)[0].([]any), map[string]any{"unit": "openkb:wolf", "count": 100})
		case "side25":
			doc["rows"] = make([]any, 25)
		case "missing":
			delete(doc, "acted")
		case "missing-count":
			delete(doc["rows"].([]any)[0].([]any)[0].(map[string]any), "count")
		case "null-acted":
			doc["acted"].([]any)[0].([]any)[0] = nil
		case "unknown-field":
			doc["new-index"] = 25
		}
		bad, _ := json.Marshal(doc)
		if name == "duplicate" {
			bad = bytes.Replace(bad, []byte(`"round":1`), []byte(`"round":1,"round":2`), 1)
		}
		if name == "trailing" {
			bad = append(bad, []byte("{}")...)
		}
		if _, err = DecodeOwnedCombatState(bad); err == nil {
			t.Fatal("malformed snapshot accepted", name)
		}
	}
}
func TestOwnedCombatMatchesNativeControls(t *testing.T) {
	path := os.Getenv("EIGHTSWORD_OWNED_COMBAT_CONTROLS")
	if path == "" {
		t.Skip("需要已保存原版控制")
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var controls struct {
		Catalog OwnedCombatCatalog `json:"catalog"`
		Cases   []struct {
			Name           string                 `json:"name"`
			Rows           [2][6]OwnedCombatStack `json:"rows"`
			Config         OwnedCombatConfig      `json:"config"`
			Action         OwnedCombatAction      `json:"action"`
			ExpectedLoss   uint32                 `json:"expected_loss"`
			Preferred      int                    `json:"preferred"`
			ExpectedChoice int                    `json:"expected_choice"`
		} `json:"cases"`
	}
	if err = json.Unmarshal(raw, &controls); err != nil || len(controls.Cases) != 15 {
		t.Fatal("native control count", err)
	}
	for _, v := range controls.Cases {
		t.Run(v.Name, func(t *testing.T) {
			s, err := NewOwnedCombat(controls.Catalog, v.Rows, v.Config, hash([]byte(v.Name)))
			if err != nil {
				t.Fatal(err)
			}
			_, out, err := s.Apply(controls.Catalog, v.Action)
			if err != nil || out.Loss != v.ExpectedLoss {
				t.Fatal("native casualty differs", out, err)
			}
			choice, err := s.Choose(controls.Catalog, v.Action.Side, v.Action.Source, v.Action.Kind, v.Action.Selector, v.Preferred)
			if err != nil || choice.Action.Target != v.ExpectedChoice {
				t.Fatal("native AI choice differs", choice, err)
			}
			copy, err := DecodeOwnedCombatState(mustOwnedCombatJSON(t, s))
			if err != nil || !reflect.DeepEqual(copy, s) {
				t.Fatal(err)
			}
		})
	}
}
func mustOwnedCombatJSON(t *testing.T, s OwnedCombatState) []byte {
	t.Helper()
	b, e := json.Marshal(s)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
