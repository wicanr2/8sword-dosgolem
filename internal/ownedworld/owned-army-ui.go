// 030 DRAFT: interactive army ownership prototype; no guest or Engine reference.
package ownedworld

import (
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

type armyUIStore struct {
	Dir, OriginalSHA, SavedSHA string
	Catalog                    ArmyCatalog
	locked                     bool
}

func openArmyUIStore(dir string, c ArmyCatalog, initial OwnedArmy) (*armyUIStore, OwnedArmy, error) {
	var empty OwnedArmy
	st, err := os.Stat(dir)
	if err != nil || !st.IsDir() {
		return nil, empty, errors.New("存檔目錄不存在")
	}
	regular := func(path string, limit int64) error {
		s, e := os.Lstat(path)
		if e != nil {
			return e
		}
		if !s.Mode().IsRegular() || s.Size() > limit {
			return errors.New("存檔不是有效的一般檔案")
		}
		return nil
	}
	if err = regular(filepath.Join(dir, "gamedata.ay"), 2987); err != nil {
		return nil, empty, err
	}
	base, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil || len(base) != 2987 {
		return nil, empty, errors.New("基底進度長度不符")
	}
	lock := filepath.Join(dir, ".owned-army-ui.lock")
	if err = os.Mkdir(lock, 0700); err != nil {
		return nil, empty, errors.New("此進度已由另一個視窗開啟，或留有未處理的鎖")
	}
	s := &armyUIStore{Dir: dir, OriginalSHA: contentSHA(base), Catalog: c, locked: true}
	army := initial
	target := filepath.Join(dir, "gamedata.ay.army.json")
	if _, err = os.Lstat(target); err == nil {
		if err = regular(target, 1<<20); err == nil {
			army, err = loadArmy(dir, c)
		}
		if err != nil {
			s.Close()
			return nil, empty, errors.New("軍隊進度無法讀取，保留原檔")
		}
		raw, e := os.ReadFile(target)
		if e != nil {
			s.Close()
			return nil, empty, e
		}
		s.SavedSHA = contentSHA(raw)
	} else if !os.IsNotExist(err) {
		s.Close()
		return nil, empty, err
	} else {
		if err = s.Save(initial); err != nil {
			s.Close()
			return nil, empty, err
		}
	}
	return s, army, nil
}
func (s *armyUIStore) Close() {
	if s != nil && s.locked {
		os.Remove(filepath.Join(s.Dir, ".owned-army-ui.lock"))
		s.locked = false
	}
}
func (s *armyUIStore) Save(a OwnedArmy) error {
	if s == nil || !s.locked {
		return errors.New("軍隊進度未鎖定")
	}
	base, err := os.ReadFile(filepath.Join(s.Dir, "gamedata.ay"))
	if err != nil || contentSHA(base) != s.OriginalSHA {
		return errors.New("基底進度已改變，請重新開啟")
	}
	target := filepath.Join(s.Dir, "gamedata.ay.army.json")
	if st, e := os.Lstat(target); e == nil {
		if !st.Mode().IsRegular() || st.Size() > 1<<20 {
			return errors.New("軍隊附檔形狀不符")
		}
		raw, e := os.ReadFile(target)
		if e != nil {
			return e
		}
		if s.SavedSHA == "" || contentSHA(raw) != s.SavedSHA {
			return errors.New("軍隊進度已改變，請重新開啟")
		}
	} else if !os.IsNotExist(e) {
		return e
	} else if s.SavedSHA != "" {
		return errors.New("軍隊附檔已移走，請重新開啟")
	}
	if err = saveArmy(s.Dir, s.Catalog, a); err != nil {
		return err
	}
	directory, err := os.Open(s.Dir)
	if err != nil {
		return err
	}
	err = directory.Sync()
	closeErr := directory.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	raw, err := os.ReadFile(target)
	if err != nil {
		return err
	}
	s.SavedSHA = contentSHA(raw)
	return nil
}

type armyUI struct {
	Catalog                ArmyCatalog
	Army                   OwnedArmy
	Store                  *armyUIStore
	Offers                 []string
	Selected               string
	Quantity               string
	NewOnly                bool
	Page                   int
	Font                   string
	Message                string
	QtyFocused, ReplaceQty bool
	Transactions           uint64
	Dirty                  bool
}

func freshArmyUI(c ArmyCatalog) OwnedArmy {
	a := OwnedArmy{Gold: 5000, Leadership: 1000, RecruitRank: 1, Rules: "tactics", Offers: map[string]ArmyOffer{}}
	for _, p := range c.Profiles {
		a.Offers["offer:"+p.ID] = ArmyOffer{Unit: p.ID, Stock: 1000}
	}
	return a
}
func newArmyUI(c ArmyCatalog, s *armyUIStore, a OwnedArmy) (*armyUI, error) {
	if err := a.validate(c); err != nil {
		return nil, err
	}
	u := &armyUI{Catalog: c, Army: a, Store: s, NewOnly: true, Quantity: "1", Font: "noto", Message: "選擇兵種與數量，招募後自動儲存。", Dirty: true}
	for _, p := range c.Profiles {
		var keys []string
		for key, offer := range a.Offers {
			if offer.Unit == p.ID {
				keys = append(keys, key)
			}
		}
		sort.Strings(keys)
		u.Offers = append(u.Offers, keys...)
	}
	if len(u.Offers) != len(a.Offers) {
		return nil, errors.New("招募項目身分不符")
	}
	if len(u.visibleOffers()) == 0 {
		u.NewOnly = false
	}
	u.selectFirst()
	return u, nil
}
func (u *armyUI) profile(offer string) UnitProfile {
	v := u.Army.Offers[offer]
	for _, p := range u.Catalog.Profiles {
		if p.ID == v.Unit {
			return p
		}
	}
	return UnitProfile{}
}
func (u *armyUI) visibleOffers() []string {
	var rows []string
	for _, id := range u.Offers {
		if !u.NewOnly || u.profile(id).NativeKind == 0 {
			rows = append(rows, id)
		}
	}
	return rows
}
func (u *armyUI) selectFirst() {
	rows := u.visibleOffers()
	u.Page = 0
	u.Selected = ""
	if len(rows) > 0 {
		u.Selected = rows[0]
	}
	u.Quantity = "1"
	u.QtyFocused = false
	u.Dirty = true
}
func (u *armyUI) pageOffers() []string {
	rows := u.visibleOffers()
	start := u.Page * 6
	if start >= len(rows) {
		return nil
	}
	return rows[start:min(start+6, len(rows))]
}
func (u *armyUI) quote() (ArmyQuote, error) {
	if u.Selected == "" {
		return ArmyQuote{Slot: -1, Reason: "stock"}, nil
	}
	q, e := u.Army.quote(u.Catalog, u.Selected)
	if e == nil && u.Army.Rules == "native" && u.profile(u.Selected).NativeKind == 0 {
		q.Maximum = 0
		q.Reason = "rules"
	}
	return q, e
}
func (u *armyUI) quantity() (uint32, bool) {
	if u.Quantity == "" {
		return 0, false
	}
	v, e := strconv.ParseUint(u.Quantity, 10, 32)
	return uint32(v), e == nil && v > 0
}
func (u *armyUI) canRecruit() bool {
	q, e := u.quote()
	n, ok := u.quantity()
	return e == nil && ok && n <= q.Maximum
}
func armyUIReason(reason string) string {
	switch reason {
	case "rank":
		return "等級不足"
	case "slots":
		return "六隊已滿"
	case "gold":
		return "金錢不足"
	case "leadership":
		return "領導力不足"
	case "stock":
		return "庫存不足"
	case "stack-limit":
		return "兵數已達上限"
	case "rules":
		return "新增兵種需增強規則"
	}
	return "無法招募"
}
func (u *armyUI) recruit() error {
	q, err := u.quote()
	if err != nil {
		return err
	}
	n, ok := u.quantity()
	if !ok {
		return errors.New("請輸入有效的招募數量")
	}
	if n > q.Maximum {
		return fmt.Errorf("%s，可招募 %d。", armyUIReason(q.Reason), q.Maximum)
	}
	next, receipt, err := u.Army.recruit(u.Catalog, u.Selected, n)
	if err != nil {
		return err
	}
	if err = u.Store.Save(next); err != nil {
		return err
	}
	u.Army = next
	u.Transactions++
	u.Message = fmt.Sprintf("已招募%s %d，花費 %d。已儲存。", u.profile(u.Selected).Name, n, receipt.Spent)
	u.Dirty = true
	return nil
}
func (u *armyUI) setRules(id string) error {
	if id != "native" && id != "formation" && id != "tactics" {
		return errors.New("規則選項無效")
	}
	if id == u.Army.Rules {
		return nil
	}
	next := u.Army
	next.Rules = id
	if err := next.validate(u.Catalog); err != nil {
		return errors.New("軍隊含新增兵種，請保留增強規則")
	}
	if err := u.Store.Save(next); err != nil {
		return err
	}
	u.Army = next
	u.Message = "規則已儲存。"
	u.Dirty = true
	return nil
}
func (u *armyUI) action(name string) error {
	u.Dirty = true
	switch name {
	case "recruit":
		return u.recruit()
	case "all", "new":
		u.NewOnly = name == "new"
		u.selectFirst()
	case "prev", "next":
		rows := u.visibleOffers()
		page := u.Page
		if name == "prev" {
			page--
		} else {
			page++
		}
		if page >= 0 && page*6 < len(rows) {
			u.Page = page
			u.Selected = rows[page*6]
			u.Quantity = "1"
			u.QtyFocused = false
		}
	case "up", "down":
		rows := u.visibleOffers()
		for i, id := range rows {
			if id == u.Selected {
				n := i - 1
				if name == "down" {
					n = i + 1
				}
				if n >= 0 && n < len(rows) {
					u.Selected = rows[n]
					u.Page = n / 6
					u.Quantity = "1"
					u.QtyFocused = false
				}
				break
			}
		}
	case "minus", "plus":
		n, e := strconv.ParseUint(u.Quantity, 10, 32)
		if e != nil {
			n = 0
		}
		if name == "minus" {
			if n > 0 {
				n--
			}
		} else if n < math.MaxUint32 {
			n++
		}
		u.Quantity = strconv.FormatUint(n, 10)
	case "max":
		q, e := u.quote()
		if e != nil {
			return e
		}
		u.Quantity = strconv.FormatUint(uint64(q.Maximum), 10)
	case "quantity":
		u.QtyFocused = true
		u.ReplaceQty = true
	case "clear":
		if u.QtyFocused {
			u.Quantity = ""
			u.ReplaceQty = false
		}
	case "backspace":
		if u.QtyFocused && len(u.Quantity) > 0 {
			u.Quantity = u.Quantity[:len(u.Quantity)-1]
			u.ReplaceQty = false
		}
	case "escape":
		u.QtyFocused = false
	default:
		if strings.HasPrefix(name, "select:") {
			for _, id := range u.visibleOffers() {
				if id == strings.TrimPrefix(name, "select:") {
					u.Selected = id
					u.Quantity = "1"
					u.QtyFocused = false
					return nil
				}
			}
			return errors.New("招募項目不在目前清單")
		}
		if strings.HasPrefix(name, "rules:") {
			return u.setRules(strings.TrimPrefix(name, "rules:"))
		}
	}
	return nil
}
func (u *armyUI) text(chars string) {
	if !u.QtyFocused || chars == "" {
		return
	}
	for _, r := range chars {
		if r < '0' || r > '9' {
			continue
		}
		if u.ReplaceQty {
			u.Quantity = ""
			u.ReplaceQty = false
		}
		if len(u.Quantity) < 10 {
			u.Quantity += string(r)
		}
	}
	u.Dirty = true
}
func (u *armyUI) handle(name string) {
	if err := u.action(name); err != nil {
		u.Message = err.Error()
		u.Dirty = true
	}
}
func (u *armyUI) usage() uint64 {
	idx, _ := u.Catalog.index()
	var n uint64
	for _, s := range u.Army.Slots {
		if s.Count > 0 {
			n += uint64(s.Count) * idx[s.Unit].Command
		}
	}
	return n
}
