// 030 READY: optional target selection. The original executor resolves every action.
package eightsword

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"strings"

	"github.com/wicanr2/dosgolem/oracle"
)

var errBattleAINoTarget = errors.New("no supported legal target")

type BattleAIFault struct {
	Step   uint64
	CS, IP uint16
	Reason string
}

func (f *BattleAIFault) Error() string {
	return fmt.Sprintf("策略AI在 %04X:%04X 停止：%s", f.CS, f.IP, f.Reason)
}

type BattleAIRecord struct {
	Step     uint64
	Decision battleAIDecision
}
type BattleAIInfo struct {
	Mode                        string
	Bound                       bool
	Decisions, Changed, Skipped uint64
	LastSkip                    string
	Recent                      []BattleAIRecord
	Fault                       *BattleAIFault
}
type battleAIController struct {
	BattleAIInfo
	code, data uint16
	patterns   map[uint16][]byte
}

var battleAIEntries = map[uint16]string{0x180a: "normal", 0x16e7: "ranged", 0x1974: "ranged", 0xdbd: "special0", 0xf06: "special2", 0xfbb: "special5"}

func (e *Engine) BattleAIMode() string {
	if e.battleAI == nil {
		return "native"
	}
	return e.battleAI.Mode
}
func (e *Engine) BattleAIStatus() BattleAIInfo {
	if e.battleAI == nil {
		return BattleAIInfo{Mode: "native"}
	}
	s := e.battleAI.BattleAIInfo
	s.Recent = append([]BattleAIRecord(nil), s.Recent...)
	for i := range s.Recent {
		s.Recent[i].Decision.Candidates = append([]battleAICandidate(nil), s.Recent[i].Decision.Candidates...)
	}
	return s
}

