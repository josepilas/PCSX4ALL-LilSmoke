# SPDX-License-Identifier: MPL-2.0
"""Package a freshly built emulator; never reuse an internal runtime binary."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from build import ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def archive(path, files):
    with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as output:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,(2026,10,24,0,0,0))
            info.create_system=3;info.compress_type=zipfile.ZIP_DEFLATED
            executable=name.endswith('.sh') or name=='runtime/bin/pcsx4all'
            info.external_attr=(0o100755 if executable else 0o100644)<<16
            output.writestr(info,data)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--libraries',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    gate=json.loads((ROOT/'RELEASE_GATE.json').read_text())
    binary=(a.build/'pcsx4all').read_bytes()
    assert gate['publication_ready'] and not gate['blockers']
    assert gate['runtime_binary_sha256']==digest(binary)
    files={f.relative_to(ROOT/'app').as_posix():f.read_bytes()
           for f in (ROOT/'app').rglob('*') if f.is_file()}
    files['runtime/bin/pcsx4all']=binary
    files['runtime/defaults/pcsx4all.cfg']=files.pop('pcsx4all.cfg')
    for name in ('libSDL2-2.0.so.0','libSDL2_ttf-2.0.so.0','libfreetype.so.6','libpng16.so.16','libz.so.1'):
        data=(a.libraries/name).read_bytes()
        assert data.startswith(b'\x7fELF')
        files['runtime/lib/'+name]=data
    for f in (ROOT/'LICENSES').iterdir():
        if f.is_file():files['runtime/licenses/'+f.name]=f.read_bytes()
    for name in ('LICENSE','THIRD_PARTY_NOTICES.md','BUILD-EVIDENCE.json'):
        files['runtime/'+name]=(ROOT/name).read_bytes()
    info=json.loads((a.build/'build-info.json').read_text())
    info['commands']='See corresponding source build scripts and BUILD-EVIDENCE.json'
    info['bundled_libraries']={n:digest(data) for n,data in files.items() if n.startswith('runtime/lib/')}
    files['runtime/build-info.json']=(json.dumps(info,indent=2)+'\n').encode()
    files['SOURCE-OFFER.txt']=(
        'Complete corresponding source for PCSX4ALL-LilSmoke 0.0.1:\n'
        'https://github.com/josepilas/PCSX4ALL-LilSmoke/releases/download/0.0.1/corresponding-source.zip\n'
        'Public repository: https://github.com/josepilas/PCSX4ALL-LilSmoke\n'
        'Upstream licenses remain in runtime/licenses. Eligible authored files are MPL-2.0.\n'
        'No BIOS or commercial game data is distributed.\n').encode()
    assert len([n for n in files if '/' not in n and n.endswith('.sh')])==1
    assert 'meta.json' in files and len(files)==len({n.casefold() for n in files})
    archive(a.out/'PCSX4ALL-LilSmoke-0.0.1.lilpck',files)
    source={}
    for f in ROOT.rglob('*'):
        if not f.is_file():continue
        relative=f.relative_to(ROOT)
        if any(p in ('.git','out','__pycache__') for p in relative.parts):continue
        if f.suffix in ('.pyc','.o','.a','.so','.lilpck'):continue
        source['PCSX4ALL-LilSmoke/'+relative.as_posix()]=f.read_bytes()
    archive(a.out/'corresponding-source.zip',source)
    sums=''.join(digest(f.read_bytes())+'  '+f.name+'\n' for f in sorted(a.out.iterdir()) if f.is_file())
    (a.out/'SHA256SUMS.txt').write_text(sums)
    print(sums,end='')

if __name__=='__main__':main()
