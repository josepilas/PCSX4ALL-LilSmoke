# PCSX4ALL-LilSmoke 0.0.1

First public source release and LilSmoke Application.

Native MIPS dynarec, Unai software graphics, SPU audio, a standalone game browser,
Start+X menu and Start+Select exit. Ten save-state slots use transactional writes,
damaged-state recovery and old-kernel sync fallbacks. The executable and all five
bundled libraries were rebuilt from the supplied public sources.

Installer identity: `org.lilsmoke.pcsx4all`. Open Core provider: `psx`.
Architecture: `mipsel-linux-musl`. No BIOS or games included. Original icon
omitted. Existing compatible LilSmoke OS/device adapters and font required.

Licensing is mixed: GPL larger work, preserved upstream MIT/GPL/LGPL/per-file
notices, library licenses, and MPL-2.0 only for eligible original files. It is
not an MPL-only relicense of PCSX4ALL.

Includes the narrow Input/Keymap/Log support closure and an independently
rewritten PCSX platform bridge. Linux/MIPS tests exercise actual emulation,
nonzero SPU PCM, save/load of CPU/RAM, both production menu render paths and
storage failures with one CPU and 120 MiB RAM. These do not establish physical
M8 speed or sound quality for this exact new build.

Downloads:
- PCSX4ALL-LilSmoke-0.0.1.lilpck: install through LilSmoke Explorer.
- corresponding-source.zip: emulator/support/dependency source, patches and build tools.
- SHA256SUMS.txt: file verification.

Public 0.0.1 is numerically older than internal 1.0.x. Use the installer's
different-version update, not uninstall, and back up saves first.
The application requires a compatible LilSmokeOS; no desktop executable,
BIOS, commercial games, firmware or OS image is included.
