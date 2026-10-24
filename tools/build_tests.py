# SPDX-License-Identifier: MPL-2.0
"""Compile engine/menu/storage regressions against the freshly built core."""
import argparse
import json
import subprocess
from pathlib import Path
from build import ROOT, limits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--build', type=Path, required=True)
    args = parser.parse_args()
    out = args.build.resolve()
    cross = str(args.sdk.resolve() / 'host/bin/mipsel-buildroot-linux-musl-')
    core = out / 'core'
    flags = ['-std=c++17', '-O2', '-fno-delete-null-pointer-checks',
             '-mips32r2', '-mplt', '-mno-shared',
             '-DPSXREC', '-DGPU_UNAI', '-DUSE_GPULIB', '-DSPU_PCSXREARMED']
    flags += ['-I' + str(path) for path in
              (core, core / 'src', core / 'src/port/rkgame', core / 'src/plugin_lib', ROOT / 'support')]
    library = str(core / 'libpcsx4all_rkgame.a')
    link = ['-no-pie', '-Wl,-Ttext-segment=0x40000000',
            '-Wl,--wrap=SDL_QueueAudio', '-lSDL2', '-lSDL2_ttf', '-lpng', '-lz', '-lm', '-lpthread', '-lrt']
    support = [str(ROOT / 'support' / name) for name in ('Input.cpp', 'Keymap.cpp', 'Log.cpp')]
    common = [cross + 'g++', *flags, '-include', str(ROOT / 'support/input-wire.h')]
    commands = [
        [cross + 'g++', *flags, str(ROOT / 'tests/readonly.cpp'), '-no-pie', '-lz', '-o', str(out / 'pcsx-readonly-test')],
        [*common, str(ROOT / 'tests/engine.cpp'), library,
         '-Wl,--wrap=malloc', *link, '-o', str(out / 'pcsx-recovery-engine')],
        [*common, str(ROOT / 'tests/production-menu.cpp'), *support, library,
         '-Wl,--wrap=SDL_Delay,--wrap=pcsx_load_game', *link, '-o', str(out / 'pcsx-recovery-menu')],
    ]
    with (out / 'tests-build.log').open('w') as log:
        for command in commands:
            log.write(json.dumps(command) + '\n')
            log.flush()
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, preexec_fn=limits)
    print('PASS compiled public-source regression programs:', out)


if __name__ == '__main__':
    main()
