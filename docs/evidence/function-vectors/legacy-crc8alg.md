# Legacy `CRC8Alg` characterization vectors

These vectors isolate the first C function being ported. They were obtained by
running the private legacy Combiner 1.13 oracle with a generated valid
`NT51932BASED_NORMAL_MODE CRC8` no-overlay fixture.

| Function input bytes | Address | Size code | Expected result |
| --- | ---: | ---: | ---: |
| `00 01 ... 0F` | `0x10000` | `0x0F` | `0xA97AFF4D` |
| `A0 A1 ... AF` | `0x11000` | `0x0F` | `0x3C1D5899` |
| `FF` repeated 16 times | `0x10000` | `0x0F` | `0xA79C3203` |
| `55` repeated 16 times | `0x11000` | `0x0F` | `0xF8FD261C` |
| `FF FE ... F0` | `0x10000` | `0x0F` | `0x5BCBEF86` |
| `0F 0E ... 00` | `0x11000` | `0x0F` | `0x841F9BB8` |

The source C loop is `for (i = addr; i <= addr + size; i++)`; consequently
`size` is an inclusive size code, not a Python length. The fixture command
returned `0`, and its full output SHA-256 was
`031b3439ae9a758353b1666fecad1b7a86ad9d3546f72cd988bb89359f961b08`.

Only the function vectors are committed at this point. No CLI dispatcher,
NT51932 module, output writer, or module-level differential test is permitted
until the function primitive has passed review and been fixed in Git.

## Legacy `CRC32Alg` vectors

`CRC32Alg` is verified separately. Its `byte_count` is not a size code;
`CalCrc` invokes it with `size_code + 1`.

| Function input bytes | Byte count | Expected result |
| --- | ---: | ---: |
| `00 01 ... 0F` | `16` | `0x081B46CA` |
| `A0 A1 ... AF` | `16` | `0x9D7CE11E` |
| `00 01` | `2` | `0x151D1CA7` |
| `A0 A1 A2` | `3` | `0x92EF2E79` |

The partial-word vectors prove the legacy-specific zero-padding behavior.
