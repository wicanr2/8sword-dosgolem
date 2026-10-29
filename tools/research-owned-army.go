//go:build ignore

// 030 DRAFT: disposable Go-owned army/recruitment/save prototype.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"strings"
)

type UnitProfile struct {
	ID                 string   `json:"id"`
	Name               string   `json:"name"`
	Origin             string   `json:"origin"`
	NativeKind         uint16   `json:"native_kind,omitempty"`
	Gold               uint64   `json:"gold"`
	Command            uint64   `json:"command"`
	Rank               uint32   `json:"rank"`
	ReferenceAbilities []string `json:"reference_abilities,omitempty"`
}
type ArmyCatalog struct {
	Schema    string            `json:"schema"`
	Profiles  []UnitProfile     `json:"profiles"`
	SourceSHA map[string]string `json:"source_sha256"`
}
type ArmyStack struct {
	Unit  string `json:"unit"`
	Count uint32 `json:"count"`
}
type ArmyOffer struct {
	Unit  string `json:"unit"`
	Stock uint32 `json:"stock"`
}

func (s *ArmyStack) UnmarshalJSON(raw []byte) error {
	var v struct {
		Unit  *string `json:"unit"`
		Count *uint32 `json:"count"`
	}
	if err := strictJSON(raw, &v); err != nil {
		return err
	}
	if v.Unit == nil || v.Count == nil {
		return errors.New("missing stack fields")
	}
	s.Unit = *v.Unit
	s.Count = *v.Count
	return nil
}
func (o *ArmyOffer) UnmarshalJSON(raw []byte) error {
	var v struct {
		Unit  *string `json:"unit"`
		Stock *uint32 `json:"stock"`
	}
	if err := strictJSON(raw, &v); err != nil {
		return err
	}
	if v.Unit == nil || v.Stock == nil {
		return errors.New("missing offer fields")
	}
	o.Unit = *v.Unit
	o.Stock = *v.Stock
	return nil
}

type OwnedArmy struct {
	Gold        uint64               `json:"gold"`
	Leadership  uint64               `json:"leadership"`
	RecruitRank uint32               `json:"recruit_rank"`
	Rules       string               `json:"rules"`
	Slots       [6]ArmyStack         `json:"slots"`
	Offers      map[string]ArmyOffer `json:"offers"`
}

func (a *OwnedArmy) UnmarshalJSON(raw []byte) error {
	var v struct {
		Gold        *uint64              `json:"gold"`
		Leadership  *uint64              `json:"leadership"`
		RecruitRank *uint32              `json:"recruit_rank"`
		Rules       *string              `json:"rules"`
		Slots       *[]ArmyStack         `json:"slots"`
		Offers      map[string]ArmyOffer `json:"offers"`
	}
	if err := strictJSON(raw, &v); err != nil {
		return err
	}
	if v.Gold == nil || v.Leadership == nil || v.RecruitRank == nil || v.Rules == nil || v.Slots == nil || len(*v.Slots) != 6 || v.Offers == nil {
		return errors.New("missing army fields or six-slot shape")
	}
	a.Gold = *v.Gold
	a.Leadership = *v.Leadership
	a.RecruitRank = *v.RecruitRank
	a.Rules = *v.Rules
	a.Offers = v.Offers
	copy(a.Slots[:], *v.Slots)
	return nil
}

type ArmySave struct {
	Schema      string    `json:"schema"`
	OriginalSHA string    `json:"original_sha256"`
	CatalogSHA  string    `json:"catalog_sha256"`
	Army        OwnedArmy `json:"army"`
}
type ArmyQuote struct {
	Slot    int    `json:"slot"`
	Maximum uint32 `json:"maximum"`
	Reason  string `json:"reason,omitempty"`
}
type RecruitReceipt struct {
	Offer string `json:"offer"`
	Unit  string `json:"unit"`
	Slot  int    `json:"slot"`
	Count uint32 `json:"count"`
	Spent uint64 `json:"spent"`
}

