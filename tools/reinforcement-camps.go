//go:build ignore

// Approved A. Independent camp stock never enters the guest unit tables.
package main

import (
	"bytes"
	"errors"
	"fmt"
	"math"
	"reflect"
	"strings"
)

func reinforcementKey(g, r int, kind uint16, id string) string {
	return fmt.Sprintf("reinforce:%02d:%02d:%02d:%s", g, r, kind, strings.TrimPrefix(id, "openkb:"))
}
func parseReinforcementKey(k string) (g, r int, kind uint16, id string, e error) {
	var n int
	var suffix string
	if _, e = fmt.Sscanf(k, "reinforce:%02d:%02d:%02d:%s", &g, &r, &n, &suffix); e != nil {
		return
	}
	kind = uint16(n)
	id = "openkb:" + suffix
	if g < 0 || g >= 5 || r < 0 || r >= 24 || n < 1 || n > 25 || k != reinforcementKey(g, r, kind, id) {
		e = errors.New("reinforcement key domain")
		return
	}
	for _, v := range openKBArtIDs {
		if id == v {
			return
		}
	}
	e = errors.New("reinforcement unit domain")
	return
}
func reinforcementOffers(a OwnedArmy) map[string]ArmyOffer {
	v := map[string]ArmyOffer{}
	for k, o := range a.Offers {
		if strings.HasPrefix(k, "reinforce:") {
			v[k] = o
		}
	}
	return v
}
func validateReinforcements(native []byte, a OwnedArmy, c ArmyCatalog) error {
	groups := map[string]int{}
	for k, o := range reinforcementOffers(a) {
		g, r, kind, id, e := parseReinforcementKey(k)
		if e != nil {
			return e
		}
		rec, e := decodeCampRecord(native, g, r)
		if e != nil || rec.Words[3] != kind || o.Unit != id {
			return errors.New("reinforcement source binding")
		}
		groups[campKey(g, r)]++
	}
	for _, n := range groups {
		if n != len(openKBArtIDs) {
			return errors.New("incomplete reinforcement camp")
		}
	}
	return nil
}
func bindReinforcementWorld(b progressPairSnapshot, c ArmyCatalog, g, r int) (OwnedWorld, error) {
	w := cloneCampWorld(b.World)
	if w.Battle != nil || w.Revision == math.MaxUint64 {
		return w, errors.New("reinforcement battle/revision")
	}
	if e := validateReinforcements(b.Bytes.Native, w.Army, c); e != nil {
		return w, e
	}
	rec, e := decodeCampRecord(b.Bytes.Native, g, r)
	if e != nil || rec.Words[3] == 0 {
		return w, errors.New("reinforcement original camp")
	}
	idx, e := c.index()
	if e != nil {
		return w, e
	}
	old, ok := idx[rec.unit()]
	if !ok || old.Gold == 0 {
		return w, errors.New("reinforcement native price")
	}
	if _, ok = w.Army.Offers[reinforcementKey(g, r, rec.Words[3], openKBArtIDs[0])]; ok {
		return w, nil
	}
	for _, id := range openKBArtIDs {
		u, ok := idx[id]
		if !ok || u.Gold == 0 || u.NativeKind != 0 || u.Origin == "native" {
			return w, errors.New("reinforcement catalog")
		}
		stock := uint64(rec.Words[4]) * old.Gold / u.Gold
		if stock > math.MaxUint32 {
			return w, errors.New("reinforcement stock overflow")
		}
		w.Army.Offers[reinforcementKey(g, r, rec.Words[3], id)] = ArmyOffer{id, uint32(stock)}
	}
	w.Revision++
	return w, w.Army.validate(c)
}
func (s *progressPairStore) BindReinforcements(token string, g, r int) (progressPairSnapshot, error) {
	b, e := s.Recover()
	if e != nil {
		return b, e
	}
	if token == "" || token != b.Token {
		return b, errors.New("stale reinforcement token")
	}
	w, e := bindReinforcementWorld(b, s.Catalog, g, r)
	if e != nil {
		return b, e
	}
	if w.Revision == b.World.Revision {
		return b, nil
	}
	return s.commitResumeBytes(token, w, nil, nil, nil)
}
func (s *progressPairStore) RecruitReinforcement(token, key string, count uint32) (progressPairSnapshot, error) {
	b, e := s.Recover()
	if e != nil {
		return b, e
	}
	if token == "" || token != b.Token || b.World.Battle != nil || b.World.Revision == math.MaxUint64 {
		return b, errors.New("reinforcement stale/battle/revision")
	}
	if _, _, _, _, e = parseReinforcementKey(key); e != nil {
		return b, e
	}
	if b.World.Army.Rules == "native" {
		return b, errors.New("reinforcement requires owned rules")
	}
	w := cloneCampWorld(b.World)
	w.Army, _, e = w.Army.recruit(s.Catalog, key, count)
	if e != nil {
		return b, e
	}
	w.Revision++
	return s.commitResumeBytes(token, w, nil, nil, nil)
}
func checkReinforcementTransition(b, a progressPairSnapshot, c ArmyCatalog) (bool, error) {
	old, next := reinforcementOffers(b.World.Army), reinforcementOffers(a.World.Army)
	if reflect.DeepEqual(old, next) {
		return false, nil
	}
	fail := func() (bool, error) { return true, errors.New("noncanonical reinforcement transition") }
	if b.World.Battle != nil || a.World.Battle != nil || b.World.Revision == math.MaxUint64 || a.World.Revision != b.World.Revision+1 {
		return fail()
	}
	var changed []string
	var added []string
	for k, v := range old {
		n, ok := next[k]
		if !ok || n.Unit != v.Unit || n.Stock > v.Stock {
			return fail()
		}
		if n != v {
			changed = append(changed, k)
		}
	}
	for k := range next {
		if _, ok := old[k]; !ok {
			added = append(added, k)
		}
	}
	w := cloneCampWorld(b.World)
	var e error
	if len(added) == 8 && len(changed) == 0 {
		g, r, _, _, err := parseReinforcementKey(added[0])
		if err != nil {
			return true, err
		}
		w, e = bindReinforcementWorld(b, c, g, r)
	} else if len(added) == 0 && len(changed) == 1 && w.Army.Rules != "native" {
		k := changed[0]
		w.Army, _, e = w.Army.recruit(c, k, old[k].Stock-next[k].Stock)
		w.Revision++
	} else {
		return fail()
	}
	if e != nil {
		return true, e
	}
	if worldDigest(w) != worldDigest(a.World) {
		return fail()
	}
	return true, nil
}
func refillReinforcements(a *OwnedArmy, native []byte, c ArmyCatalog, pam []byte) error {
	offers := reinforcementOffers(*a)
	if len(offers) == 0 {
		return nil
	}
	if e := validateReinforcements(native, *a, c); e != nil {
		return e
	}
	caps, e := monthlyCaps(pam)
	if e != nil {
		return e
	}
	idx, e := c.index()
	if e != nil {
		return e
	}
	for k, o := range offers {
		g, r, _, id, _ := parseReinforcementKey(k)
		rec, e := decodeCampRecord(native, g, r)
		if e != nil {
			return e
		}
		u, ok := idx[id]
		old, ok2 := idx[rec.unit()]
		if !ok || !ok2 || u.Gold == 0 {
			return errors.New("monthly reinforcement profile")
		}
		cap := uint64(caps[g*24+r]) * old.Gold / u.Gold
		n := uint64(o.Stock)
		add := n / 10
		if add < 10 {
			add = 10
		}
		n += add
		if n > cap {
			n = cap
		}
		if n > math.MaxUint32 {
			return errors.New("monthly reinforcement overflow")
		}
		o.Stock = uint32(n)
		a.Offers[k] = o
	}
	return nil
}
func sameReinforcementNative(a, b []byte) bool {
	return len(a) == 2987 && len(b) == 2987 && bytes.Equal(a[12:1236], b[12:1236])
}
