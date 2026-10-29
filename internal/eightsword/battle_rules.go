// Spec 030 READY: optional formation rule. The original code resolves damage.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

var ErrBattleRulesLocked = errors.New("本場規則已固定，請於戰鬥結束後切換")

type BattleRuleFault struct {
	Step   uint64
	CS, IP uint16
	Reason string
}

func (f *BattleRuleFault) Error() string {
	return fmt.Sprintf("戰鬥規則在 %04X:%04X 停止：%s", f.CS, f.IP, f.Reason)
}

type BattleRuleRecord struct {
	Step                           uint64
	Side                           string
	Slot, Unit, Original, Adjusted uint16
	Eligible                       bool
	Suppressed                     bool `json:",omitempty"`
}
type BattleRuleInfo struct {
	Mode                                       string
	Bound, Active                              bool
	Started, Finished, Calls, Applied, Markers uint64
	Recent                                     []BattleRuleRecord
	Fault                                      *BattleRuleFault
	Suppressed                                 uint64 `json:",omitempty"`
}
type battleRulesController struct {
	BattleRuleInfo
	code, data, entrySS, entrySP uint16
	patterns                     map[uint16][]byte
	saves                        string
	persist, needFiles           bool
	fileCursor, writeCursor      int
	writeMode                    string
	writeBytes                   int
}
type rulesMarker struct {
	Schema    int    `json:"schema"`
	Rules     string `json:"rules"`
	SaveSHA   string `json:"save_sha256"`
	SaveBytes int    `json:"save_bytes"`
}

func formationEligible(slot int, kind, count uint16, frontCounts [3]uint16) bool {
	if slot < 0 || slot >= 3 || kind != 1 || count == 0 {
		return false
	}
	for i, n := range frontCounts {
		if i != slot && n > 0 {
			return true
		}
	}
	return false
}

func formationDamage(amount uint16) uint16 {
	return uint16(uint32(amount) * 80 / 100)
}

func validBattleRules(mode string) bool {
	return mode == "native" || mode == "formation" || mode == "tactics"
}
func rulesHaveFormation(mode string) bool { return mode == "formation" || mode == "tactics" }
func battleRulesName(mode string) string {
	switch mode {
	case "formation":
		return "結陣試作"
	case "tactics":
		return "戰術試作"
	default:
		return "原版規則"
	}
}
func (e *Engine) BattleRulesName() string { return battleRulesName(e.BattleRulesMode()) }
func archerPressureEligible(slot int, kind, count uint16, opposed [3]uint16) bool {
	return slot >= 0 && slot < 3 && kind == 3 && count > 0 && opposed[slot] > 0
}
func archerPressureDamage(amount uint16) uint16 { return uint16(uint32(amount) * 75 / 100) }