func contentSHA(raw []byte) string { h := sha256.Sum256(raw); return hex.EncodeToString(h[:]) }
func validSHA(s string) bool {
	b, e := hex.DecodeString(s)
	return e == nil && len(b) == 32 && strings.ToLower(s) == s
}
func strictJSON(raw []byte, dst any) error {
	if len(raw) > 1<<20 {
		return errors.New("JSON size limit")
	}
	keys := json.NewDecoder(bytes.NewReader(raw))
	keys.UseNumber()
	var walk func() error
	walk = func() error {
		token, err := keys.Token()
		if err != nil {
			return err
		}
		if delimiter, ok := token.(json.Delim); ok {
			switch delimiter {
			case '{':
				seen := map[string]bool{}
				for keys.More() {
					key, err := keys.Token()
					if err != nil {
						return err
					}
					name, ok := key.(string)
					if !ok || seen[name] {
						return errors.New("duplicate JSON key")
					}
					seen[name] = true
					if err = walk(); err != nil {
						return err
					}
				}
			case '[':
				for keys.More() {
					if err = walk(); err != nil {
						return err
					}
				}
			default:
				return errors.New("unexpected JSON delimiter")
			}
			_, err = keys.Token()
			return err
		}
		return nil
	}
	if err := walk(); err != nil {
		return err
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(dst); err != nil {
		return err
	}
	var extra any
	if err := d.Decode(&extra); err != io.EOF {
		return errors.New("trailing JSON")
	}
	return nil
}
func (c ArmyCatalog) index() (map[string]UnitProfile, error) {
	if c.Schema != "eightsword-owned-catalog/1" || len(c.Profiles) == 0 || len(c.Profiles) > 256 {
		return nil, errors.New("catalog schema/count")
	}
	result := make(map[string]UnitProfile, len(c.Profiles))
	for _, u := range c.Profiles {
		if len(u.ID) > 80 || u.Name == "" || u.Gold == 0 || u.Command == 0 || u.Gold > 1e9 || u.Command > 1e9 || u.Rank > 100 {
			return nil, errors.New("invalid profile")
		}
		if _, ok := result[u.ID]; ok {
			return nil, errors.New("duplicate unit ID")
		}
		if u.Origin == "native" {
			if u.NativeKind < 1 || u.NativeKind > 25 || u.ID != fmt.Sprintf("native:%02d", u.NativeKind) {
				return nil, errors.New("native identity")
			}
		} else if u.Origin == "openkb-reference-prototype" {
			if u.NativeKind != 0 || !strings.HasPrefix(u.ID, "openkb:") || len(u.ID) <= 7 {
				return nil, errors.New("extension identity")
			}
		} else {
			return nil, errors.New("unknown origin")
		}
		result[u.ID] = u
	}
	for _, h := range c.SourceSHA {
		if !validSHA(h) {
			return nil, errors.New("source SHA")
		}
	}
	return result, nil
}
func (c ArmyCatalog) digest() string { raw, _ := json.Marshal(c); return contentSHA(raw) }
func (a OwnedArmy) validate(c ArmyCatalog) error {
	idx, err := c.index()
	if err != nil {
		return err
	}
	if a.Rules != "native" && a.Rules != "formation" && a.Rules != "tactics" {
		return errors.New("unknown rules")
	}
	if a.Offers == nil || len(a.Offers) > 1024 || a.RecruitRank > 100 {
		return errors.New("army bounds")
	}
	seen := map[string]bool{}
	var used uint64
	for _, s := range a.Slots {
		if s.Unit == "" && s.Count == 0 {
			continue
		}
		u, ok := idx[s.Unit]
		if !ok || s.Count == 0 || seen[s.Unit] {
			return errors.New("unknown, empty or duplicate stack")
		}
		if a.Rules == "native" && u.Origin != "native" {
			return errors.New("extended units require owned rules; no silent native downgrade")
		}
		seen[s.Unit] = true
		cost := uint64(s.Count) * u.Command
		if used > math.MaxUint64-cost {
			return errors.New("leadership overflow")
		}
		used += cost
	}
	if used > a.Leadership {
		return errors.New("army over leadership limit")
	}
	for key, o := range a.Offers {
		if key == "" || len(key) > 120 {
			return errors.New("offer ID")
		}
		if _, ok := idx[o.Unit]; !ok {
			return errors.New("unknown offer unit")
		}
	}
	return nil
}
func (a OwnedArmy) quote(c ArmyCatalog, offerID string) (ArmyQuote, error) {
	if err := a.validate(c); err != nil {
		return ArmyQuote{}, err
	}
	o, ok := a.Offers[offerID]
	if !ok {
		return ArmyQuote{}, errors.New("unknown offer")
	}
	idx, _ := c.index()
	u := idx[o.Unit]
	q := ArmyQuote{Slot: -1}
	if u.Rank > a.RecruitRank {
		q.Reason = "rank"
		return q, nil
	}
	var used uint64
	for i, s := range a.Slots {
		if s.Unit == o.Unit {
			q.Slot = i
		}
		if s.Unit != "" {
			used += uint64(s.Count) * idx[s.Unit].Command
		}
	}
	if q.Slot < 0 {
		for i, s := range a.Slots {
			if s.Unit == "" {
				q.Slot = i
				break
			}
		}
	}
	if q.Slot < 0 {
		q.Reason = "slots"
		return q, nil
	}
	maximum := uint64(o.Stock)
	q.Reason = "stock"
	for _, limit := range []struct {
		Value  uint64
		Reason string
	}{
		{a.Gold / u.Gold, "gold"}, {(a.Leadership - used) / u.Command, "leadership"},
		{uint64(math.MaxUint32 - a.Slots[q.Slot].Count), "stack-limit"},
	} {
		if limit.Value < maximum {
			maximum = limit.Value
			q.Reason = limit.Reason
		}
	}
	q.Maximum = uint32(maximum)
	return q, nil
}
func (a OwnedArmy) recruit(c ArmyCatalog, offerID string, count uint32) (OwnedArmy, RecruitReceipt, error) {
	q, err := a.quote(c, offerID)
	if err != nil {
		return a, RecruitReceipt{}, err
	}
	if count == 0 || count > q.Maximum {
		return a, RecruitReceipt{}, fmt.Errorf("recruit refused: %s maximum=%d", q.Reason, q.Maximum)
	}
	idx, _ := c.index()
	offer := a.Offers[offerID]
	u := idx[offer.Unit]
	next := a
	next.Offers = make(map[string]ArmyOffer, len(a.Offers))
	for k, v := range a.Offers {
		next.Offers[k] = v
	}
	next.Gold -= uint64(count) * u.Gold
	next.Slots[q.Slot].Unit = u.ID
	next.Slots[q.Slot].Count += count
	offer.Stock -= count
	next.Offers[offerID] = offer
	if err := next.validate(c); err != nil {
		return a, RecruitReceipt{}, err
	}
	return next, RecruitReceipt{Offer: offerID, Unit: u.ID, Slot: q.Slot, Count: count, Spent: uint64(count) * u.Gold}, nil
}

// Separate, SHA-bound sidecar. The original 2987-byte file is never written.
// A crash between original-save and sidecar commit is detected at load.
func saveArmy(dir string, c ArmyCatalog, a OwnedArmy) error {
	if err := a.validate(c); err != nil {
		return err
	}
	original, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return err
	}
	if len(original) != 2987 {
		return errors.New("original save length")
	}
	data, err := json.MarshalIndent(ArmySave{Schema: "eightsword-owned-army/1", OriginalSHA: contentSHA(original), CatalogSHA: c.digest(), Army: a}, "", "  ")
	if err != nil {
		return err
	}
	f, err := os.CreateTemp(dir, ".owned-army-*.tmp")
	if err != nil {
		return err
	}
	name := f.Name()
	defer os.Remove(name)
	if _, err = f.Write(append(data, '\n')); err == nil {
		err = f.Sync()
	}
	closeErr := f.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	// Recheck the original before committing a sidecar for it.
	current, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return err
	}
	if !bytes.Equal(current, original) {
		return errors.New("original changed during sidecar write")
	}
	return os.Rename(name, filepath.Join(dir, "gamedata.ay.army.json"))
}
func loadArmy(dir string, c ArmyCatalog) (OwnedArmy, error) {
	f, err := os.Open(filepath.Join(dir, "gamedata.ay.army.json"))
	if err != nil {
		return OwnedArmy{}, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() > 1<<20 {
		return OwnedArmy{}, errors.New("sidecar size/type")
	}
	data, err := io.ReadAll(io.LimitReader(f, (1<<20)+1))
	if err != nil {
		return OwnedArmy{}, err
	}
	var saved ArmySave
	if err = strictJSON(data, &saved); err != nil {
		return OwnedArmy{}, err
	}
	original, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return OwnedArmy{}, err
	}
	if saved.Schema != "eightsword-owned-army/1" || len(original) != 2987 || saved.OriginalSHA != contentSHA(original) || saved.CatalogSHA != c.digest() {
		return OwnedArmy{}, errors.New("save binding or version mismatch")
	}
	if err = saved.Army.validate(c); err != nil {
		return OwnedArmy{}, err
	}
	return saved.Army, nil
}

