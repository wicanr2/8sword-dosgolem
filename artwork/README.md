# 定稿原圖永久保存

完整原圖的現行入口是本目錄的 `approved/masters/`。它位於專案根目錄，與可清理的 `workplace/` 分開。定稿圖、正式採用的圖像、完整提示及來源收據均按原始位元組保存。

| 內容 | 路徑 | 檔數 |
|---|---|---|
| 定稿與正式採用的美術主檔 | `approved/masters/` | 132 |
| 完整提示 | `approved/provenance/` | 175 |
| 生成與來源收據 | `approved/provenance/` | 127 |
| 提示引用的參考輸入 | `approved/references/` | 82 |
| 正式r64的圖像輸入 | `approved/registration-r64/` | 231 |
| 正式r64的圖像清單與相關輸入 | `approved/registration-r64/` | 227 |

合計974檔、450810751 bytes，約430 MiB。主檔包含完整圖集及一份可編輯SVG，不把裁切材質當成唯一原圖。參考輸入與正式組保留的歷史檔分別標示，不冒稱它們都是新增定稿。

[完整檔案清單](manifest.json)逐檔保存原路徑、永久路徑、SHA-256、大小、用途及圖片形狀。[匯入計畫](archive-plan-r1.json)固定本次來源；[獨立核對收據](verification-detached-r1.json)是在完全沒有掛載workplace的Docker內重驗全部974檔。永久檔案是獨立複本，沒有指回研究區的符號連結或共用inode。

| 主檔類別 | 檔數 |
|---|---|
| 軍隊人物 | 1 |
| 部隊圖集、戰場、遭遇與效果 | 55 |
| 結局 | 11 |
| 器物與武器 | 16 |
| 地圖建築與靜物 | 14 |
| 開場博物館、人物及女主角 | 7 |
| 海報 | 2 |
| 已批准風格與可編輯發行商圖案 | 3 |
| 故事前導與背景 | 2 |
| 地表、介面、動作與主角肖像 | 21 |

完整PNG與本機來源輸入放在Git排除的 `approved/`。Git保存本索引、清單、提示所在路徑與核對工具；README比較圖及已批准參考圖仍沿原私人倉庫範圍保存。此目錄不是公開發行包，也沒有變更原版素材的權利分類。

新圖確認或正式採用後，先把完整原PNG及完整提示保存到此處的新版本路徑，更新清單並核對，再將workplace副本視為可清理。未定稿的試作可留研究區。歷史收據中的workplace路徑維持原樣，透過清單的 `source` 與 `path` 找到永久複本。不要以縮小比較圖取代原圖，不重新編碼或覆寫舊定稿。

[保存與核對工具](../tools/archive-approved-art.py)在固定Pillow11.3.0容器執行。只驗證永久檔案時，不需要原版遊戲、Go工具鏈或workplace：

```bash
timeout 60s docker run --rm --network none \
  --user 1000:1000 --memory 768m --cpus 2 --pids-limit 64 \
  -v /home/anr2/cht/8sword/artwork:/archive:ro \
  -v /home/anr2/cht/8sword/tools:/tools:ro \
  --entrypoint python sc-cht-hdtools:pillow11.3.0-r1 \
  /tools/archive-approved-art.py --archive /archive --verify
```

本目錄保存美術。程式、音樂、字型、存檔與其他必要研究資料已於2026-10-28另完成[永久保存與還原核對](../preserved/README.md)，原workplace副本尚未刪除。
