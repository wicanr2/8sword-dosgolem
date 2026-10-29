package eightsword

import (
	"errors"
	"fmt"
	"os"
	"strings"
)

// The owned combat data core is available, but the player handoff is not yet
// integrated. Never silently open its base DOS save and discard extended units.
var ErrOwnedArmyHandoffPending = errors.New("自有軍隊存檔的玩家交接尚未完成")

func guardOwnedArmySave(dir string) error {
	entries, err := os.ReadDir(dir)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return fmt.Errorf("讀取存檔目錄：%w", err)
	}
	for _, entry := range entries {
		if strings.EqualFold(entry.Name(), "gamedata.ay.army.json") {
			return fmt.Errorf("%w；已在啟動原版程式前停止，保留 %s", ErrOwnedArmyHandoffPending, entry.Name())
		}
	}
	return nil
}
