package eightsword

import (
	"bytes"
	"testing"

	"github.com/wicanr2/dosgolem/oracle"
)

// Exercise failure metadata on copies of a transaction reached through normal
// play. These diagnostics do not pretend DOS really issued an unknown write.
func checkRealBattleTransactionGuards(t *testing.T, e *Engine) func() bool {
	t.Helper()
	done := false
	e.Oracle.OnCall(oracle.Addr{Seg: e.Tracker.stringSeg, Off: 0x626}, func(*oracle.Oracle) {
		g := e.Tracker.graphics
		if done || g.pending == nil {
			return
		}
		before := observerGuestState(t, e)
		original := g.pending
		clone := func() *Graphics {
			copyG, copyT, copyB := *g, *g.parent, *g.pending
			copyG.parent, copyT.graphics, copyG.pending = &copyT, &copyG, &copyB
			copyG.owners = append([]graphicCell(nil), g.owners...)
			copyG.actors = append([]graphicCell(nil), g.actors...)
			copyT.cachedIndexed = append([]byte(nil), g.parent.cachedIndexed...)
			copyT.glyphs = make(map[uint32]*glyph, len(g.parent.glyphs))
			for id, value := range g.parent.glyphs {
				copyValue := *value
				copyT.glyphs[id] = &copyValue
			}
			return &copyG
		}
		valid := clone()
		if !valid.holdBattleFrame() || valid.parent.cachedFrame != g.parent.cachedFrame {
			t.Fatal("real eligible transaction did not retain its complete cache")
		}
		for _, name := range []string{"unknown-write", "mode-reset", "incomplete-return", "missing-return-bound", "unsupported-page"} {
			c := clone()
			fallbacks := c.Stats.BitmapTransactionFallbacks
			switch name {
			case "unknown-write":
				c.observeBattleTransactionWrite(oracle.VideoWrite{CS: e.Tracker.stringSeg, IP: 0xffff, Offset: c.pending.First})
			case "mode-reset":
				c.clear() // Every real mode event, including same mode, calls this.
			case "incomplete-return":
				c.pending.Writes = c.pending.Want - 1
				c.finishBattleTransaction(c.pending.Entry)
			case "missing-return-bound":
				c.pending.Start = e.Oracle.Steps() - battleBitmapStepBound - 1
			case "unsupported-page":
				b := *c.pending
				c.startBattleTransaction(b.Entry, b.First, b.Width, b.Height, 0xa400, 1)
			}
			if c.holdBattleFrame() || c.pending != nil || c.Stats.BitmapTransactionFallbacks != fallbacks+1 {
				t.Fatalf("%s could freeze a stale frame", name)
			}
		}
		replacement := clone()
		b := *replacement.pending
		replacement.startBattleTransaction(b.Entry, b.First, b.Width, b.Height, 0xa000, 1)
		if replacement.pending == nil || replacement.Stats.BitmapTransactionFallbacks != g.Stats.BitmapTransactionFallbacks+1 {
			t.Fatal("replacement transaction retained the old transaction")
		}
		completed := clone()
		completed.captureAfterHold = true
		completed.pending.Writes = completed.pending.Want
		completed.finishBattleTransaction(completed.pending.Entry)
		if completed.pending != nil || completed.captureAfterHold || completed.Stats.BitmapCompletionCaptures != g.Stats.BitmapCompletionCaptures+1 {
			t.Fatal("return after a held frame failed to refresh its complete cache")
		}
		if g.pending != original || !bytes.Equal(before, observerGuestState(t, e)) {
			t.Fatal("diagnostic metadata altered the real transaction or DOS")
		}
		done = true
		t.Log("real transaction: complete-cache retention and six failure/replacement guards passed without guest writes")
	})
	return func() bool { return done }
}
