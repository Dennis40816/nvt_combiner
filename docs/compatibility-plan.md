# 相容性優先重構計畫

## 已確認的現況

- 原始實作是私有 legacy C Combiner 1.13，版本 banner 為 `Combiner version:1.13.0.0`；參考原始碼不隨本 repo 發布。
- 主要檔案格式邏輯集中於單一 2,196 行 C 檔；共通 file helpers 在 `Utilities.c`。
- Python 與 PyInstaller 已可用，故 Python 實作與 Windows EXE packaging 不受工具鏈阻礙。
- 私有 legacy Combiner 1.13 參考 EXE 曾作為差分 oracle；不隨本 repo 發布。私有環境以 `NVT_COMBINER_LEGACY_ORACLE` 指定其絕對路徑。
- NT51929 的 no-overlay map 等效性已由 owner golden run 證實；詳見 [evidence](evidence/nt51929-no-overlay-map.md)。

## CLI contract inventory

以下為從 C source 與原始 `.bat` 取得的起始 inventory；實作前每一列都要以 reference EXE 再確認 stdout 與錯誤分支。

| Mode | 介面摘要 | C 的已知 arity 規則 |
| --- | --- | --- |
| `CRC_Enable` / `CRC32_Enable` / `CRC_Disable` | `<mode> <fw-in-out> <block> <src-hex> <dest-hex> <len-dec> ...` | `argc >= 7` 且 `argc` 為偶數 |
| `MERGE_MODE` | `<mode> <output> <block> <src-hex> <dest-hex> <len-dec> ...` | source 未先檢查 arity；須 characterization |
| `NT36672ABASED_MERGE_BIN_AND_GEN_CRC_MODE` | `<mode> <CRC8|CRC32> <output> <fw> <block> <src-hex> <dest-hex> <len-dec> ...` | `argc >= 9` 且 `argc` 為奇數 |
| `NT51927BASED_GEN_CRC_MODE` | `<mode> <CRC8|CRC32> <input> <output>` | total `argc == 5` |
| `NT51931BASED_NORMAL_MODE` | `<mode> <CRC8|CRC32> <output> <fw> <block tuple>...` | `argc >= 9` 且為奇數 |
| `NT51930BASED_NORMAL_MODE` | 同上 | `argc >= 9` 且為奇數 |
| `NT51932BASED_NORMAL_MODE` | 同上 | `argc >= 9` 且為奇數 |
| `NT51932BASED_MERGE_AB_MODE` | `<mode> <a-code> <b-code> <output> <b-offset>` | total `argc == 6` |
| `NT51950BASED_NORMAL_MODE` | 同上 | `argc >= 9` 且為奇數 |
| `NT51950BASED_MERGE_AB_MODE` | `<mode> <CRC8|CRC32> <a-code> <b-code> <output> <b-offset>` | total `argc == 7` |
| `NT51928BBASED_NORMAL_MODE` | `<mode> <CRC8|CRC32> <output> <fw> <block tuple>...` | `argc >= 9` 且為奇數 |

`block tuple` 的順序固定為 `<block_bin> <source_address> <destination_address> <length>`；source/destination 以 hex `strtol(..., 16)` 解析，length 以 decimal `strtol(..., 10)` 解析。不可為了改善 UX 改動這些既有定義。

## 已驗證的實作切片

`NT51932BASED_NORMAL_MODE` 已有一個可重建的 no-overlay differential case：`CRC8` 與 `CRC32` 都使用相同相對 argv，對 pinned 1.13 EXE 比較 process exit code、stdout、stderr、輸出 bytes 與 SHA-256。它只覆蓋 256 KiB、單 IC、正常 source range 的 synthetic firmware，並不宣稱 overlay map、cascade、malformed CLI 或其他 IC family 已相容。詳見 [module evidence](evidence/modules/nt51932-no-overlay.md)。

`NT51932BASED_MERGE_AB_MODE` 的成功 merge 與 A/B overlap failure 都已對 pinned EXE 做完整 process / console / file differential；詳見 [A/B module evidence](evidence/modules/nt51932-merge-ab.md)。

`NT51950BASED_MERGE_AB_MODE` 的 CRC8 / CRC32 header-CRC 路徑，以及 overlap failure 也已對 pinned EXE 做完整 differential；詳見 [NT51950 A/B evidence](evidence/modules/nt51950-merge-ab.md)。

`NT51927BASED_GEN_CRC_MODE` 的 common header、單一 M-IC linked flash header、ILM/DLM RAM CRC 和 flash-header CRC 已使用 CRC8 / CRC32 synthetic differential 驗證；詳見 [NT51927 evidence](evidence/modules/nt51927-crc.md)。

