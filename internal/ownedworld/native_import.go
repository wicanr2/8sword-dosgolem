package ownedworld

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	game "github.com/wicanr2/8sword-dosgolem/internal/eightsword"
	"golang.org/x/sys/unix"
)

var nativeImportSource = flag.String("import-native", "", "從已關閉遊戲的原版存檔目錄建立新Go進度")
var nativeImportOnly = flag.Bool("import-only", false, "匯入成功後退出")

const importArmyCatalogSHA = "07d6a012b89c788fc17547636b05c2b71aa79fed6d2cdb8d2f79952805f140e4"
const importCombatCatalogSHA = "dc31b8267eddf490da3ef055edc91f7a532901834afe3a2d82702917d4fbf36d"

// importFile resolves exactly one case-insensitive regular file. A missing
// optional map can use the original data directory; malformed entries cannot.
func importFile(dir, name string, limit int, optional bool) (string, []byte, error) {
	st, err := os.Lstat(dir)
	if err != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return "", nil, errors.New("匯入來源目錄不符")
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return "", nil, err
	}
	var found string
	for _, entry := range entries {
		if !strings.EqualFold(entry.Name(), name) {
			continue
		}
		if found != "" {
			return "", nil, fmt.Errorf("匯入檔名重複：%s", name)
		}
		found = filepath.Join(dir, entry.Name())
	}
	if found == "" {
		if optional {
			return "", nil, nil
		}
		return "", nil, fmt.Errorf("匯入缺少檔案：%s", name)
	}
	st, err = os.Lstat(found)
	if err != nil || !st.Mode().IsRegular() || st.Mode()&os.ModeSymlink != 0 || st.Size() > int64(limit) {
		return "", nil, fmt.Errorf("匯入檔案形狀不符：%s", name)
	}
	b, err := os.ReadFile(found)
	return found, b, err
}

func nativeImportedWorld(raw, pam []byte, c ArmyCatalog, cc game.OwnedCombatCatalog) (OwnedWorld, error) {
	var w OwnedWorld
	if c.digest() != importArmyCatalogSHA || cc.Digest() != importCombatCatalogSHA {
		return w, errors.New("匯入兵種資料版本不符")
	}
	v, err := decodeNativeResources(nativeProgressSource, raw)
	if err != nil {
		return w, err
	}
	code, err := worldArmyCode(pam)
	if err != nil {
		return w, err
	}
	w = OwnedWorld{Schema: "eightsword-owned-world/1", Army: OwnedArmy{
		Gold: v.Gold, Leadership: v.Leadership, RecruitRank: uint32(v.Rank), Rules: "native", Offers: map[string]ArmyOffer{},
	}, Progress: WorldProgress{Rank: uint32(v.Rank), Merit: v.Merit, Legacy04F6: v.MonthlyPay, Legacy04FC: v.SpellPower}, Encounters: map[string]WorldEncounter{}}
	for i := range w.Progress.Thresholds {
		w.Progress.Thresholds[i] = uint64(binary.LittleEndian.Uint16(code[0x1d780+0x5b2+i*2:]))
	}
	seen := map[uint16]bool{}
	for i := 0; i < 6; i++ {
		at := 12 + i*4
		kind := binary.LittleEndian.Uint16(raw[at:]) - uint16(at+3)
		count := binary.LittleEndian.Uint16(raw[at+2:]) - uint16(at+5)
		if kind == 0 && count == 0 {
			continue
		}
		if kind < 1 || kind > 25 || count == 0 || count > 32767 || seen[kind] {
			return w, errors.New("匯入軍隊種類、兵數或重複陣位不符")
		}
		seen[kind] = true
		w.Army.Slots[i] = ArmyStack{Unit: fmt.Sprintf("native:%02d", kind), Count: uint32(count)}
	}
	return w, w.validate(c, cc)
}

func importNativeProgress(root, source, destination, input string, c ArmyCatalog, cc game.OwnedCombatCatalog) error {
	if os.Getuid() != 1000 || destination == "" {
		return errors.New("匯入需要獨立的新進度目錄")
	}
	entries, err := os.ReadDir(source)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if strings.EqualFold(entry.Name(), "gamedata.ay.army.json") {
			return errors.New("來源已有Go軍隊附檔，請直接讀取該進度")
		}
	}
	inputs := map[string][]byte{}
	path, native, err := importFile(source, "gamedata.ay", 2987, false)
	if err != nil {
		return err
	}
	inputs[path] = native
	_, pam, err := importFile(input, "PAM.AY", 1<<20, false)
	if err != nil {
		return err
	}
	w, err := nativeImportedWorld(native, pam, c, cc)
	if err != nil {
		return err
	}
	maps := map[string][]byte{}
	for i := 0; i < 9; i++ {
		name := fmt.Sprintf("map%02d.ay", i)
		path, b, e := importFile(source, name, 5761, true)
		if e != nil {
			return e
		}
		if path == "" {
			path, b, e = importFile(root, name, 5761, false)
		}
		if e != nil {
			return e
		}
		maps[name] = b
		inputs[path] = b
	}
	if err = checkNativeMaps(maps); err != nil {
		return err
	}
	saved := checkpointSave{WorldSave: WorldSave{Schema: campSchema, OriginalSHA: nativeSHA(native), ArmyCatalogSHA: c.digest(), CombatCatalogSHA: cc.Digest(), World: w}, NativeFiles: maps}
	raw, err := json.MarshalIndent(saved, "", "  ")
	if err != nil {
		return err
	}
	pair := progressPairBytes{Native: native, World: append(raw, '\n')}
	if _, err = decodeProgressPair(pair, c, cc); err != nil {
		return err
	}
	for path, before := range inputs {
		st, e := os.Lstat(path)
		if e != nil || !st.Mode().IsRegular() {
			return errors.New("匯入來源已改變")
		}
		after, e := os.ReadFile(path)
		if e != nil || !bytes.Equal(before, after) {
			return errors.New("匯入來源已改變")
		}
	}
	return publishImportedProgress(destination, pair)
}

// Publish the complete v5 pair once. Existing destinations are never replaced.
func publishImportedProgress(dir string, pair progressPairBytes) error {
	parent := filepath.Dir(dir)
	var st unix.Stat_t
	if e := unix.Lstat(parent, &st); e != nil || st.Mode&unix.S_IFMT != unix.S_IFDIR || st.Uid != 1000 {
		return errors.New("匯入目的地的父目錄不符")
	}
	tmp, err := os.MkdirTemp(parent, ".owned-native-import-")
	if err != nil {
		return err
	}
	defer os.RemoveAll(tmp)
	for name, data := range map[string][]byte{"gamedata.ay": pair.Native, "gamedata.ay.army.json": pair.World} {
		f, e := os.OpenFile(filepath.Join(tmp, name), os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if e != nil {
			return e
		}
		_, e = f.Write(data)
		if e == nil {
			e = f.Sync()
		}
		closeErr := f.Close()
		if e != nil {
			return e
		}
		if closeErr != nil {
			return closeErr
		}
	}
	if err = pairSyncDir(tmp); err != nil {
		return err
	}
	if err = unix.Renameat2(unix.AT_FDCWD, tmp, unix.AT_FDCWD, dir, unix.RENAME_NOREPLACE); err != nil {
		return err
	}
	return pairSyncDir(parent)
}
