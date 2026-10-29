// Spec 030: Go-owned count/strength core. No DOS pointers, writes or executors.
package eightsword

import (
	"bytes"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"strings"
)

var ErrOwnedCombatTarget = errors.New("自有戰鬥目標不合法")

type OwnedCombatProfile struct {
	ID         string `json:"id"`
	NativeKind uint16 `json:"native_kind,omitempty"`
	Attack     uint64 `json:"attack"`
	HP         uint64 `json:"hp"`
	Ranged     bool   `json:"ranged"`
}
type OwnedCombatCatalog struct {
	Schema   string                        `json:"schema"`
	Profiles map[string]OwnedCombatProfile `json:"profiles"`
}
type OwnedCombatStack struct {
	Unit  string `json:"unit"`
	Count uint32 `json:"count"`
}
type OwnedCombatConfig struct {
	Rules       string    `json:"rules"`
	Divisors    [2]uint32 `json:"divisors"`
	Multipliers [2]uint32 `json:"multipliers"`
	// Explicit compatibility input for the sampled original special-5 gate.
	// It is a boolean, never an unchecked physical-unit or table index.
	Special5ZeroGate [2]bool `json:"special5_zero_gate"`
}
type OwnedCombatState struct {
	Schema     string                 `json:"schema"`
	CatalogSHA string                 `json:"catalog_sha256"`
	ArmySHA    string                 `json:"army_sha256"`
	Config     OwnedCombatConfig      `json:"config"`
	Rows       [2][6]OwnedCombatStack `json:"rows"`
	Initial    [2][6]OwnedCombatStack `json:"initial"`
	Acted      [2][6]bool             `json:"acted"`
	Round      uint32                 `json:"round"`
	Result     string                 `json:"result"`
	Committed  bool                   `json:"committed"`
}
type OwnedCombatAction struct {
	Side     int    `json:"side"`
	Source   int    `json:"source"`
	Target   int    `json:"target"`
	Kind     string `json:"kind"`
	Selector int    `json:"selector"`
}
type OwnedCombatOutcome struct {
	Action OwnedCombatAction `json:"action"`
	Damage uint64            `json:"damage"`
	Loss   uint32            `json:"loss"`
	Before uint32            `json:"before"`
	After  uint32            `json:"after"`
	Result string            `json:"result"`
}
type OwnedCombatStrength struct {
	Units     uint64 `json:"units"`
	BasePower uint64 `json:"base_power"`
	BaseHP    uint64 `json:"base_hp"`
}

