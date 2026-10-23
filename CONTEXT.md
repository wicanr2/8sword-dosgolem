# 目前狀態

核對日期：2026-10-23。工作規則：[AGENTS.md](AGENTS.md)。歷程：[WORKLOG.md](WORKLOG.md)。

| 面向 | 現況與證據 |
|---|---|
| 目標 | 以 dosgolem 執行《神州八劍》，接入 HD 畫面及 HD 音樂；參考 mm3 的方法 |
| 授權 | 使用者已授權 Docker 存取與主機 gh 建立 GitHub 倉庫；畫風、音色、平台及公開方式尚未定案 |
| GitHub | [wicanr2/8sword-dosgolem](https://github.com/wicanr2/8sword-dosgolem)，主機 gh 認證為 wicanr2；遠端回讀確認 PRIVATE |
| 本機 Git | 已建立 `main`，`origin` 指向上述倉庫。提交身分沿用 mm3 的 Chun-Yu Wang、`wicanr2@gmail.com`，僅設定本案 |
| Docker | 已可列出映像及容器；以既有 `mm3-research:20261015-r1` 成功執行唯讀、無網路、非 root 的一次性檢查 |
| 工具能力 | 上述映像內為 UID/GID 1000:1000、Python 3.13.15，具 `/usr/bin/7z` 與 `/usr/bin/bsdtar`；尚未用本作封包驗證解包能力 |
| 原始輸入 | 根目錄有 `8sword.zip`、`珍092-神州八劍.rar`；尚未解包、計算 SHA-256 或辨識版本。已由 `.gitignore` 排除 |
| 參考入口 | 已查閱 mm3 的 AGENTS、CONTEXT 與音樂、呈現及效能規格，以及 dosgolem 的 README、CLAUDE；入口見 AGENTS |
| 已完成 | 專案規則、Docker 基本執行檢查、私人遠端倉庫與本機 Git 初始化 |
| 原版未知 | DOS 主程式、版本、素材格式、音樂介面與 dosgolem 相容性均未驗證，阻擋正式接入 |
| 可選打磨 | 尚未進入此階段；沒有已驗證的遊戲或 HD 資產 |
| 清理 | 一次性檢查使用 `--rm`，未建立新映像、研究目錄或轉檔產物；容器內擁有權檢查無 root-owned 檔案及誤建 `.md` 目錄 |

下一步在 Docker 中唯讀盤點兩份封包，固定來源雜湊與實際 DOS 主程式，再建立 dosgolem 冷啟動基線。目前沒有可啟動、可玩、音畫接入或對拍完成的聲明。
