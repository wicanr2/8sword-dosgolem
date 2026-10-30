//go:build ignore

package main

import (
	"bytes"
	"encoding/json"
	"math"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	dg "github.com/wicanr2/dosgolem"
)

func dismissFixture(t *testing.T) (*armyDismiss, *armyUIFonts) {
	t.Helper()
	c, w, f := reviewFixture(t)
	var cc game.OwnedCombatCatalog
	b, e := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_REVIEW_INPUT"), "combat-catalog.json"))
	if e != nil {
		t.Fatal(e)
	}
	if e = pairStrictJSON(b, &cc); e != nil {
		t.Fatal(e)
	}
	base, e := os.ReadFile(filepath.Join(os.Getenv("EIGHTSWORD_DISMISS_SESSION"), "gamedata.ay"))
	if e != nil {
		t.Fatal(e)
	}
	dir := filepath.Join(t.TempDir(), "pair")
	if e = initializeProgressPair(dir, base, c, cc, w); e != nil {
		t.Fatal(e)
	}
	store, snap, e := openProgressPair(dir, c, cc)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(store.Close)
	d := &armyDismiss{Port: &worldArmyPort{Store: store, Current: snap}, Active: true, Selected: 0}
	if e = d.refresh(snap); e != nil {
		t.Fatal(e)
	}
	return d, f
}
func TestDismissTransactionCancelOnceCompactAndCold(t *testing.T) {
	d, _ := dismissFixture(t)
	before := d.Snapshot
	close, e := d.handle(0x011b)
	if e != nil || !close || d.Port.Current.Token != before.Token {
		t.Fatal("cancel mutation", e)
	}
	d.NoteKey(0x1c, true)
	if _, e = d.handle(0x1c0d); e != nil {
		t.Fatal(e)
	}
	now := d.Port.Current
	if now.World.Army.Slots[0] != (ArmyStack{"openkb:wolf", 5}) || now.World.Army.Slots[1] != (ArmyStack{}) || d.Transactions != 1 || now.World.Revision != before.World.Revision+1 {
		t.Fatal("whole stack / compact", now.World)
	}
	if !bytes.Equal(now.Bytes.Native, before.Bytes.Native) || now.World.Army.Gold != before.World.Army.Gold || !reflect.DeepEqual(now.World.Army.Offers, before.World.Army.Offers) {
		t.Fatal("refund/native/stock changed")
	}
	for i := 0; i < 20; i++ {
		if _, e = d.handle(0x1c0d); e != nil {
			t.Fatal(e)
		}
	}
	if d.Transactions != 1 {
		t.Fatal("held key dismissed twice")
	}
	token := now.Token
	store := d.Port.Store
	store.Close()
	cold, s, e := openProgressPair(store.Dir, store.Catalog, store.Combat)
	if e != nil {
		t.Fatal(e)
	}
	defer cold.Close()
	if s.Token != token {
		t.Fatal("cold mismatch")
	}
	d.Port.Store = cold
	d.NoteKey(0x1c, true)
	if _, e = d.handle(0x1c0d); e != nil {
		t.Fatal(e)
	}
	if d.Selected != -1 || d.Data.Metrics.Total != 0 || d.Transactions != 2 {
		t.Fatal("last stack")
	}
	d.NoteKey(0x1c, true)
	if _, e = d.handle(0x1c0d); e != nil || d.Transactions != 2 {
		t.Fatal("empty stack", e)
	}
}
func TestDismissRejectsStaleBattleWidthAndPreservesInput(t *testing.T) {
	d, _ := dismissFixture(t)
	w := d.Snapshot.World
	c, cc := d.Port.Store.Catalog, d.Port.Store.Combat
	r := armyDismissRequest{w.Revision, 0, "native:01", 31}
	for _, name := range []string{"revision", "slot", "unit", "count", "overflow", "battle"} {
		t.Run(name, func(t *testing.T) {
			v, request := w, r
			switch name {
			case "revision":
				request.Revision++
			case "slot":
				request.Slot = 6
			case "unit":
				request.Unit = "openkb:wolf"
			case "count":
				request.Count--
			case "overflow":
				v.Revision = math.MaxUint64
				request.Revision = v.Revision
			case "battle":
				v.Battle = &WorldBattle{}
			}
			before, _ := json.Marshal(v)
			_, e := dismissWholeStack(c, cc, v, request)
			after, _ := json.Marshal(v)
			if e == nil || !bytes.Equal(before, after) {
				t.Fatal("bad request accepted or input changed", e)
			}
		})
	}
	// A wide Go army never narrows to native 16-bit quantities.
	v := w
	v.Army.Leadership = 30000
	v.Army.Slots = [6]ArmyStack{{"native:01", 20000}, {"native:02", 1}, {"openkb:wolf", 1}}
	out, e := dismissWholeStack(c, cc, v, armyDismissRequest{v.Revision, 1, "native:02", 1})
	if e != nil || out.Army.Slots[0].Count != 20000 || out.Army.Slots[1].Unit != "openkb:wolf" {
		t.Fatal("middle order", e)
	}
	// An external paired write invalidates the displayed request before any second write.
	changed := w
	changed.Revision++
	if _, e = d.Port.Store.Commit(d.Snapshot.Token, changed); e != nil {
		t.Fatal(e)
	}
	before, e := d.Port.Store.readBytes()
	if e != nil {
		t.Fatal(e)
	}
	if e = d.commit(); e == nil {
		t.Fatal("stale screen accepted")
	}
	after, e := d.Port.Store.readBytes()
	if e != nil || !bytes.Equal(before.World, after.World) || d.Transactions != 0 {
		t.Fatal("stale commit wrote", e)
	}
}
func TestDismissNavigationThreeFontsAndNoGuestMutationOnReject(t *testing.T) {
	d, f := dismissFixture(t)
	d.move(0x5000)
	if d.Selected != 1 {
		t.Fatal("down")
	}
	d.move(0x5000)
	if d.Selected != 1 {
		t.Fatal("empty navigation")
	}
	d.move(0x4800)
	if d.Selected != 0 {
		t.Fatal("up")
	}
	d.move(0x4d00)
	if d.Selected != 0 {
		t.Fatal("empty column")
	}
	for _, font := range []string{"noto", "lishu", "caoshu"} {
		_, texts := d.Paint(f, font)
		for _, s := range texts {
			r, b := s.Rect, s.Ink
			if b != [4]int{} && (b[0] < r[0] || b[1] < r[1] || b[2] > r[2] || b[3] > r[3]) {
				t.Fatal("text overflow", font, s)
			}
		}
	}
	for _, ip := range []uint16{0x777f, 0x77a3} {
		m := dg.New()
		mem := append([]byte(nil), m.Mem...)
		regs := m.CPU.R
		ok, e := d.instruction(m, ip)
		if ok || e == nil || !bytes.Equal(mem, m.Mem) || regs != m.CPU.R || m.CPU.Cycles != 0 {
			t.Fatal("unsafe ABI mutated guest")
		}
	}
}