func main() {
	catalogPath := flag.String("catalog", "", "prototype catalog")
	out := flag.String("out", "", "new output directory")
	loadDir := flag.String("load", "", "cold-process load from an existing prototype save")
	flag.Parse()
	check := func(err error) {
		if err != nil {
			panic(err)
		}
	}
	if *catalogPath == "" || *out == "" || os.Getuid() != 1000 {
		panic("explicit paths and UID1000")
	}
	if _, err := os.Stat(*out); !os.IsNotExist(err) {
		panic("output exists")
	}
	check(os.Mkdir(*out, 0755))
	raw, err := os.ReadFile(*catalogPath)
	check(err)
	var c ArmyCatalog
	check(strictJSON(raw, &c))
	_, err = c.index()
	check(err)
	if *loadDir != "" {
		army, err := loadArmy(*loadDir, c)
		check(err)
		encoded, err := json.MarshalIndent(map[string]any{"status": "passed-owned-army-cold-load", "production": false, "army": army, "catalog_sha256": c.digest()}, "", "  ")
		check(err)
		check(os.WriteFile(filepath.Join(*out, "receipt.json"), append(encoded, '\n'), 0644))
		fmt.Println("Restored all army and stock fields in a fresh process")
		return
	}
	a := OwnedArmy{Gold: 10000, Leadership: 10000, RecruitRank: 6, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	var receipts []RecruitReceipt
	for _, id := range []string{"native:01", "openkb:wolf", "openkb:skel", "openkb:troll", "openkb:vamp", "openkb:drag"} {
		a.Offers[id] = ArmyOffer{Unit: id, Stock: 20}
		next, receipt, err := a.recruit(c, id, 1)
		check(err)
		a = next
		receipts = append(receipts, receipt)
	}
	// Synthetic original bytes are clearly labeled, never a real player save.
	original := bytes.Repeat([]byte{0x5a}, 2987)
	check(os.WriteFile(filepath.Join(*out, "gamedata.ay"), original, 0600))
	check(saveArmy(*out, c, a))
	restored, err := loadArmy(*out, c)
	check(err)
	before, _ := json.Marshal(a)
	after, _ := json.Marshal(restored)
	if !bytes.Equal(before, after) {
		panic("save round-trip differs")
	}
	result := map[string]any{"status": "passed-owned-army-prototype", "production": false, "profiles": len(c.Profiles), "catalog_sha256": c.digest(), "receipts": receipts, "army": a, "save_roundtrip_equal": true, "original_sha256": contentSHA(original), "limits": []string{"Synthetic economy and original-save bytes; not a normal gameplay or native save receipt.", "OpenKB gold/HP/rank are reference values for a disposable prototype, not final game balance.", "Reference abilities are metadata only, not active combat traits.", "No original EXE or original type ID is overwritten; Go owns these transactions."}}
	encoded, err := json.MarshalIndent(result, "", "  ")
	check(err)
	check(os.WriteFile(filepath.Join(*out, "receipt.json"), append(encoded, '\n'), 0644))
	fmt.Println("Passed", len(receipts), "Go recruitment transactions and complete sidecar round-trip")
}
