package ownedworld

import (
	"errors"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
)

// Set only by the prepared-source launcher, which installs the reviewed Go
// source-scene patch. A raw build keeps refusing before opening progress.
var originalPlayerBuild string

func installOriginalPlayerServices(e *game.Engine, p *worldArmyPort, scratch, art string) (*originalArmyReview, armyScreenExtra, error) {
	if p.Current.World.Battle != nil {
		return nil, nil, errors.New("此進度含舊卡片戰中狀態，請保留原檔並使用原研究工具恢復")
	}
	if _, err := installOriginalRecruitQuantity(e, p); err != nil {
		return nil, nil, err
	}
	v, err := installOriginalArmyReview(e, p)
	if err != nil {
		return nil, nil, err
	}
	d, err := installOriginalArmyDismiss(e, p, v)
	if err != nil {
		return nil, nil, err
	}
	if p.OriginalCheckpoint, err = installNativeCheckpoint(e, p, scratch); err != nil {
		return nil, nil, err
	}
	for _, install := range []func() error{
		func() error { _, x := installMonthlyPort(e, p); return x },
		func() error { _, x := installTreasurePort(e, p); return x },
		func() error { _, x := installAlchemyPort(e, p); return x },
		func() error { _, x := installSummonPort(e, p); return x },
		func() error { _, x := installOriginalPlayerBattles(e, p, art); return x },
	} {
		if err = install(); err != nil {
			return nil, nil, err
		}
	}
	x := &reinforcementUI{Previous: &wideMonthlyExtra{Previous: d}, Engine: e, Port: p, Count: 1, Blocked: map[byte]bool{}}
	installOriginalReinforcementQuantity(x)
	reinforcementCurrent = x
	return v, x, nil
}
