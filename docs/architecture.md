# 初版 Python 架構

## 設計原則

此專案的正確性定義是 legacy `Combiner.exe` 的外部可觀測行為，不是重新設計 firmware format。每一個 mode 都以相同 argv 對私有 legacy Combiner 1.13 oracle 比對 exit code、stdout/stderr 與完整 output bytes。私有參考不隨本 repo 發布，測試環境以 `NVT_COMBINER_LEGACY_ORACLE` 提供。只有通過差分測試的 mode 才能標示為支援。

CLI 不採用 `argparse`：它會改變缺參數、未知 mode 與數值解析的行為。第一層只接收原始 `sys.argv[1:]`，保留 selector、參數順序、十六進位/十進位基底與既有輸出訊息。

## 實際目錄與依賴方向

```text
src/nvt_combiner/
  primitives/       # 先以 unit tests 固定、不可依賴 modes
    crc.py          # bit-for-bit CRC8 / CRC32
    c_semantics.py  # strtol、uint32、little-endian read/write
    files.py        # binary I/O、atomic replace 與可診斷的 write failure
    safety.py       # exact-range validation 與不會改變 buffer 大小的 copy
    map_text.py     # MSVC text-mode CRLF 與 500-byte fgets records
    result_codes.py # legacy 0 / -1 / 1 process result vocabulary
    checksum.py     # legacy CalCrc method dispatch
    header.py       # common-header size decode
    normal_crc.py   # generic / NT36672 common-header CRC fields
    nt51930_crc.py
    nt51931_crc.py
    nt51928b_crc.py
  __main__.py       # 僅呼叫 cli.main
  cli.py            # banner、raw argv、mode dispatch
  postbuild.py      # optional --overlay-map-txt wrapper；不改變 Combiner argv
  modes/
    legacy_io.py    # map/block/buffer 與 normal preamble 的共用流程
    normal.py       # CRC_Enable / CRC32_Enable / CRC_Disable
    merge.py        # MERGE_MODE
    nt36672.py
    nt51927.py
    nt51928b.py
    nt51930.py
    nt51931.py
    nt51932.py
    nt51950.py
```

`primitives/` 是最低層：每個 C function 先有獨立 unit vectors，並在 mode 實作開始前以獨立 commit 固定。`modes/legacy_io.py` 只集中 C 共通且已有差分證據的 map/block/normal-preamble 行為；其餘 `modes/` 只協調各 IC family 的固定 offset、buffer 大小與 CRC 寫入順序。`primitives/` 不得反向 import modes。

`modes.nt51932` 提供已差分驗證的 `map.txt` lookup 和 block tuple 讀取小工具；其他 normal modes 共用它們。generic、NT51928B、NT51930、NT51931、NT51932 與 NT51950 normal modes 都已各自差分驗證 ordinary overlay descriptor path，以及 CRC8 的 HostDL/Process `OverlayDLMaddr` path。generic mode 的 HostDL path 另涵蓋 CRC8 與 CRC32；各 family 的一般 overlay CRC8/CRC32 path 也各自有 differential gate。

## CLI dispatcher

目前 C `main` 的 selector 均有 handler：

| Selector | Python handler |
| --- | --- |
| `MERGE_MODE` | `modes.merge` |
| `NT36672ABASED_MERGE_BIN_AND_GEN_CRC_MODE` | `modes.nt36672` |
| `NT51927BASED_GEN_CRC_MODE` | `modes.nt51927` |
| `CRC_Enable`, `CRC32_Enable`, `CRC_Disable` | `modes.normal` |
| `NT51931BASED_NORMAL_MODE` | `modes.nt51931` |
| `NT51930BASED_NORMAL_MODE` | `modes.nt51930` |
| `NT51932BASED_NORMAL_MODE`, `NT51932BASED_MERGE_AB_MODE` | `modes.nt51932` |
| `NT51950BASED_NORMAL_MODE`, `NT51950BASED_MERGE_AB_MODE` | `modes.nt51950` |
| `NT51928BBASED_NORMAL_MODE` | `modes.nt51928b` |

對 C 的未定義行為（例如完全沒有 `argv[1]`、越界 pointer 或未初始化 allocation gap）不臆測相容；會明確記錄為不受支援的 malformed invocation，避免把 crash 當成產品契約。

## Binary semantics

Python 明確實作 C 的 little-endian、`uint32_t` wraparound、size-code（含/不含末位元組）與覆寫順序。不可用 dataclass 序列化取代原始位址操作；只可使用明確 `<I` helper。

對所有 reference EXE 可成功處理的有效輸入，copy/CRC 的長度、覆寫順序、console 與 output bytes 維持完全一致。對 C 原本會越界讀寫或進入 undefined behavior 的 malformed range，Python 會在任何 output replace 前拒絕，log 包含 operation context、start、length、end、buffer size 與 available bytes。長度為 0 的 legacy copy 仍是 no-op，即使舊 argv 保留了非零 source address。

所有正式 output 先寫入同目錄暫存檔，完成 write、flush 與 `fsync` 後才用 `os.replace` 原子替換；失敗時保留既有 output。詳細保護與測試證據見 [write-safety.md](evidence/write-safety.md)。

## Test architecture

```text
tests/
  unit/       # 每個 primitive 的 vectors、stdout 與寫回位置
  module/     # synthetic fixture：reference EXE、Python 與 postbuild wrapper 差分
  packaged/   # COMBINER_EXE 指向 PyInstaller EXE 時的 release gate
```

每個差分案例在互不影響的 temporary work directory 各跑一次。預設逐字比較 stdout/stderr、process return code 與完整 output bytes；任何一 byte 不同即失敗。fixture 只使用可重建的 synthetic data，私有 firmware 與 golden BIN 保留在 repository 外。

## EXE 發行

以 `pyproject.toml` 建立 wheel，並以 PyInstaller 打包：

```powershell
pyinstaller --clean --noconfirm --onefile --name Combiner --paths src `
  --distpath artifacts\pyinstaller\dist --workpath artifacts\pyinstaller\work `
  --specpath artifacts\pyinstaller\spec src\nvt_combiner\__main__.py
```

`tests/packaged/test_supported_modes.py` 要求對該 EXE（不是只對 `python -m`）重跑每一個已支援 selector 的成功 case；reference EXE、stdout/stderr 和 output bytes 均為 gate。

分支層級的架構優化決策與刻意延後的高風險項目記錄於
[architecture-optimization.md](architecture-optimization.md)。
