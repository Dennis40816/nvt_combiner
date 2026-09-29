from __future__ import annotations
from pathlib import Path
import sys, unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from nvt_combiner.primitives.header import decode_one_header_size
class Test(unittest.TestCase):
 def test_decodes_first_zero_bin_section(self):
  b=bytearray(0x80);b[:4]=(0x80).to_bytes(4,'little');b[0x34:0x38]=(3).to_bytes(4,'little');self.assertEqual(4,decode_one_header_size(b))
 def test_returns_none_without_section(self):
  b=bytearray(0x80);b[:4]=(0x80).to_bytes(4,'little');b[0x34:0x38]=(3).to_bytes(4,'little');b[0x38:0x3c]=(1).to_bytes(4,'little');self.assertIsNone(decode_one_header_size(b))
