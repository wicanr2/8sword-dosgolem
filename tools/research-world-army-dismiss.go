//go:build ignore

// 030 DRAFT: whole-stack dismissal, with a paired commit before UI mutation.
package main

import (
	"bytes"
	"errors"
	"fmt"
	"image"
	"math"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/oracle"
)

type armyDismissRequest struct {
	Revision uint64 `json:"revision"`
	Slot     int    `json:"slot"`
	Unit     string `json:"unit"`
	Count    uint32 `json:"count"`
}

func dismissWholeStack(c ArmyCatalog, cc game.OwnedCombatCatalog, w OwnedWorld, r armyDismissRequest) (OwnedWorld, error) {
	if e := w.validate(c, cc); e != nil {
		return w, e
	}
	if w.Battle != nil || r.Revision != w.Revision || w.Revision == math.MaxUint64 || r.Slot < 0 || r.Slot >= 6 {
		return w, errors.New("過期或無效的解雇狀態")
	}
	s := w.Army.Slots[r.Slot]
	if s.Unit == "" || s.Count == 0 || s.Unit != r.Unit || s.Count != r.Count {
		return w, errors.New("部隊已改變")
	}
	next := w
	next.Revision++
	next.Army.Slots = [6]ArmyStack{}
	at := 0
	for i, s := range w.Army.Slots {
		if i != r.Slot && s.Count > 0 {
			next.Army.Slots[at] = s
			at++
		}
	}
	if e := next.validate(c, cc); e != nil {
		return w, e
	}
	return next, nil
}

type armyDismiss struct {
	Engine                                       *game.Engine
	Port                                         *worldArmyPort
	Active                                       bool
	Selected                                     int
	Data                                         armyReviewData
	Snapshot                                     progressPairSnapshot
	Expected                                     []byte
	Dispatch                                     []byte
	FrameBP, FrameSP                             uint16
	EntrySP                                      uint16
	NativeRows                                   []byte
	EnterSerial, HandledEnter                    uint64
	Opens, Closes, Transactions, NativeDrawCalls uint64
	Events                                       []armyDismissRequest
}

