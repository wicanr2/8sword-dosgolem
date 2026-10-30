//go:build ignore

// 030 DRAFT: included only in the paired-progress research build.
package main

import game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"

func init() { battleUIOpener = openPairedBattleUI }
func openPairedBattleUI(dir string, c ArmyCatalog, cc game.OwnedCombatCatalog, _ OwnedWorld) (*battleUI, error) {
	store, snapshot, e := openProgressPair(dir, c, cc)
	if e != nil {
		return nil, e
	}
	u := &battleUI{Catalog: c, Combat: cc, World: snapshot.World, Dir: dir, BaseSHA: snapshot.NativeSHA, SavedSHA: snapshot.WorldSHA, Font: "noto", Dirty: true, Locked: true, Message: "先招募野狼，再進入戰場。", ClosePair: store.Close}
	token := snapshot.Token
	u.CommitPair = func(w OwnedWorld) (string, string, error) {
		next, e := store.Commit(token, w)
		if e != nil {
			return "", "", e
		}
		token = next.Token
		return next.NativeSHA, next.WorldSHA, nil
	}
	return u, nil
}
