# 工作歷程

目前狀態以 [CONTEXT.md](CONTEXT.md) 為準，規則與研究入口見 [AGENTS.md](AGENTS.md)。

## 2026-10-23：建立專案規則

- 使用者要求參考 mm3，為《神州八劍》規劃 dosgolem、HD 畫面與 HD 音樂，先產生 AGENTS.md。
- 載入復古重製技能、文件職責及必要參考，建立專案規則與下一條工作鏈。
- 當時沙箱無法存取 Docker socket，提權被權限政策拒絕。Git 回報非倉庫，當時的 `.git` 為環境管理的唯讀目錄，未作變更。
- 僅確認兩份來源壓縮檔存在，未解包或執行遊戲，未建立容器。

## 2026-10-23：Docker 授權與 GitHub 建倉

- 使用者追加授權 Docker 存取與主機 gh 建倉；目前環境已解除先前沙箱限制。
- 主機 `/home/anr2/.local/bin/gh auth status` 成功，登入 wicanr2。建立私人倉庫 `wicanr2/8sword-dosgolem`，隨後遠端回讀確認 PRIVATE。建倉時沒有上傳原版素材。
- Docker 映像及容器列舉成功。檢查既有 `mm3-research:20261015-r1` 設定，沿用該映像；未建立重複工具鏈。
- 容器 `8sword-environment-check-20261023` 使用 `--rm`、30 秒外層逾時、128 MiB 記憶體、0.5 CPU、64 程序上限、UID/GID 1000:1000、無網路、唯讀檔案系統與唯讀專案掛載。Python 3.13.15、7z、bsdtar 檢查通過；擁有權及誤建目錄檢查無輸出。
- 容器基本檢查不代表本作已能解包或執行。此輪未處理來源內容、音畫或遊戲測試。
- 在已無環境保留目錄的工作區初始化本機 Git，建立 `main` 與 `origin`。參考 mm3 現有 Git 身分，僅設定本案為 Chun-Yu Wang、`wicanr2@gmail.com`。
- 新增 `.gitignore` 排除兩份原始壓縮檔、研究與交付目錄。建立 CONTEXT 保存現況、WORKLOG 保存歷程，並從 AGENTS 掛入入口；不建立其他空白文件或研究目錄。
- 初始同步範圍為 AGENTS.md、CONTEXT.md、WORKLOG.md 與 .gitignore。提交與推送結果於遠端核對後追加。
- 未完成事項：來源雜湊、版本辨識、dosgolem 冷啟動、HD 音畫樣本與方向確認。

### 初始推送核對

- 初始提交 `46ff80b2c73acc7145f56e6ccde06da7c6e1f551` 已推送至 `origin/main`，`git ls-remote` 回讀與本機 HEAD 一致。
- 主機 gh 讀回遠端樹，確認只有上述四份文件與設定，沒有 ZIP、RAR 或其他原版素材。兩份來源封包的忽略規則均生效。
- 暫存變更的空白檢查通過，文件擁有者均為 UID/GID 1000:1000。`docker ps -a --filter name=8sword` 無輸出，本案沒有殘留容器。
