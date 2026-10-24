# SPDX-License-Identifier: MPL-2.0
"""Build the complete emulator from this export; never install into the SDK."""
import argparse
import calendar
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def limits():
    cpus = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {cpus[1] if len(cpus) > 1 else cpus[0]})
    os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS, (805306368, 805306368))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sdk', type=Path, required=True)
    p.add_argument('--out', type=Path, default=ROOT / 'out')
    p.add_argument('--library-root', type=Path, help='optional separately rebuilt dependency sysroot')
    p.add_argument('--resume', action='store_true', help='resume this tool\'s existing generated build')
    a = p.parse_args()
    out = a.out.resolve()
    if out.exists() and not a.resume:
        raise SystemExit('Output already exists; use a fresh build directory')
    if a.resume and not ((out / 'core/Makefile.rkgame').is_file() and (out / 'build.log').is_file()):
        raise SystemExit('Not a recognized generated PCSX build directory')
    sdk = a.sdk.resolve()
    cross = str(sdk / 'host/bin/mipsel-buildroot-linux-musl-')
    out.mkdir(parents=True, exist_ok=a.resume)
    shutil.copytree(ROOT / 'pcsx4all', out / 'core', dirs_exist_ok=a.resume)
    os.environ['SOURCE_DATE_EPOCH'] = str(calendar.timegm((2026, 10, 24, 0, 0, 0)))
    flags = '-O3 -g0 -mips32r2 -mtune=74kc -mfp32 -mhard-float -mplt -mno-shared -fno-delete-null-pointer-checks'
    commands = [['make', '-j1', '-C', str(out / 'core'), '-f', 'Makefile.rkgame',
                 'NO_SDL=1', 'SOUND_DRIVERS=sdl2', 'CROSS_COMPILE=' + cross, 'EXTRA_CFLAGS=' + flags]]
    library_flags = []
    if a.library_root:
        library_flags = ['-I' + str(a.library_root / 'usr/include'),
                         '-I' + str(a.library_root / 'usr/include/SDL2'),
                         '-L' + str(a.library_root / 'usr/lib'),
                         '-Wl,-rpath-link,' + str(a.library_root / 'usr/lib')]
    sources = [out / 'core/pcsx4all-launch.cpp', out / 'core/native-menu.cpp']
    sources += [ROOT / 'support' / name for name in ('Input.cpp', 'Keymap.cpp', 'Log.cpp')]
    commands.append([cross + 'g++', *flags.split(), '-std=c++17', '-include', str(ROOT / 'support/input-wire.h'),
                     '-I' + str(ROOT / 'support'), '-I' + str(out / 'core/src/port/rkgame'),
                     *library_flags, *map(str, sources), str(out / 'core/libpcsx4all_rkgame.a'),
                     '-no-pie', '-Wl,-Ttext-segment=0x40000000', '-lSDL2', '-lSDL2_ttf', '-lpng', '-lz',
                     '-lm', '-lpthread', '-lrt', '-o', str(out / 'pcsx4all')])
    commands.append([cross + 'strip', str(out / 'pcsx4all')])
    with (out / 'build.log').open('a' if a.resume else 'w') as log:
        for command in commands:
            log.write(json.dumps(command) + '\n'); log.flush()
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, preexec_fn=limits)
    report = {'built_from_exported_source': True,
              'compiler': subprocess.check_output([cross + 'g++', '--version'], text=True).splitlines()[0],
              'binary_sha256': hashlib.sha256((out / 'pcsx4all').read_bytes()).hexdigest(),
              'core_sha256': hashlib.sha256((out / 'core/libpcsx4all_rkgame.a').read_bytes()).hexdigest(),
              'cpu_count': 1, 'preferred_cpu': 1, 'nice': 10, 'compiler_as_limit': 805306368,
              'sdk_mutated': False, 'commands': commands}
    (out / 'build-info.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'commands'}, indent=2))


if __name__ == '__main__':
    main()
