from __future__ import annotations
from pathlib import Path
import os, subprocess, sys, tempfile, unittest
ROOT=Path(__file__).resolve().parents[2]; EXE=Path(os.environ.get('NVT_COMBINER_LEGACY_ORACLE') or '.')
def run(cmd,cwd,env=None): return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=False,env=env)
class Test(unittest.TestCase):
 def test_matches_reference(self):
  with tempfile.TemporaryDirectory() as t:
   r=Path(t)/'r';p=Path(t)/'p';r.mkdir();p.mkdir()
   for d in (r,p): d.joinpath('fw.bin').write_bytes(b'0123456789');d.joinpath('block.bin').write_bytes(b'WXYZ');d.joinpath('map.txt').write_bytes(b'')
   a=['CRC_Disable','fw.bin','block.bin','0x0','0x4','4'];x=run([str(EXE),*a],r);e=os.environ.copy();e['PYTHONPATH']=str(ROOT/'src');y=run([sys.executable,'-m','nvt_combiner',*a],p,e);self.assertEqual(x.returncode,y.returncode);self.assertEqual(x.stdout,y.stdout);self.assertEqual(r.joinpath('fw.bin').read_bytes(),p.joinpath('fw.bin').read_bytes())