generic `CRC_Enable` / `CRC32_Enable` / `CRC_Disable` 已以 no-overlay synthetic case 對 pinned EXE 驗證；CRC-enabled case 覆蓋 CRC8、CRC32、two-header cascade，以及一個 ordinary `_ovly_table =` descriptor CRC 路徑。詳見 [generic normal evidence](evidence/modules/generic-normal.md)。

`NT36672ABASED_MERGE_BIN_AND_GEN_CRC_MODE` 已以沒有 map dependency 的 synthetic common-header case 對 pinned EXE 驗證；涵蓋 CRC8、CRC32 及 cascade header。詳見 [NT36672 evidence](evidence/modules/nt36672.md)。

`NT51931BASED_NORMAL_MODE` 已以 no-overlay synthetic case 對 pinned EXE 驗證；涵蓋 CRC8 / CRC32 的 common ILM/DLM、三段 firmware-header section、per-IC DLM diff 和 firmware-header CRC。詳見 [NT51931 evidence](evidence/modules/nt51931.md)。

`NT51930BASED_NORMAL_MODE` 已以 256 KiB no-overlay synthetic case 對 pinned EXE 驗證；涵蓋 IC-count buffer size、FwConfig 位置計算、`NVT` end flag，以及 CRC8 / CRC32 的 ILM/DLM、DLM diff、header CRC。詳見 [NT51930 evidence](evidence/modules/nt51930.md)。

`NT51928BBASED_NORMAL_MODE` 已以 no-overlay synthetic case 對 pinned EXE 驗證；涵蓋固定 `0x3E000` 的 1920-byte FwConfig 複製，以及 CRC8 / CRC32 的 `0xDxxx` ILM/DLM/header CRC。詳見 [NT51928B evidence](evidence/modules/nt51928b.md)。

上述五個 map-based normal families 都另有 ordinary `_ovly_table =` descriptor 的 CRC8 / CRC32 differential case，及 HostDL/Process `OverlayDLMaddr` 的 CRC8 differential case；generic normal 的 HostDL branch 另涵蓋 CRC32。多 descriptor table 目前有 generic normal differential case，尚未逐 IC family 展開。

## 提交與驗收節點

1. **Baseline（已完成）**：於私有環境凍結 legacy 參考、保護 firmware artifacts、記錄 CLI inventory 與參考 EXE；私有參考不隨本 repo 發布。
2. **Function-first（已固定）**：一次只移植一個 C function 或語意 primitive（CRC、little-endian access、`strtol`、block copy、map text records）。每個 primitive 都先有獨立 unit vectors，通過後以獨立 commit 固定；不得以 module success 取代 function-level evidence。
3. **Architecture after primitives（已完成初版）**：以已固定的 primitives 重整 `src/nvt_combiner/` 模組邊界與依賴方向；後續只可在既有相容切片內做小範圍 primitive 修正。
4. **Module / differential tests（持續執行）**：架構固定後，以可重建 synthetic fixture 搭配 reference EXE 驗證每個新增切片；二進位、exit code 與 console output 都必須通過。
5. **Normal families**：每個 IC family 一個獨立 commit，附 synthetic case 與至少一個本機 differential report 的 SHA-256 摘要。
6. **Release**：所有被宣告支援的 mode 都在 Python 與 `dist/Combiner.exe` 上通過 byte-level differential gate，才建立 release tag。

## Differential gate

每一 case 都必須執行下列序列：

1. 複製相同的 input 到 `artifacts/reference/<case>` 與 `artifacts/python/<case>`。
2. 各自以**完全相同的 interface args** 執行 legacy EXE 與 Python 版；兩邊只替換 executable path。
3. 比較 return code、stdout、stderr、output 檔有無、檔案長度和 SHA-256。
4. 若輸出不同，儲存第一個 byte offset 與前後 32 bytes 的 hex diff；不得接受「CRC 看起來對」作為通過。
5. Python version 通過後，再以同一 case 比較 PyInstaller 產出的 `Combiner.exe`。

## Git discipline

- 一個 commit 只移植一個可驗收單位；commit message 使用 `feat(mode): ...` 或 `test(mode): ...`。
- 不提交 firmware BIN、golden output、VS build artifacts 或 credentials；私有 legacy 參考程式不得提交；差分測試從 `NVT_COMBINER_LEGACY_ORACLE` 取得。
- 每個行為修正都要在 commit body / `docs/` 說明：reference source location、case、輸出 SHA-256、已知未覆蓋分支。
- `Combiner.exe` 的既有 positional CLI 不可新增旗標。使用者指定的 `--overlay-map-txt` 僅由獨立 `nvt-combiner-postbuild` wrapper 接受，負責暫存/還原 legacy 所讀取的 `map.txt`；它絕不進入 final `Combiner.exe` 的 selector 或 public args。
