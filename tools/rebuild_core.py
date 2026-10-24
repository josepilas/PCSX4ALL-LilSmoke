# SPDX-License-Identifier: MPL-2.0
"""Core-only source rebuild; no prebuilt archive, OS install or downloads."""
import argparse
import os
from pathlib import Path
import resource
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--sdk', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
work = root / 'out/core'
if work.exists():
    raise SystemExit('out/core exists; preserve/inspect that build before retrying')
shutil.copytree(root / 'pcsx4all', work)
cross = a.sdk.resolve() / 'host/bin/mipsel-buildroot-linux-musl-'


def limits():
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {available[1] if len(available) > 1 else available[0]})
    os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)


flags = '-O3 -g0 -mips32r2 -mtune=74kc -mfp32 -mhard-float -mplt -mno-shared -fno-delete-null-pointer-checks'
raise SystemExit(subprocess.run(['make', '-j1', '-C', str(work), '-f', 'Makefile.rkgame',
    'NO_SDL=1', 'SOUND_DRIVERS=sdl2', 'CROSS_COMPILE=' + str(cross),
    'EXTRA_CFLAGS=' + flags], preexec_fn=limits).returncode)
