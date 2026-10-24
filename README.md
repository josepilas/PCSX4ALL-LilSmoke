<p align="center">
  <a href="https://ko-fi.com/josepilas" target="_blank" rel="noopener noreferrer">
    <img src="https://josepilas.github.io/kofi.webp" alt="Ko-fi" width="300" />
  </a>
</p>

# PCSX4ALL-LilSmoke

Native PlayStation emulator for LilSmokeOS, by Jose Pilas.

Download **PCSX4ALL-LilSmoke-0.0.1.lilpck** from
[Releases](https://github.com/josepilas/PCSX4ALL-LilSmoke/releases/tag/0.0.1).
This is a MIPS Linux application, not a Windows executable.

## Installation

1. Copy the package to LILROMS/packages.
2. Open it in LilSmoke Explorer and select INSTALL.
3. Open LilSmoke Applications to start the emulator's own game browser, or select
   PCSX4ALL-LilSmoke for PSX in Settings > Emulator Core Settings.
4. Put your legally obtained games in LILROMS/roms/psx. For multi-track games,
   retain the CUE and every referenced track together.

The stable application ID is `org.lilsmoke.pcsx4all`; its Open Core system is
`psx`. Public version 0.0.1 follows internal builds numbered 1.0.x. The installer
therefore calls this a different-version installation, not a newer version.
Do not uninstall the existing application to update it. Back up saves first.
The package does not contain game data, a Sony BIOS, firmware, or an OS image.
HLE BIOS is available; some games require a legally obtained compatible BIOS.

## Controls And Saves

Gamepad inputs use LilSmoke's evdev/input configuration.
Start+X opens the emulator menu; Start+Select exits to LilSmokeUI.
The menu includes resume, save/load, ten state slots, display and audio settings.
Persistent memory cards and save states are outside the installed application,
under the OS's configured persistent storage. Do not remove the card during use.
Use the system's safe Power Off before disconnecting power.

## Platform And Scope

The build targets little-endian MIPS32r2, o32 hard-float/FP32, musl, CPU software
rendering and SDL2/DirectFB. It retains the MIPS-to-MIPS dynarec, Unai GPU and
SPU audio backend. A compatible LilSmokeOS supplies device-specific display,
audio, input and archive-resolution services; this package does not replace them.
It is not a universal OpenDingux binary or an independently bootable image.

The public executable is rebuilt from this repository, not copied from the
previous internal package. Automated Linux/MIPS tests cover actual emulation,
nonzero SPU PCM, save/load RAM and CPU restoration, the production menu, and
storage failures. Those VM checks do not measure physical M8 speed or audio
quality. See `BUILD-EVIDENCE.json` and `BUILDING.md`.

## Source And Licenses

The complete emulator/support source, build scripts, dependency source archives,
patches and notices are included. Release downloads keep the small runtime
package and `corresponding-source.zip` separate. The package's SOURCE-OFFER.txt
links directly to that source asset.

**This is not an MPL-only emulator.** The combined program is GPL-3.0-or-later.
Upstream PCSX, Unai, gpulib, SPU and MIPS recompiler notices remain intact.
Eligible original LilSmoke files use MPL-2.0; dependencies keep their own licenses.
See `LICENSE`, `LICENSES/`, `SUPPORT-ORIGINS.json` and
`THIRD_PARTY_NOTICES.md`. Thanks to the PCSX/PCSX-df/PCSX-Reloaded/PCSX4ALL teams,
Unai, notaz, Senquack, Dmitry Smagin, Ulrich Hecht and all retained contributors.
