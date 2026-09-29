# 第二階段重構審查

## 已完成的可讀性改善

- `result_codes.py` 以 `RUNTIME_SUCCESS`、`RUNTIME_FAIL`、`IO_FAIL` 與
  `INPUT_FAIL` 表達 legacy process status，數值仍分別是 `0`、`-1`、`1`
  與 `1`。
- mode 的 return 與 file-helper status comparison 已移除 magic numbers；CRC
  計算、offset、size code 等資料值不套用這些名稱。

## 已收斂的流程

`modes/legacy_io.py` 是唯一的共用 orchestration helper：

- `open_legacy_map`：同層 `map.txt` 後再 `output\\map.txt` 的 lookup 與
  原 console text；
- `read_validated_overlay_map`：text-mode map decode 與 overlay validation；
- `read_legacy_blocks`：block open、legacy `strtol` 與逐列 table output；
- `merge_firmware_and_blocks`：動態大小 buffer 的 copy order；
- `prepare_map_based_normal_input`：map → arity → firmware → blocks 的 C
  可觀察順序，以及原本不同的 `-1` / `1` failure status。

generic、NT51928B、NT51930、NT51931、NT51932 與 NT51950 normal modes 現在使用
同一前置流程。

## 刻意保留在 IC mode 的邏輯

以下內容不以 callback 或設定表強行抽象，因為會掩蓋 firmware-specific 的寫入
順序，或尚未有足夠共同的 reference evidence：

- 固定/動態 output buffer 尺寸與 IC count 分支；
- FwConfig copy、NVT end flag 與各 family 的 header/DLM offset；
- CRC header 與 overlay descriptor 的順序；
- NT51927 CRC-only、MERGE_MODE，以及 NT51932/NT51950 A/B merge。

## 驗收

本輪每個 helper 都先有 unit test，再搬移 mode。`7cbf4b1` 時完整驗證為
54 unit tests、37 reference differential module tests，以及 `compileall` 通過。