// SetBattleAI runs on the emulation thread, outside an Advance call. Native is
// the default; after the first enable, registered callbacks remain dormant.
func (e *Engine) SetBattleAI(mode string) error {
	if mode == "" {
		mode = "native"
	}
	if mode != "native" && mode != "target" {
		return fmt.Errorf("AI模式無效：%s", mode)
	}
	if mode == "native" {
		if e.battleAI != nil {
			e.battleAI.Mode = mode
		}
		return nil
	}
	if hash(e.PAM) != PAMSHA {
		return fmt.Errorf("策略AI的PAM來源不符")
	}
	if e.battleAI == nil {
		e.battleAI = &battleAIController{BattleAIInfo: BattleAIInfo{Mode: mode}}
	}
	if e.battleAI.Fault != nil {
		return e.battleAI.Fault
	}
	e.battleAI.Mode = mode
	return e.syncBattleAI()
}
func (e *Engine) battleAIFail(reason string) *BattleAIFault {
	r := e.Oracle.Regs()
	f := &BattleAIFault{Step: e.Oracle.Steps(), CS: r.CS, IP: r.IP, Reason: reason}
	e.battleAI.Fault = f
	return f
}
func (e *Engine) battleAIRun(run func() error) (err error) {
	defer func() {
		if p := recover(); p != nil {
			if f, ok := p.(*BattleAIFault); ok {
				err = f
			} else {
				panic(p)
			}
		}
	}()
	return run()
}
func (e *Engine) syncBattleAI() error {
	a := e.battleAI
	if a == nil || a.Mode == "native" {
		return nil
	}
	if a.Fault != nil {
		return a.Fault
	}
	if a.Bound || e.inEndingPhase() {
		return nil
	}
	for _, overlay := range e.Oracle.Overlays() {
		if !strings.EqualFold(overlay.Name, "PAM.AY") {
			continue
		}
		return e.bindBattleAI(overlay.Seg, overlay.Reloc)
	}
	return nil
}
func (e *Engine) bindBattleAI(load, reloc uint16) error {
	a := e.battleAI
	if a == nil || a.Mode != "target" || a.Bound {
		return nil
	}
	if load != reloc || uint32(load)+0x1d78 > 65535 {
		return e.battleAIFail("overlay-base")
	}
	if hash(e.PAM) != PAMSHA {
		return e.battleAIFail("source-sha")
	}
	a.code, a.data = load+0xe57, load+0x1d78
	u16 := func(at int) uint16 { return binary.LittleEndian.Uint16(e.PAM[at:]) }
	header := int(u16(8)) * 16
	code := append([]byte(nil), e.PAM[header:]...)
	for i := 0; i < int(u16(6)); i++ {
		at := int(u16(24)) + i*4
		loc := int(u16(at+2))*16 + int(u16(at))
		binary.LittleEndian.PutUint16(code[loc:], binary.LittleEndian.Uint16(code[loc:])+reloc)
	}
	patterns := map[uint16][]byte{}
	for ip := range battleAIEntries {
		at := 0xe57*16 + int(ip)
		expected := append([]byte(nil), code[at:at+24]...)
		if !bytes.Equal(expected, e.Oracle.Bytes(oracle.Addr{Seg: a.code, Off: ip}, 24)) {
			return e.battleAIFail("entry-bytes")
		}
		patterns[ip] = expected
	}
	a.patterns = patterns
	for ip, route := range battleAIEntries {
		ip, route := ip, route
		e.Oracle.OnCall(oracle.Addr{Seg: a.code, Off: ip}, func(*oracle.Oracle) { e.battleAITarget(ip, route) })
	}
	a.Bound = true
	return nil
}
func (e *Engine) battleAITarget(ip uint16, route string) {
	a := e.battleAI
	if a == nil || a.Mode != "target" || e.inEndingPhase() {
		return
	}
	if a.Fault != nil {
		panic(a.Fault)
	}
	o := e.Oracle
	r := o.Regs()
	if r.CS != a.code || r.IP != ip || r.DS != a.data || r.SS != a.data || r.BP < 8 || r.BP > 65525 || r.SP > r.BP {
		panic(e.battleAIFail("entry-registers"))
	}
	if !bytes.Equal(a.patterns[ip], o.Bytes(oracle.Addr{Seg: r.CS, Off: ip}, 24)) {
		panic(e.battleAIFail("entry-bytes"))
	}
	word := func(seg, off uint16) uint16 { return o.Word(oracle.Addr{Seg: seg, Off: off}) }
	source := word(r.SS, r.BP-6)
	target := word(r.SS, r.BP-4)
	selector := uint16(65535)
	offset := r.BP - 4
	if strings.HasPrefix(route, "special") {
		source = word(r.SS, r.BP+6)
		selector = word(r.SS, r.BP-4)
		target = word(r.SS, r.BP-8)
		offset = r.BP - 8
		expected := map[string]uint16{"special0": 0, "special2": 2, "special5": 5}[route]
		if selector != expected {
			panic(e.battleAIFail("selector-route"))
		}
		if selector == 5 {
			target = r.DX
			if target >= 6 {
				panic(e.battleAIFail("target-range"))
			}
			guard := word(r.DS, 0x6fb4+target*2)
			if guard >= 6 {
				panic(e.battleAIFail("shifted-mapping"))
			}
			if word(r.DS, 0x56ea+guard*4) == 0 {
				a.Skipped++
				a.LastSkip = "原版仍在重選目標"
				return
			}
		}
		route = "special"
	} else {
		if target < 7 || target > 12 {
			panic(e.battleAIFail("encoded-target"))
		}
		target -= 7
	}
	v := battleAIView{Route: route, SourceSlot: source, OriginalSlot: target, Selector: selector, ShiftedSlotZero: word(r.DS, 0x6fb4), Divisor: word(r.DS, 0x26ac)}
	for i := uint16(0); i < 6; i++ {
		v.Friendly[i] = battleAIUnit{word(r.DS, 0x56e8+i*4), word(r.DS, 0x56ea+i*4)}
		v.Enemy[i] = battleAIUnit{word(r.DS, 0x5700+i*4), word(r.DS, 0x5702+i*4)}
		v.FriendlySlots[i] = word(r.DS, 0x6fb6+i*2)
		v.EnemySlots[i] = word(r.DS, 0x6fc2+i*2)
	}
	for i := range v.Factors {
		v.Factors[i] = word(r.DS, 0x70ce+uint16(i*2))
	}
	d, err := evaluateBattleAI(v)
	if errors.Is(err, errBattleAINoTarget) {
		a.Skipped++
		a.LastSkip = "沒有受支援的活目標"
		return
	}
	if err != nil {
		panic(e.battleAIFail(err.Error()))
	}
	// All validation and scoring is complete. Submit exactly one logical target.
	if d.SuggestedSlot != d.OriginalSlot {
		if selector == 5 {
			o.SetRegs(oracle.CallRegs{DX: d.SuggestedSlot, SetDX: true})
		} else {
			selected := d.SuggestedSlot
			if route != "special" {
				selected += 7
			}
			o.WriteU16(oracle.Addr{Seg: r.SS, Off: offset}, selected)
		}
		a.Changed++
	}
	a.Decisions++
	record := BattleAIRecord{Step: o.Steps(), Decision: d}
	if len(a.Recent) == 32 {
		copy(a.Recent, a.Recent[1:])
		a.Recent[31] = record
	} else {
		a.Recent = append(a.Recent, record)
	}
}