func init() {
	armyReviewExtraFactory = func(e *game.Engine, p *worldArmyPort) (armyScreenExtra, error) { return installArmyDismiss(e, p) }
	armyReviewTitle = "神州八劍・軍隊試作・管理"
}
func (d *armyDismiss) IsActive() bool { return d.Active }
func (d *armyDismiss) NoteKey(scan byte, down bool) {
	if d.Active && scan == 0x1c && down {
		d.EnterSerial++
	}
}
func (d *armyDismiss) refresh(s progressPairSnapshot) error {
	v, e := describeArmyReview(d.Port.Store.Catalog, s.World)
	if e != nil {
		return e
	}
	d.Snapshot = s
	d.Data = v
	if d.Selected >= 6 || d.Selected < 0 || v.Rows[d.Selected].Count == 0 {
		d.Selected = -1
		for i, r := range v.Rows {
			if r.Count > 0 {
				d.Selected = i
				break
			}
		}
	}
	return nil
}
func (d *armyDismiss) commit() error {
	if d.Selected < 0 {
		return nil
	}
	s, e := d.Port.snapshot()
	if e != nil {
		return e
	}
	if s.Token != d.Snapshot.Token {
		return errors.New("解雇畫面已過期")
	}
	r := armyDismissRequest{s.World.Revision, d.Selected, d.Data.Rows[d.Selected].ID, d.Data.Rows[d.Selected].Count}
	next, e := dismissWholeStack(d.Port.Store.Catalog, d.Port.Store.Combat, s.World, r)
	if e != nil {
		return e
	}
	updated, e := d.Port.Store.Commit(s.Token, next)
	if e != nil {
		return e
	}
	// No native row, resource, shop stock or currency write is needed.
	d.Port.Current = updated
	d.Transactions++
	d.Events = append(d.Events, r)
	if d.Selected >= updated.WorldArmyCount() {
		d.Selected = updated.WorldArmyCount() - 1
	}
	return d.refresh(updated)
}
func (s progressPairSnapshot) WorldArmyCount() int {
	n := 0
	for _, r := range s.World.Army.Slots {
		if r.Count > 0 {
			n++
		}
	}
	return n
}
func (d *armyDismiss) move(key uint16) {
	if d.Selected < 0 {
		return
	}
	col, row := d.Selected/3, d.Selected%3
	switch key {
	case 0x4800:
		row = (row + 2) % 3
	case 0x5000:
		row = (row + 1) % 3
	case 0x4b00, 0x4d00:
		col = 1 - col
	default:
		return
	}
	at := col*3 + row
	if d.Data.Rows[at].Count > 0 {
		d.Selected = at
	}
}
func (d *armyDismiss) handle(key uint16) (bool, error) {
	if key == 0x011b {
		return true, nil
	}
	if key == 0x1c0d {
		if d.EnterSerial == d.HandledEnter {
			return false, nil
		}
		d.HandledEnter = d.EnterSerial
		return false, d.commit()
	}
	d.move(key)
	return false, nil
}
func installArmyDismiss(e *game.Engine, p *worldArmyPort) (*armyDismiss, error) {
	code, x := worldArmyCode(e.PAM)
	if x != nil {
		return nil, x
	}
	d := &armyDismiss{Engine: e, Port: p, Selected: -1, Expected: append([]byte(nil), code[0x775a:0x7bf2]...), Dispatch: append([]byte(nil), code[0x3e92:0x3f08]...)}
	if !bytes.Equal(d.Expected, e.Oracle.Bytes(oracle.Far(0x110, 0x775a), len(d.Expected))) {
		return nil, errors.New("解雇程式來源不符")
	}
	fail := func(s string) { panic(&worldArmyPortFault{"army dismissal: " + s}) }
	e.Oracle.OnCall(oracle.Far(0x110, 0x775a), func(o *oracle.Oracle) {
		r := o.Regs()
		if r.CS != 0x110 || r.DS != 0x1e88 || r.SS != 0x1e88 || r.SP > 65531 || o.Word(oracle.Far(0x1e88, 0x56bc)) != 2 || o.Word(oracle.Far(r.SS, r.SP)) != 0x3ede || o.Word(oracle.Far(r.SS, r.SP+2)) != 0x110 {
			fail("entry ABI")
		}
		if d.Active {
			if d.FrameBP == 0 && r.SP == d.EntrySP {
				return
			}
			fail("unexpected reentry")
		}
		s, x := p.snapshot()
		if x != nil {
			fail(x.Error())
		}
		d.Selected = 0
		if x = d.refresh(s); x != nil {
			fail(x.Error())
		}
		d.Active = true
		d.EntrySP = r.SP
		d.NativeRows = o.Bytes(oracle.Far(0x1e88, 0x54a), 24)
		d.FrameBP = 0
		d.FrameSP = 0
		d.HandledEnter = d.EnterSerial
		d.Opens++
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x75c6), func(*oracle.Oracle) {
		if d.Active {
			d.NativeDrawCalls++
			fail("native row renderer escaped")
		}
	})
	e.Oracle.OnCall(oracle.Far(0x110, 0x77a6), func(*oracle.Oracle) {
		if d.Active {
			fail("native navigation escaped Go input")
		}
	})
	for _, ip := range []uint16{0x777f, 0x77a3} {
		ip := ip
		e.Oracle.OnHostInstruction(oracle.Far(0x110, ip), func(m *dg.Machine) (bool, error) { return d.instruction(m, ip) })
	}
	return d, nil
}
func (d *armyDismiss) instruction(m *dg.Machine, ip uint16) (bool, error) {
	fail := func(s string) (bool, error) { return false, &worldArmyPortFault{"army dismissal: " + s} }
	c := m.CPU
	ds := uint32(0x1e880)
	if !d.Active || c.Seg[dg.CS] != 0x110 || c.Seg[dg.DS] != 0x1e88 || c.Seg[dg.SS] != 0x1e88 || c.IP != ip || c.Cycles == math.MaxUint64 || m.Read16(ds+0x56bc) != 2 {
		return fail("input ABI")
	}
	if !bytes.Equal(d.Expected, m.Mem[0x1100+0x775a:0x1100+0x7bf2]) || !bytes.Equal(d.Dispatch, m.Mem[0x1100+0x3e92:0x1100+0x3f08]) {
		return fail("runtime bytes")
	}
	s, e := d.Port.snapshot()
	if e != nil {
		return fail(e.Error())
	}
	if s.Token != d.Snapshot.Token {
		return fail("stale world")
	}
	if !bytes.Equal(d.NativeRows, m.Mem[ds+0x54a:ds+0x562]) {
		return fail("native rows changed")
	}
	for i, n := range pairWorldResources(s.World).words() {
		if uint64(m.Read16(ds+0x4f2+uint32(i*2))) != n {
			return fail("resources changed")
		}
	}
	bp, sp := c.R[dg.BP], c.R[dg.SP]
	if bp < 16 || bp > 65520 || sp > bp || m.Read16(ds+uint32(bp)+2) != 0x3ede || m.Read16(ds+uint32(bp)+4) != 0x110 {
		return fail("original frame")
	}
	switch ip {
	case 0x777f:
		if d.FrameBP != 0 || sp > 65531 || m.Read16(ds+uint32(sp)) != 0x110 || m.Read16(ds+uint32(sp)+2) != 0x30 {
			return fail("initial renderer call")
		}
		c.R[dg.SP] += 4
		d.FrameSP = c.R[dg.SP]
		d.FrameBP = bp
		c.IP = 0x779e
	case 0x77a3:
		if bp != d.FrameBP || sp != d.FrameSP {
			return fail("key return frame")
		}
		close, e := d.handle(c.R[dg.AX])
		if e != nil {
			return fail(e.Error())
		}
		if close {
			d.Active = false
			d.Closes++
			c.IP = 0x7bed
		} else {
			c.IP = 0x779e
		}
	default:
		return fail("unknown input point")
	}
	c.Cycles++
	return true, nil
}
func dismissCard(i int) image.Rectangle {
	x, y := 60+i/3*920, 245+i%3*250
	return image.Rect(x, y, x+880, y+230)
}

var dismissCommitRect = image.Rect(1130, 1070, 1460, 1145)

func (d *armyDismiss) Click(x, y int) (byte, error) {
	pt := image.Pt(x, y)
	for i, r := range d.Data.Rows {
		if r.Count > 0 && pt.In(dismissCard(i)) {
			d.Selected = i
			return 0, nil
		}
	}
	if pt.In(reviewCloseRect) {
		return 1, nil
	}
	if d.Selected >= 0 && pt.In(dismissCommitRect) {
		return 0x1c, nil
	}
	return 0, nil
}
func (d *armyDismiss) Paint(f *armyUIFonts, font string) (*image.RGBA, []armyUIText) {
	return paintArmyDismiss(d, f, font)
}
func (d *armyDismiss) State() map[string]any {
	return map[string]any{"dismiss_active": d.Active, "dismiss_selected": d.Selected, "dismiss_data": d.Data, "dismiss_opens": d.Opens, "dismiss_closes": d.Closes, "dismiss_transactions": d.Transactions, "dismiss_native_draw_calls": d.NativeDrawCalls, "dismiss_events": d.Events}
}
func (d *armyDismiss) String() string { return fmt.Sprintf("Go dismissal: %d commits", d.Transactions) }
