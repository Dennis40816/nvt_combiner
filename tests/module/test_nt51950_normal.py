from __future__ import annotations
from pathlib import Path
import os, subprocess, sys, tempfile, unittest
REPOSITORY_ROOT=Path(__file__).resolve().parents[2]; REFERENCE_EXE=Path(os.environ.get('NVT_COMBINER_LEGACY_ORACLE') or '.'); MODE='NT51950BASED_NORMAL_MODE'
def fixture(d: Path, method: str):
    b=bytearray(0x37000); b[0xA038:0xA03C]=(0x30000).to_bytes(4,'little'); b[0xA100:0xA104]=(0x10000).to_bytes(4,'little'); b[0xA108:0xA10C]=(3).to_bytes(4,'little'); b[0xA110:0xA114]=(0x20000).to_bytes(4,'little'); b[0xA118:0xA11C]=(3).to_bytes(4,'little'); b[0x10000:0x10004]=b'ILM!'; b[0x20000:0x20004]=b'DLM!'; b[0x30000:0x30780]=bytes(i%251 for i in range(1920)); d.joinpath('fw.bin').write_bytes(b); d.joinpath('block.bin').write_bytes(b'BLK!'); d.joinpath('map.txt').write_bytes(b''); return [MODE,method,'output.bin','fw.bin','block.bin','0x0','0x11000','4']
def run(cmd,cwd,env=None): return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=False,env=env)
class Test(unittest.TestCase):
 def test_matches_reference(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'r'; p=Path(t)/'p'; r.mkdir();p.mkdir()
   for method in ('CRC8','CRC32'):
    with self.subTest(method=method):
     a=fixture(r,method);fixture(p,method);x=run([str(REFERENCE_EXE),*a],r);e=os.environ.copy();e['PYTHONPATH']=str(REPOSITORY_ROOT/'src');y=run([sys.executable,'-m','nvt_combiner',*a],p,e);self.assertEqual(x.returncode,y.returncode,y.stdout+y.stderr);self.assertEqual(x.stdout,y.stdout);self.assertEqual(x.stderr,y.stderr);self.assertEqual(r.joinpath('output.bin').read_bytes(),p.joinpath('output.bin').read_bytes())
