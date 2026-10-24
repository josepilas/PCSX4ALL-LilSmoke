# SPDX-License-Identifier: MPL-2.0
"""Rebuild bundled libraries from the included archives into a private sysroot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
from build import ROOT, limits


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.resume and not (args.out/'build.log').is_file():
        raise SystemExit('Not a recognized dependency build directory')
    args.out.mkdir(parents=True,exist_ok=args.resume)
    sdk=args.sdk.resolve();out=args.out.resolve();dest=out/'sysroot'
    records=json.loads((ROOT/'third_party/SOURCES.json').read_text())
    configurations={r['package']:r for r in json.loads((ROOT/'third_party/configure-evidence.json').read_text())}
    env=os.environ.copy();cross=str(sdk/'host/bin/mipsel-buildroot-linux-musl-')
    env.update(CC=cross+'gcc',CXX=cross+'g++',AR=cross+'ar',RANLIB=cross+'ranlib',STRIP=cross+'strip',
        CFLAGS='-O3 -g0 -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64',
        CXXFLAGS='-O3 -g0 -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64',
        CPPFLAGS='-I'+str(dest/'usr/include'),LDFLAGS='-L'+str(dest/'usr/lib')+' -Wl,-rpath-link,'+str(dest/'usr/lib'),
        PKG_CONFIG=str(sdk/'host/bin/pkgconf'),PKG_CONFIG_SYSROOT_DIR=str(sdk/'staging'),
        PKG_CONFIG_LIBDIR=str(sdk/'staging/usr/lib/pkgconfig'),SOURCE_DATE_EPOCH='1792800000')
    commands=[];built=[]
    def relocate_libtool():
        # DESTDIR is a staging prefix, not a target path in libtool metadata.
        for file in (dest/'usr/lib').glob('*.la'):
            text=file.read_text()
            text=text.replace(' /usr/lib/',' '+str(dest/'usr/lib')+'/')
            text=text.replace("libdir='/usr/lib'","libdir='"+str(dest/'usr/lib')+"'")
            file.write_text(text)
    installed={'libzlib':'libz.so.1','libpng':'libpng16.so.16','freetype':'libfreetype.so.6',
        'sdl2':'libSDL2-2.0.so.0','sdl2_ttf':'libSDL2_ttf-2.0.so.0'}
    relocate_libtool()
    with (out/'build.log').open('a' if args.resume else 'w') as log:
        def run(command,cwd):
            commands.append(command);log.write(json.dumps(command)+'\n');log.flush()
            subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,preexec_fn=limits)
        for package in ('libzlib','libpng','freetype','sdl2','sdl2_ttf'):
            record=next(r for r in records if r['package']==package)
            archive=ROOT/'third_party/distfiles'/record['archive']
            assert hashlib.sha256(archive.read_bytes()).hexdigest()==record['sha256']
            if args.resume and (dest/'usr/lib'/installed[package]).is_file():
                built.append(package);continue
            work=out/package
            fresh=not work.exists();work.mkdir(exist_ok=args.resume)
            if fresh:
                with tarfile.open(archive) as tar:tar.extractall(work,filter='data')
            source=next(d for d in work.iterdir() if d.is_dir())
            for patch in sorted((ROOT/'patches'/package).rglob('*.patch')):
                if not fresh:continue
                # Generated headers are recreated by configure.
                if patch.name in ('SDL_config.h.patch','zconf.h.patch'):continue
                run(['patch','-p1','--input',str(patch)],source)
            if package=='libzlib':
                configure=['--prefix=/usr','--shared']
                env['CHOST']='mipsel-buildroot-linux-musl'
            else:
                row=next(r for r in configurations[record['version_directory']]['configure'] if r.lstrip().startswith('set X'))
                words=shlex.split(row)
                configure=[]
                for word in words[4:]:
                    if word.startswith('$'):break
                    if '=' not in word or word.startswith('--'):configure.append(word)
                # SDL tests/examples are not shipped or linked.
                if package=='sdl2':configure+=['--disable-sdl2-config','--disable-sdltest','--disable-test']
            run(['./configure',*configure],source)
            run(['make','-j1'],source)
            run(['make','-j1','DESTDIR='+str(dest),'install'],source)
            relocate_libtool()
            built.append(package)
    report=dict(passed=True,built=built,sdk_modified=False,cpus=1,nice=10,compiler_as_limit=805306368,
        commands=commands,outputs={str(f.relative_to(dest)):hashlib.sha256(f.read_bytes()).hexdigest()
            for f in (dest/'usr/lib').glob('*.so.*') if f.is_file()})
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS dependencies rebuilt only in private sysroot:',dest)

if __name__=='__main__':main()