func (c OwnedCombatCatalog) Digest() string { b, _ := json.Marshal(c); return hash(b) }
func (c OwnedCombatCatalog) Validate() error {
	if c.Schema != "eightsword-owned-combat-catalog/1" || len(c.Profiles) == 0 || len(c.Profiles) > 4096 {
		return errors.New("自有戰鬥兵種資料版本或數量錯誤")
	}
	seen := map[uint16]bool{}
	for id, p := range c.Profiles {
		if id == "" || len(id) > 80 || id != p.ID || p.Attack == 0 || p.HP == 0 || p.Attack > math.MaxUint32 || p.HP > math.MaxUint32 || p.NativeKind > 25 {
			return errors.New("自有戰鬥兵種資料無效")
		}
		if p.NativeKind != 0 {
			if p.ID != fmt.Sprintf("native:%02d", p.NativeKind) || seen[p.NativeKind] {
				return errors.New("原版種類與自有ID不符")
			}
			seen[p.NativeKind] = true
		} else if strings.HasPrefix(id, "native:") {
			return errors.New("擴充ID不可偽裝為原版種類")
		}
	}
	return nil
}
func ownedMul(a, b uint64) (uint64, error) {
	if a != 0 && b > math.MaxUint64/a {
		return 0, errors.New("自有兵力乘法溢位")
	}
	return a * b, nil
}
func ownedAdd(a, b uint64) (uint64, error) {
	if a > math.MaxUint64-b {
		return 0, errors.New("自有兵力加法溢位")
	}
	return a + b, nil
}
func ownedScale(v, percent uint64) uint64 { return (v/100)*percent + (v%100)*percent/100 }
func (s OwnedCombatState) strengthUnchecked(c OwnedCombatCatalog, side int) (OwnedCombatStrength, error) {
	var total OwnedCombatStrength
	for _, u := range s.Rows[side] {
		if u.Count == 0 {
			continue
		}
		p := c.Profiles[u.Unit]
		power, err := ownedMul(uint64(u.Count), p.Attack)
		if err != nil {
			return total, err
		}
		hp, err := ownedMul(uint64(u.Count), p.HP)
		if err != nil {
			return total, err
		}
		if total.Units, err = ownedAdd(total.Units, uint64(u.Count)); err != nil {
			return total, err
		}
		if total.BasePower, err = ownedAdd(total.BasePower, power); err != nil {
			return total, err
		}
		if total.BaseHP, err = ownedAdd(total.BaseHP, hp); err != nil {
			return total, err
		}
	}
	return total, nil
}
func (s OwnedCombatState) expectedResult() string {
	alive := [2]bool{}
	for side := range s.Rows {
		for _, u := range s.Rows[side] {
			alive[side] = alive[side] || u.Count > 0
		}
	}
	if !alive[0] && !alive[1] {
		return "draw"
	}
	if !alive[0] {
		return "loss"
	}
	if !alive[1] {
		return "win"
	}
	return ""
}
func (s OwnedCombatState) Validate(c OwnedCombatCatalog) error {
	if err := c.Validate(); err != nil {
		return err
	}
	if s.Schema != "eightsword-owned-combat/1" || s.CatalogSHA != c.Digest() || len(s.ArmySHA) != 64 || s.Round == 0 || !validBattleRules(s.Config.Rules) {
		return errors.New("自有戰場資料版本或來源不符")
	}
	if _, err := hex.DecodeString(s.ArmySHA); err != nil {
		return errors.New("自有軍隊SHA格式錯誤")
	}
	for side := range s.Rows {
		if s.Config.Divisors[side] == 0 || s.Config.Multipliers[side] == 0 {
			return errors.New("自有戰場除數或倍率無效")
		}
		for i, u := range s.Rows[side] {
			initial := s.Initial[side][i]
			if u.Unit != initial.Unit || u.Count > initial.Count {
				return errors.New("自有戰場部隊身分或兵數變更無效")
			}
			if u.Unit == "" {
				if u.Count != 0 || initial.Count != 0 {
					return errors.New("空部隊帶有兵數")
				}
				continue
			}
			p, ok := c.Profiles[u.Unit]
			if !ok {
				return errors.New("自有戰場兵種未登錄")
			}
			if s.Config.Rules == "native" && p.NativeKind == 0 {
				return errors.New("新增兵種不能交給原版規則執行器")
			}
		}
		if _, err := s.strengthUnchecked(c, side); err != nil {
			return err
		}
	}
	if s.Result != s.expectedResult() || (s.Committed && s.Result == "") {
		return errors.New("自有戰場結果或回寫旗標不符")
	}
	return nil
}
func NewOwnedCombat(c OwnedCombatCatalog, rows [2][6]OwnedCombatStack, cfg OwnedCombatConfig, armySHA string) (OwnedCombatState, error) {
	s := OwnedCombatState{Schema: "eightsword-owned-combat/1", CatalogSHA: c.Digest(), ArmySHA: armySHA, Config: cfg, Rows: rows, Initial: rows, Round: 1}
	s.Result = s.expectedResult()
	return s, s.Validate(c)
}
func (s OwnedCombatState) Strength(c OwnedCombatCatalog, side int) (OwnedCombatStrength, error) {
	if side < 0 || side >= 2 {
		return OwnedCombatStrength{}, errors.New("陣營超出範圍")
	}
	if err := s.Validate(c); err != nil {
		return OwnedCombatStrength{}, err
	}
	return s.strengthUnchecked(c, side)
}