func readRulesMarker(dir string) (string, bool, error) {
	p := filepath.Join(dir, "gamedata.ay.rules.json")
	s, err := os.Lstat(p)
	if os.IsNotExist(err) {
		return "native", false, nil
	}
	if err != nil {
		return "", false, err
	}
	if !s.Mode().IsRegular() || s.Size() > 4096 {
		return "", true, fmt.Errorf("規則標記形狀無效")
	}
	f, err := os.Open(p)
	if err != nil {
		return "", true, err
	}
	defer f.Close()
	var m rulesMarker
	d := json.NewDecoder(io.LimitReader(f, 4097))
	d.DisallowUnknownFields()
	if err = d.Decode(&m); err != nil {
		return "", true, fmt.Errorf("規則標記無效：%w", err)
	}
	var extra any
	if d.Decode(&extra) != io.EOF || m.Schema != 1 || !validBattleRules(m.Rules) || m.SaveBytes != 2987 {
		return "", true, fmt.Errorf("規則標記內容無效")
	}
	data, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return "", true, err
	}
	if len(data) != m.SaveBytes || hash(data) != m.SaveSHA {
		return "", true, fmt.Errorf("規則標記與原版進度不符")
	}
	return m.Rules, true, nil
}
func writeRulesMarker(dir, mode string) error {
	if !validBattleRules(mode) {
		return fmt.Errorf("規則標記模式無效")
	}
	data, err := os.ReadFile(filepath.Join(dir, "gamedata.ay"))
	if err != nil {
		return err
	}
	if len(data) != 2987 {
		return fmt.Errorf("原版進度長度不符")
	}
	p := filepath.Join(dir, "gamedata.ay.rules.json")
	s, err := os.Lstat(p)
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	if err == nil && !s.Mode().IsRegular() {
		return fmt.Errorf("規則標記不是一般檔案")
	}
	f, err := os.CreateTemp(dir, ".rules-*")
	if err != nil {
		return err
	}
	defer os.Remove(f.Name())
	err = json.NewEncoder(f).Encode(rulesMarker{1, mode, hash(data), len(data)})
	closed := f.Close()
	if err != nil {
		return err
	}
	if closed != nil {
		return closed
	}
	return os.Rename(f.Name(), p)
}
func (e *Engine) initBattleRules(mode, dir string) error {
	if mode == "" {
		mode = "auto"
	}
	persist := mode != "auto"
	if mode == "auto" {
		var err error
		mode, persist, err = readRulesMarker(dir)
		if err != nil {
			return err
		}
	}
	if !validBattleRules(mode) {
		return fmt.Errorf("戰鬥規則無效：%s", mode)
	}
	e.rules = &battleRulesController{BattleRuleInfo: BattleRuleInfo{Mode: mode}, saves: dir, persist: persist || rulesHaveFormation(mode)}
	e.Oracle.OnFileOpen(func(name string) {
		if e.rules.persist && strings.EqualFold(filepath.Base(strings.ReplaceAll(name, "\\", "/")), "gamedata.ay") {
			if !e.rules.needFiles {
				e.rules.fileCursor = max(0, len(e.Oracle.FileOps())-1)
				e.rules.writeCursor = len(e.Oracle.Wrote())
				e.rules.writeMode = ""
				e.rules.writeBytes = 0
			}
			e.rules.needFiles = true
		}
	})
	return nil
}
func (e *Engine) BattleRulesMode() string {
	if e.rules == nil {
		return "native"
	}
	return e.rules.Mode
}
func (e *Engine) BattleRulesStatus() BattleRuleInfo {
	if e.rules == nil {
		return BattleRuleInfo{Mode: "native"}
	}
	s := e.rules.BattleRuleInfo
	s.Recent = append([]BattleRuleRecord(nil), s.Recent...)
	return s
}
func (e *Engine) SetBattleRules(mode string) error {
	if !validBattleRules(mode) {
		return fmt.Errorf("戰鬥規則無效：%s", mode)
	}
	if e.rules == nil {
		return fmt.Errorf("規則控制器尚未建立")
	}
	if e.rules.Fault != nil {
		return e.rules.Fault
	}
	if e.rules.Active && e.rules.Mode != mode {
		return ErrBattleRulesLocked
	}
	e.rules.Mode = mode
	if rulesHaveFormation(mode) && !e.rules.persist {
		e.rules.persist = true
		e.rules.fileCursor = len(e.Oracle.FileOps())
	}
	return e.syncBattleRules()
}
func (e *Engine) ruleFail(reason string) *BattleRuleFault {
	regs := e.Oracle.Regs()
	f := &BattleRuleFault{e.Oracle.Steps(), regs.CS, regs.IP, reason}
	e.rules.Fault = f
	return f
}
func (e *Engine) syncBattleRules() error {
	r := e.rules
	if r == nil {
		return nil
	}
	if r.Fault != nil {
		return r.Fault
	}
	if e.inEndingPhase() {
		r.Active = false
		return nil
	}
	if r.Bound {
		return nil
	}
	for _, overlay := range e.Oracle.Overlays() {
		if strings.EqualFold(overlay.Name, "PAM.AY") {
			return e.bindBattleRules(overlay.Seg, overlay.Reloc)
		}
	}
	return nil
}
func (e *Engine) bindBattleRules(load, reloc uint16) error {
	r := e.rules
	if r == nil || r.Bound {
		return nil
	}
	if load != reloc || uint32(load)+0x1d78 > 65535 || hash(e.PAM) != PAMSHA {
		return e.ruleFail("overlay-source")
	}
	r.code, r.data = load+0xe57, load+0x1d78
	word := func(at int) uint16 { return binary.LittleEndian.Uint16(e.PAM[at:]) }
	header := int(word(8)) * 16
	code := append([]byte(nil), e.PAM[header:]...)
	for i := 0; i < int(word(6)); i++ {
		at := int(word(24)) + i*4
		loc := int(word(at+2))*16 + int(word(at))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+reloc)
	}
	r.patterns = map[uint16][]byte{}
	for _, ip := range []uint16{8, 0x40, 0x1560, 0x15ca} {
		at := 0xe57*16 + int(ip)
		expected := append([]byte(nil), code[at:at+24]...)
		if !bytes.Equal(expected, e.Oracle.Bytes(oracle.Addr{Seg: r.code, Off: ip}, 24)) {
			return e.ruleFail("entry-bytes")
		}
		r.patterns[ip] = expected
	}
	for _, ip := range []uint16{8, 0x40, 0x1560, 0x15ca} {
		ip := ip
		e.Oracle.OnCall(oracle.Addr{Seg: r.code, Off: ip}, func(*oracle.Oracle) { e.battleRulePoint(ip) })
	}
	r.Bound = true
	return nil
}
func (e *Engine) battleRulePoint(ip uint16) {
	r := e.rules
	if r == nil || e.inEndingPhase() {
		return
	}
	if r.Fault != nil {
		panic(r.Fault)
	}
	c := e.Oracle.Regs()
	if c.CS != r.code || c.IP != ip || c.DS != r.data || c.SS != r.data || !bytes.Equal(r.patterns[ip], e.Oracle.Bytes(oracle.Addr{Seg: r.code, Off: ip}, 24)) {
		panic(e.ruleFail("entry-context"))
	}
	if ip == 8 {
		if r.Active {
			panic(e.ruleFail("nested-battle"))
		}
		r.Active = true
		r.Started++
		r.entrySS, r.entrySP = c.SS, c.SP
		return
	}
	if ip == 0x40 {
		if !r.Active || c.SS != r.entrySS || c.SP != r.entrySP {
			panic(e.ruleFail("battle-return"))
		}
		r.Active = false
		r.Finished++
		return
	}
	if !rulesHaveFormation(r.Mode) || !r.Active {
		return
	}
	if c.BP < 8 || c.BP > 65525 || c.SP > c.BP {
		panic(e.ruleFail("stack"))
	}
	word := func(off uint16) uint16 { return e.Oracle.Word(oracle.Addr{Seg: r.data, Off: off}) }
	source, target := word(c.BP+6), word(c.BP+8)
	if source >= 6 || target >= 6 {
		panic(e.ruleFail("unit-index"))
	}
	base, slots, side := uint16(0x56e8), uint16(0x6fb6), "player"
	if ip == 0x15ca {
		base, slots, side = 0x5700, 0x6fc2, "enemy"
	}
	mapping := [6]uint16{}
	seen := [6]bool{}
	targetSlot := -1
	for i := range mapping {
		id := word(slots + uint16(i*2))
		if id >= 6 {
			panic(e.ruleFail("slot-mapping"))
		}
		mapping[i] = id
		if word(base+id*4+2) > 0 {
			if seen[id] {
				panic(e.ruleFail("duplicate-live-mapping"))
			}
			seen[id] = true
		}
		if id == target {
			if targetSlot >= 0 && word(base+target*4+2) > 0 {
				panic(e.ruleFail("duplicate-target"))
			}
			targetSlot = i
		}
	}
	if word(base+target*4+2) > 0 && targetSlot < 0 {
		panic(e.ruleFail("unmapped-live-target"))
	}
	frontCounts := [3]uint16{}
	for i := range frontCounts {
		frontCounts[i] = word(base + mapping[i]*4 + 2)
	}
	eligible := formationEligible(targetSlot, word(base+target*4), word(base+target*4+2), frontCounts)
	adjusted := c.AX
	suppressed := false
	if r.Mode == "tactics" {
		sourceBase, sourceSlots := uint16(0x5700), uint16(0x6fc2)
		if ip == 0x15ca {
			sourceBase, sourceSlots = 0x56e8, 0x6fb6
		}
		kind, count := word(sourceBase+source*4), word(sourceBase+source*4+2)
		if kind == 3 && count > 0 {
			sourceSlot := -1
			seen := [6]bool{}
			for i := 0; i < 6; i++ {
				id := word(sourceSlots + uint16(i*2))
				if id >= 6 {
					panic(e.ruleFail("source-slot-mapping"))
				}
				if word(sourceBase+id*4+2) > 0 {
					if seen[id] {
						panic(e.ruleFail("source-duplicate-live-mapping"))
					}
					seen[id] = true
				}
				if id == source {
					sourceSlot = i
				}
			}
			if sourceSlot < 0 {
				panic(e.ruleFail("unmapped-live-source"))
			}
			suppressed = archerPressureEligible(sourceSlot, kind, count, frontCounts)
		}
	}
	if suppressed {
		adjusted = archerPressureDamage(adjusted)
		r.Suppressed++
	}
	if eligible {
		adjusted = formationDamage(adjusted)
	}
	if eligible || suppressed {
		e.Oracle.SetRegs(oracle.CallRegs{AX: adjusted, SetAX: true})
		r.Applied++
	}
	r.Calls++
	r.Recent = append(r.Recent, BattleRuleRecord{Step: e.Oracle.Steps(), Side: side, Slot: uint16(max(targetSlot, 0)), Unit: target, Original: c.AX, Adjusted: adjusted, Eligible: eligible, Suppressed: suppressed})
	if len(r.Recent) > 16 {
		r.Recent = append([]BattleRuleRecord(nil), r.Recent[len(r.Recent)-16:]...)
	}
}
func (e *Engine) syncRulesSave() error {
	r := e.rules
	if r == nil || !r.needFiles {
		return nil
	}
	if r.Fault != nil {
		return r.Fault
	}
	writes := e.Oracle.Wrote()
	if r.writeCursor > len(writes) {
		return e.ruleFail("write-log-reset")
	}
	for _, w := range writes[r.writeCursor:] {
		if strings.EqualFold(filepath.Base(strings.ReplaceAll(w.Name, "\\", "/")), "gamedata.ay") && w.N > 0 {
			if r.writeMode == "" {
				r.writeMode = r.Mode
			}
			r.writeBytes += w.N
		}
	}
	r.writeCursor = len(writes)
	ops := e.Oracle.FileOps()
	if r.fileCursor > len(ops) {
		return e.ruleFail("file-log-reset")
	}
	for _, op := range ops[r.fileCursor:] {
		if op.Failed || !strings.EqualFold(filepath.Base(strings.ReplaceAll(op.Name, "\\", "/")), "gamedata.ay") {
			continue
		}
		if op.Op == "open" {
			r.needFiles = true
		}
		if op.Op == "close" {
			if r.writeMode != "" {
				if r.writeBytes != 2987 {
					return e.ruleFail("saved-progress-write-size")
				}
				data, err := os.ReadFile(filepath.Join(r.saves, "gamedata.ay"))
				if err != nil {
					return e.ruleFail("saved-progress: " + err.Error())
				}
				if !bytes.Equal(data, e.Oracle.Bytes(oracle.Addr{Seg: 0x9e00}, 2987)) {
					return e.ruleFail("saved-progress-buffer")
				}
				if err = writeRulesMarker(r.saves, r.writeMode); err != nil {
					return e.ruleFail("save-marker: " + err.Error())
				}
				r.Markers++
				r.writeMode = ""
				r.writeBytes = 0
			}
			r.needFiles = false
		}
	}
	r.fileCursor = len(ops)
	return nil
}
