# NT51950 normal-mode gate

The unchanged interface `NT51950BASED_NORMAL_MODE <CRC8|CRC32> <output> <fw> <block tuple>...` is verified for a no-overlay fixture. The differential test covers map discovery, block copy, FWConfig copy from `0xA038` to `0x36000`, ILM/DLM CRCs, and the `0xA100` header CRC for both CRC methods.

`tests/module/test_nt51950_overlay.py` now covers one ordinary
`_ovly_table =` descriptor CRC for both methods:

| CRC method | Reference overlay output SHA-256 |
| --- | --- |
| CRC8 | `ae06949ccc01ebc0e983e539fdad9b07a878c6dee04900f38fa3fd071cbc3bbb` |
| CRC32 | `1bd5e8591c3782223b163b172ee269de9de9feac189be8b42292314dd2f3f973` |

Still excluded: HostDL/Process `OverlayDLMaddr` mutation, invalid source
ranges and legacy uninitialised allocation gaps beyond supplied input.