// This is the sampled original encoded casualty threshold, widened safely.
// BaseHP is count*per-unit-HP, not a claim about original accumulated injury UI.
func ownedCombatLoss(damage, hp uint64, count uint32) uint32 {
	if count == 0 {
		return 0
	}
	q := damage / hp
	if q == 0 {
		return 0
	}
	if q >= uint64(count)-1 {
		return count
	}
	return uint32(q)
}
func (s OwnedCombatState) Plan(c OwnedCombatCatalog, a OwnedCombatAction) (OwnedCombatOutcome, error) {
	r := OwnedCombatOutcome{Action: a}
	if a.Side < 0 || a.Side >= 2 || a.Source < 0 || a.Source >= 6 || a.Target < 0 || a.Target >= 6 {
		return r, errors.New("自有戰場陣營或陣位超出範圍")
	}
	if err := s.Validate(c); err != nil {
		return r, err
	}
	if s.Result != "" || s.Committed {
		return r, errors.New("戰鬥已結束或已回寫")
	}
	if s.Acted[a.Side][a.Source] {
		return r, errors.New("部隊本輪已行動")
	}
	source := s.Rows[a.Side][a.Source]
	target := s.Rows[1-a.Side][a.Target]
	if source.Count == 0 {
		return r, errors.New("行動部隊已全滅")
	}
	if target.Count == 0 {
		return r, ErrOwnedCombatTarget
	}
	sp, tp := c.Profiles[source.Unit], c.Profiles[target.Unit]
	r.Before = target.Count
	switch a.Kind {
	case "normal", "ranged":
		if (a.Kind == "ranged") != sp.Ranged || (a.Kind == "normal" && a.Source >= 3) {
			return r, errors.New("普通或遠程行動種類不符")
		}
		if a.Kind == "normal" {
			front := false
			for i := 0; i < 3; i++ {
				front = front || s.Rows[1-a.Side][i].Count > 0
			}
			if front {
				if a.Target >= 3 {
					return r, ErrOwnedCombatTarget
				}
				if s.Rows[1-a.Side][a.Source].Count > 0 && a.Target != a.Source {
					return r, ErrOwnedCombatTarget
				}
			} else if a.Target < 3 {
				return r, ErrOwnedCombatTarget
			}
		}
		amount, err := ownedMul(uint64(source.Count), sp.Attack)
		if err != nil {
			return r, err
		}
		amount /= uint64(s.Config.Divisors[a.Side])
		amount, err = ownedMul(amount, uint64(s.Config.Multipliers[a.Side]))
		if err != nil {
			return r, err
		}
		if s.Config.Rules == "tactics" && sp.NativeKind == 3 && a.Source < 3 && s.Rows[1-a.Side][a.Source].Count > 0 {
			amount = ownedScale(amount, 75)
		}
		if rulesHaveFormation(s.Config.Rules) && tp.NativeKind == 1 && a.Target < 3 {
			for i := 0; i < 3; i++ {
				if i != a.Target && s.Rows[1-a.Side][i].Count > 0 {
					amount = ownedScale(amount, 80)
					break
				}
			}
		}
		r.Damage = amount
		r.Loss = ownedCombatLoss(amount, tp.HP, target.Count)
	case "special":
		if a.Source < 3 || (sp.NativeKind != 10 && sp.NativeKind != 12) {
			return r, errors.New("特殊行動來源未接管")
		}
		var loss uint64
		switch a.Selector {
		case 0:
			loss = 5
			if sp.NativeKind == 12 {
				loss = 2
			}
		case 2:
			if tp.NativeKind < 6 || tp.NativeKind > 15 {
				return r, ErrOwnedCombatTarget
			}
			loss = 15
			if sp.NativeKind == 12 {
				loss = 6
			}
		case 5:
			if a.Target == 0 && !s.Config.Special5ZeroGate[1-a.Side] {
				return r, ErrOwnedCombatTarget
			}
			if a.Target > 0 && s.Rows[1-a.Side][a.Target-1].Count == 0 {
				return r, ErrOwnedCombatTarget
			}
			divisor := uint64(2)
			if sp.NativeKind == 12 {
				divisor = 3
			}
			loss = uint64(target.Count)/divisor + 1
		default:
			return r, errors.New("特殊或法術分支尚未接管")
		}
		r.Loss = uint32(min(loss, uint64(target.Count)))
		var err error
		r.Damage, err = ownedMul(uint64(r.Loss), tp.HP)
		if err != nil {
			return r, err
		}
	default:
		return r, errors.New("未知的自有戰鬥行動")
	}
	r.After = target.Count - r.Loss
	return r, nil
}
func (s OwnedCombatState) Choose(c OwnedCombatCatalog, side, source int, kind string, selector, preferred int) (OwnedCombatOutcome, error) {
	if preferred < -1 || preferred >= 6 {
		return OwnedCombatOutcome{}, errors.New("原目標陣位超出範圍")
	}
	if err := s.Validate(c); err != nil {
		return OwnedCombatOutcome{}, err
	}
	var candidates []OwnedCombatOutcome
	for target := 0; target < 6; target++ {
		v, err := s.Plan(c, OwnedCombatAction{Side: side, Source: source, Target: target, Kind: kind, Selector: selector})
		if errors.Is(err, ErrOwnedCombatTarget) {
			continue
		}
		if err != nil {
			return v, err
		}
		candidates = append(candidates, v)
	}
	if len(candidates) == 0 {
		return OwnedCombatOutcome{}, ErrOwnedCombatTarget
	}
	best := candidates[0]
	for _, v := range candidates {
		if v.Action.Target == preferred {
			best = v
		}
	}
	for _, v := range candidates {
		kills, bestKills := v.After == 0, best.After == 0
		if kills && !bestKills || (kills == bestKills && uint64(v.Loss)*uint64(best.Before) > uint64(best.Loss)*uint64(v.Before)) {
			best = v
		}
	}
	return best, nil
}
func (s OwnedCombatState) Apply(c OwnedCombatCatalog, a OwnedCombatAction) (OwnedCombatState, OwnedCombatOutcome, error) {
	v, err := s.Plan(c, a)
	if err != nil {
		return s, v, err
	}
	next := s
	next.Rows[1-a.Side][a.Target].Count = v.After
	next.Acted[a.Side][a.Source] = true
	next.Result = next.expectedResult()
	v.Result = next.Result
	if err := next.Validate(c); err != nil {
		return s, OwnedCombatOutcome{}, err
	}
	return next, v, nil
}
func (s OwnedCombatState) NextRound(c OwnedCombatCatalog) (OwnedCombatState, error) {
	if err := s.Validate(c); err != nil {
		return s, err
	}
	if s.Result != "" || s.Committed || s.Round == math.MaxUint32 {
		return s, errors.New("不能開始下一輪")
	}
	for side := range s.Rows {
		for i, u := range s.Rows[side] {
			if u.Count > 0 && !s.Acted[side][i] {
				return s, errors.New("本輪尚有部隊未行動")
			}
		}
	}
	s.Round++
	s.Acted = [2][6]bool{}
	return s, nil
}
func (s OwnedCombatState) PassRearMelee(c OwnedCombatCatalog, side, source int) (OwnedCombatState, error) {
	if side < 0 || side >= 2 || source < 3 || source >= 6 {
		return s, errors.New("不能略過此陣位")
	}
	if err := s.Validate(c); err != nil {
		return s, err
	}
	u := s.Rows[side][source]
	p := c.Profiles[u.Unit]
	if s.Result != "" || s.Committed || s.Acted[side][source] || u.Count == 0 || p.Ranged || p.NativeKind == 10 || p.NativeKind == 12 {
		return s, errors.New("後排部隊仍有行動或已行動")
	}
	s.Acted[side][source] = true
	return s, nil
}
func (s OwnedCombatState) Commit(c OwnedCombatCatalog, armySHA string) (OwnedCombatState, [6]OwnedCombatStack, error) {
	var survivors [6]OwnedCombatStack
	if err := s.Validate(c); err != nil {
		return s, survivors, err
	}
	if s.Result == "" || s.Committed || armySHA != s.ArmySHA {
		return s, survivors, errors.New("戰果未完成、已回寫或軍隊已變更")
	}
	for i, u := range s.Rows[0] {
		if u.Count > 0 {
			survivors[i] = u
		}
	}
	s.Committed = true
	return s, survivors, nil
}

