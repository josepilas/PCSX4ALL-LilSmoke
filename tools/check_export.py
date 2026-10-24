# SPDX-License-Identifier: MPL-2.0
"""Verify source inventory, dependency pins and reproducible upstream patches."""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import tempfile
from build import ROOT

def sha(file):return hashlib.sha256(file.read_bytes()).hexdigest()
def main():
    inventory=json.loads((ROOT/'SOURCE-MANIFEST.json').read_text())
    for name,expected in inventory.items():
        file=(ROOT/name).resolve();assert file.is_relative_to(ROOT.resolve()),name
        assert sha(file)==expected,name
    for record in json.loads((ROOT/'third_party/SOURCES.json').read_text()):
        assert sha(ROOT/'third_party/distfiles'/record['archive'])==record['sha256']
    with tempfile.TemporaryDirectory(prefix='pcsx-source-check-') as temp:
        root=Path(temp)
        with tarfile.open(ROOT/'third_party/distfiles/pcsx4all-upstream-code-only.tar.gz') as archive:
            for member in archive.getmembers():
                assert member.isfile()
                relative=Path(member.name).relative_to('pcsx4all-upstream')
                file=(root/relative).resolve();assert file.is_relative_to(root)
                file.parent.mkdir(parents=True,exist_ok=True)
                file.write_bytes(archive.extractfile(member).read().replace(b'\r\n',b'\n'))
        with (ROOT/'patches/pcsx4all-local-vs-comparison.patch').open('rb') as patch:
            result=subprocess.run(['patch','--batch','-p1'],cwd=root,stdin=patch,capture_output=True)
        assert result.returncode==0,(result.stdout,result.stderr)
        count=0
        for file in (ROOT/'pcsx4all').rglob('*'):
            if not file.is_file():continue
            relative=file.relative_to(ROOT/'pcsx4all')
            assert (root/relative).read_bytes().replace(b'\r\n',b'\n')==file.read_bytes().replace(b'\r\n',b'\n'),relative
            count+=1
    subprocess.run(['python3',str(ROOT/'tools/release_gate.py')],check=True)
    print('PASS',len(inventory),'source inventory records, five dependency archives,',count,'patched PCSX files')

if __name__=='__main__':main()
