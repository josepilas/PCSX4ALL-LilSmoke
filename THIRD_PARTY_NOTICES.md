# Third-Party Notices

| Component | Provenance And Retained Terms |
| --- | --- |
| PCSX4ALL | dmitrysmagin/pcsx4all, comparison `c7faf12b893eba94faced88baa5e7dd059be58b7`; GPL-2.0-or-later file headers; GPLv3 top-level text |
| PCSX core | PCSX, PCSX-df and PCSX-Reloaded teams including Ryan Schultz; per-file GPL-2.0-or-later |
| GPU Unai | PCSX4ALL team, Unai, Daniel Silsby/Senquack; GPL-2.0-or-later |
| MIPS recompiler | Ulrich Hecht, Dmitry Smagin, Daniel Silsby; retained MIT permission notices |
| gpulib | Grazvydas "notaz" Ignotas; GPL-2.0-or-later OR LGPL-2.1-or-later as stated in files |
| SPU | Pete Bernert, P.E.Op.S., PCSX-ReARMed contributors, notaz and Senquack; GPL-2.0-or-later; upstream import log retained in README.TXT |
| HLE Japanese font | Shinonome/k14goth, Yasuyuki Furukawa, H. Kagotani, TAKADA Toshihiro, /efont/, Wei Mingzhi; public-domain attribution in src/sjisfont.h retained |
| SDL2 2.28.5 | Sam Lantinga and contributors; zlib; local changes under patches/sdl2, not MPL-relabeled |
| SDL2_ttf 2.22.0 | Sam Lantinga and contributors; zlib; HarfBuzz disabled in recorded configure |
| FreeType 2.13.2 | FreeType authors; FTL or GPLv2; retain both texts and all module notices; this GPLv3 work selects FTL |
| libpng 1.6.43 | libpng authors; libpng-2.0; complete LICENSE and source retained |
| zlib 1.3.1 | Jean-loup Gailly, Mark Adler; zlib; exact version's notice retained |

The runtime's license directory includes original library notices as supplied
by the reference package, augmented with GPLv2, GPLv3, LGPLv2.1 and MPL2 texts.
The source archives retain their own embedded licenses, including subcomponents.
FreeType acknowledgment: portions of this software are copyright The FreeType
Project (https://freetype.org/). All rights reserved.

The new executable includes the publicly exported Input/Keymap/Log support and
the narrow EmulatorHelper header. Their source and retained licenses are under
support/. It does not link the historical private support revision.

DirectFB, ALSA, musl, libstdc++, libgcc_s, the DejaVu font, the ROM resolver,
libod-sdl and M8 display/audio/loading adapters are separately supplied by the
installed OS. No stock vendor firmware, SDK sysroot, OS image, or backend library
is bundled into this export. Their availability and applicable obligations must
be considered when distributing the OS itself.

The historical internal integration used recovered vendor glue. That bridge
has been replaced for this public executable by a new source implementation
using the PCSX GPL port interfaces. No historical vendor implementation or object
is included. The original core import commit is unknown; the explicit public
comparison pin is not presented as proof of the historical import.

Primary references:
- https://github.com/dmitrysmagin/pcsx4all/tree/c7faf12b893eba94faced88baa5e7dd059be58b7
- https://raw.githubusercontent.com/dmitrysmagin/pcsx4all/c7faf12b893eba94faced88baa5e7dd059be58b7/gpl.txt
- https://raw.githubusercontent.com/libsdl-org/SDL/release-2.28.5/LICENSE.txt
- https://raw.githubusercontent.com/libsdl-org/SDL_ttf/release-2.22.0/LICENSE.txt
- https://freetype.org/license.html
- https://github.com/pnggroup/libpng/blob/v1.6.43/LICENSE
- https://github.com/madler/zlib/blob/v1.3.1/LICENSE
- https://www.mozilla.org/en-US/MPL/2.0/FAQ/
- https://www.gnu.org/licenses/gpl-faq.html#GPLRequireSourcePostedPublic

This is a technical release inventory, not legal advice.