// JSON arrays otherwise accept short arrays and silently truncate long arrays.
// The owner must reject either shape before using any troop or slot index.
func DecodeOwnedCombatState(raw []byte) (OwnedCombatState, error) {
	var s OwnedCombatState
	if len(raw) > 1<<20 {
		return s, errors.New("自有戰場快照超過大小限制")
	}
	keys := json.NewDecoder(bytes.NewReader(raw))
	keys.UseNumber()
	var walk func(int) error
	walk = func(depth int) error {
		if depth > 32 {
			return errors.New("自有戰場JSON過深")
		}
		tok, err := keys.Token()
		if err != nil {
			return err
		}
		if delimiter, ok := tok.(json.Delim); ok {
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
						return errors.New("自有戰場JSON重複欄位")
					}
					seen[name] = true
					if err = walk(depth + 1); err != nil {
						return err
					}
				}
			case '[':
				for keys.More() {
					if err = walk(depth + 1); err != nil {
						return err
					}
				}
			default:
				return errors.New("自有戰場JSON結構錯誤")
			}
			_, err = keys.Token()
			return err
		}
		return nil
	}
	if err := walk(0); err != nil {
		return s, err
	}
	var shape map[string]json.RawMessage
	if err := json.Unmarshal(raw, &shape); err != nil {
		return s, err
	}
	for _, key := range []string{"schema", "catalog_sha256", "army_sha256", "config", "rows", "initial", "acted", "round", "result", "committed"} {
		if v, ok := shape[key]; !ok || bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
			return s, errors.New("自有戰場缺少欄位")
		}
	}
	for _, key := range []string{"rows", "initial", "acted"} {
		var sides [][]json.RawMessage
		if err := json.Unmarshal(shape[key], &sides); err != nil || len(sides) != 2 {
			return s, errors.New("自有戰場陣營數錯誤")
		}
		for _, slots := range sides {
			if len(slots) != 6 {
				return s, errors.New("自有戰場陣位數錯誤")
			}
			for _, cell := range slots {
				if bytes.Equal(bytes.TrimSpace(cell), []byte("null")) {
					return s, errors.New("自有戰場陣位為null")
				}
				if key != "acted" {
					var stack map[string]json.RawMessage
					if err := json.Unmarshal(cell, &stack); err != nil {
						return s, err
					}
					for _, field := range []string{"unit", "count"} {
						if v, ok := stack[field]; !ok || bytes.Equal(bytes.TrimSpace(v), []byte("null")) {
							return s, errors.New("自有戰場部隊欄位遺失")
						}
					}
				}
			}
		}
	}
	var cfg map[string]json.RawMessage
	if err := json.Unmarshal(shape["config"], &cfg); err != nil {
		return s, err
	}
	for _, key := range []string{"divisors", "multipliers", "special5_zero_gate"} {
		var sides []json.RawMessage
		if err := json.Unmarshal(cfg[key], &sides); err != nil || len(sides) != 2 {
			return s, errors.New("自有戰場設定陣營數錯誤")
		}
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if err := d.Decode(&s); err != nil {
		return s, err
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return s, errors.New("自有戰場附有額外JSON")
	}
	return s, nil
}
