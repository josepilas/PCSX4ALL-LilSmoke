# Building PCSX4ALL-LilSmoke

Use Linux, Python 3.12+, GNU make, patch, and a MIPS32r2 little-endian o32,
FP32 hard-float musl cross-toolchain. The qualified SDK is Buildroot 2024.02.3
with GCC 12.3.0. SDL requires the platform's DirectFB/ALSA development interfaces;
these OS interfaces and the cross-toolchain are not bundled firmware.

## Dependencies

All five bundled dependency source archives are in third_party/distfiles, with
SHA256 pins in third_party/SOURCES.json. Build them and apply included changes:

```sh
python3 tools/build_dependencies.py --sdk /path/buildroot/output --out /tmp/pcsx-deps
```

This extracts only into the new output directory, applies non-generated source
patches, uses the recorded configure options and regenerates configuration
headers. zlib, PNG, FreeType, SDL2 and SDL2_ttf install only into the private
`/tmp/pcsx-deps/sysroot`, never the SDK. Generated-header deltas are retained as
historical configuration evidence, not patches to apply before configure.

## Emulator

```sh
python3 tools/build.py --sdk /path/buildroot/output --out /tmp/pcsx-build \
  --library-root /tmp/pcsx-deps/sysroot
python3 tools/build_tests.py --sdk /path/buildroot/output --build /tmp/pcsx-build
```

The complete source includes support/Input, Keymap, Log and the narrow helper
header used by the frontend. No unrelated private OS source is needed to link.
The rkgame-named bridge is a new public API integration, not a vendor object.
The original import revision is unknown; PROVENANCE.json explicitly distinguishes
the pinned public comparison baseline from a claimed historical import.

Builds are serial, nice 10, bound to one available CPU, with 768 MiB compiler
address-space limits. Preserve `-fno-delete-null-pointer-checks` and the MIPS
dynarec. The executable MUST link at `0x40000000` using
`-no-pie -Wl,-Ttext-segment=0x40000000`: PSX RAM intentionally maps at address
zero. A normal low-address executable will break this layout.

## Tests

`tools/make_test_disc.py /tmp/pcsx-build/test.iso` generates an original
ISO9660 PSX test program with GPU output, changing RAM and a looping ADPCM tone.
It contains no Sony BIOS or commercial game assets.

The compiled tests require real Linux/MIPS with mmap at zero permitted; the
emulator test kernel is a one-CPU Malta VM with 120 MiB RAM. Execute
`pcsx-recovery-engine DISC STATE_DIRECTORY normal` there. Further scenarios:
`sync-enosys`, `all-sync-enosys`, `io-error`, `rename-error`, `enospc`,
`gpu-oom`, `screenshot-oom`. Kernel seccomp injects failures, not fake serializers.
`pcsx-recovery-menu DISC surface` and `renderer` exercise the production menu.
`pcsx-readonly-test` additionally requires tmpfs mount/remount permission.
Use SDL dummy audio in the VM and DirectFB dummy video for the menu. The tests
assert nonzero actual SPU samples but do not establish physical audio quality.

## Packaging

```sh
python3 tools/package.py --build /tmp/pcsx-build \
  --libraries /tmp/pcsx-deps/sysroot/usr/lib --out /tmp/pcsx-release
```

The output contains the .lilpck, corresponding-source.zip and SHA256SUMS.txt.
The source archive excludes generated binaries and Git metadata. One launcher
and meta.json are directly at package root. No assets, ROMs, BIOS or keys are
distributed. Existing OS runtime adapters remain separate platform dependencies.
Review BUILD-EVIDENCE.json and run tools/release_gate.py before publication.
