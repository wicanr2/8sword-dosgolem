// Normal native army/save path, with the same Go HD frame and read-only icons.
package ownedworld

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"slices"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/audio"
	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"github.com/wicanr2/dosgolem/oracle"
	"golang.org/x/sys/unix"
)

func runRecruitClient() error {
	if !slices.Contains(os.Args, "-native-game") {
		return runArmyReview()
	}
	_ = flag.Bool("native-game", false, "原版軍隊與存檔，HD募兵圖示")
	root := flag.String("root", "", "唯讀原版")
	assets := flag.String("assets", "", "HD素材")
	saves := flag.String("saves", "", "獨立可寫原版存檔")
	pack := flag.String("ui-assets", "", "字型資料")
	capture := flag.String("capture-dir", "", "抽驗輸出")
	scale := flag.Float64("scale", 1, "視窗比例")
	mute := flag.Bool("mute", false, "靜音，保留音訊時鐘")
	flag.Parse()
	if os.Getuid() != 1000 || *saves == "" || *scale < 0.5 || *scale > 2 {
		return errors.New("無效的原版試玩路徑或比例")
	}
	st, err := os.Lstat(*saves)
	var owner unix.Stat_t
	ownerErr := unix.Lstat(*saves, &owner)
	if err != nil || ownerErr != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 || owner.Uid != 1000 {
		return errors.New("原版試玩存檔目錄不符")
	}
	fd, err := unix.Open(filepath.Join(*saves, ".recruit-native.lock"), unix.O_RDWR|unix.O_CREAT|unix.O_NOFOLLOW|unix.O_CLOEXEC, 0600)
	if err != nil {
		return err
	}
	defer unix.Close(fd)
	if err = unix.Flock(fd, unix.LOCK_EX|unix.LOCK_NB); err != nil {
		return errors.New("原版試玩進度使用中")
	}
	defer unix.Flock(fd, unix.LOCK_UN)
	fonts, err := loadArmyUIFonts(*pack)
	if err != nil {
		return err
	}
	engine, err := game.Open(game.Options{Root: *root, Assets: *assets, Saves: *saves, HD: true})
	if err != nil {
		return err
	}
	defer engine.Close()
	engine.Oracle.SetClock(12, 0, 0, 0)
	engine.EnableLiveClock(3000)
	pref := filepath.Join(*saves, "font-preference.json")
	font, err := game.LoadFontPreference(pref)
	if err != nil {
		return err
	}
	if err = engine.SetFont(font); err != nil {
		return err
	}
	app := &armyReviewApp{Engine: engine, Fonts: fonts, Owned: false, Capture: *capture, Preference: pref, Texture: ebiten.NewImage(1920, 1200)}
	swordOnCall(engine.Oracle, oracle.Far(0x110, 0x3e92), func(o *oracle.Oracle) {
		if o.Regs().CS == 0x110 && o.Regs().DS == 0x1e88 && o.Word(oracle.Far(0x1e88, 0x56bc)) == 1 {
			app.NativeActive = true
		}
	})
	swordOnCall(engine.Oracle, oracle.Far(0x110, 0x3ed8), func(o *oracle.Oracle) {
		if o.Regs().CS == 0x110 && o.Regs().DS == 0x1e88 {
			app.NativeActive = false
		}
	})
	if !*mute {
		ctx := audio.NewContext(48000)
		app.PCM = &reviewPCM{}
		player, err := ctx.NewPlayer(app.PCM)
		if err != nil {
			return err
		}
		defer player.Close()
		player.Play()
	}
	ebiten.SetTPS(30)
	ebiten.SetWindowTitle("神州八劍・軍隊試作・原版規則與HD招募圖示")
	ebiten.SetWindowSize(int(1920**scale), int(1200**scale))
	if err = ebiten.RunGame(app); err != nil {
		return fmt.Errorf("原版HD招募試玩：%w", err)
	}
	if *capture != "" {
		return app.writeStatus("ui-final.json")
	}
	return nil
}
