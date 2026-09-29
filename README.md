# nvt_combiner

以 Python 改寫舊版 Novatek Combiner 的相容性優先專案。目標是在**不改變現有 CLI interface args** 的前提下，輸出與舊版 C `Combiner.exe` 一致的行為，並可打包為 Windows `Combiner.exe`。

目前獨立產品版本與 Windows EXE 檔案版本皆為 **2.0.0.1**；console banner 則保留 legacy `1.13.0.0` 以維持相容性。詳見[版本策略](docs/release-versioning.md)。

目前已完成 generic `CRC_Enable` / `CRC32_Enable` / `CRC_Disable`、`NT36672ABASED_MERGE_BIN_AND_GEN_CRC_MODE`、`NT51928BBASED_NORMAL_MODE`、`NT51930BASED_NORMAL_MODE`、`NT51931BASED_NORMAL_MODE`、受限的 NT51932 vertical slices、NT51950 normal/A-B、`NT51927BASED_GEN_CRC_MODE`，以及 `MERGE_MODE` 的 differential cases。它們不代表其他 mode 已完成移植；完整支援邊界見 [module evidence](docs/evidence/modules)。

每一個目前支援的 selector 都另有 PyInstaller EXE release gate；詳見 [packaged evidence](docs/evidence/packaged-release-gate.md)。

需要明確提供 overlay map 的呼叫端可使用獨立的 [`--overlay-map-txt` postbuild wrapper](docs/overlay-map-wrapper.md)；它不改變 `Combiner.exe` 的 legacy args。

## Repository layout

- `docs/architecture.md`：Python 模組分層與 PyInstaller 發行方案。
- `docs/compatibility-plan.md`：CLI contract、差分測試與逐 mode 的驗收順序。

韌體 BIN、既有輸出 BIN 與 Visual Studio build artifacts 未放入 repository；它們可能是私有 golden data，且差分測試會在本機受控的 `artifacts/` 產生。

## Public snapshot and private oracle

本公開快照由私有 intake `2.0.0.1` (`d7b08b9`) 建立，僅包含 Python 版及其測試、文件。私有 legacy Combiner 1.13 C 原始碼與參考 EXE 不隨本 repo 發布；相容性結論保留於 `docs/evidence/`。

在有權使用私有參考程式的環境中，將 `NVT_COMBINER_LEGACY_ORACLE` 設為該 EXE 的絕對路徑，再執行 `python -m pytest`，即可執行既有差分測試。未設定或檔案不存在時，依賴該 oracle 的測試會 skip 並說明原因；一般 Python 測試仍可執行。私有參考程式與實際韌體資料請勿加入本 repo。

請先閱讀 [架構](docs/architecture.md) 與 [相容性計畫](docs/compatibility-plan.md) 再開始實作。
