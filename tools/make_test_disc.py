# SPDX-License-Identifier: MPL-2.0
"""Generate an original GPU/SPU/RAM test program in a minimal ISO9660 disc.

No Sony BIOS, game data or downloaded binary is used. Generated media is test
output only, not part of the release source/runtime archives.
"""
import argparse
from pathlib import Path
import struct


def make_disc(destination):
    code = []
    def imm(op, target, source, value):
        code.append((op << 26) | (source << 21) | (target << 16) | (value & 0xffff))
    def constant(register, value):
        imm(15, register, 0, value >> 16)
        imm(13, register, register, value)
    def write(address, value, half=False):
        constant(9, value)
        imm(41 if half else 43, 9, 8, address)
    constant(8, 0x1f800000)
    write(0x1814, 0)
    write(0x1814, 0x08000001)
    write(0x1814, 0x03000000)
    write(0x1810, 0xe3000000)
    write(0x1810, 0xe4000000 | (239 << 10) | 319)
    # Own looping ADPCM waveform in SPU RAM: eight halfwords, no asset data.
    write(0x1daa, 0xc010, True)
    write(0x1da6, 0x0200, True)
    for sample in (0x0304, 0x7531, 0xfdb9, 0x7531, 0xfdb9, 0x7531, 0xfdb9, 0x7531):
        write(0x1da8, sample, True)
    for address, value in ((0x1c00, 0x3fff), (0x1c02, 0x3fff), (0x1c04, 0x1000),
                           (0x1c06, 0x0200), (0x1c08, 0x00ff), (0x1c0a, 0x1fc0),
                           (0x1c0e, 0x0200), (0x1d80, 0x3fff), (0x1d82, 0x3fff),
                           (0x1daa, 0xc000), (0x1d88, 1)):
        write(address, value, True)
    constant(12, 0x80020000)
    constant(10, 0x0200d060)
    constant(11, (240 << 16) | 320)
    loop = len(code)
    imm(9, 13, 13, 1)
    imm(43, 13, 12, 0)
    imm(43, 10, 8, 0x1810)
    imm(43, 0, 8, 0x1810)
    imm(43, 11, 8, 0x1810)
    imm(9, 15, 0, 12000)
    imm(9, 15, 15, -1)
    imm(5, 0, 15, -2)
    code.append(0)
    code.append((2 << 26) | (((0x80010000 + loop * 4) >> 2) & 0x03ffffff))
    code.append(0)
    executable = bytearray(4096)
    executable[:8] = b'PS-X EXE'
    struct.pack_into('<IIII', executable, 0x10, 0x80010000, 0, 0x80010000, 2048)
    struct.pack_into('<I', executable, 0x30, 0x801fff00)
    executable[2048:2048 + len(code) * 4] = struct.pack('<' + 'I' * len(code), *code)
    def both32(value): return struct.pack('<I', value) + struct.pack('>I', value)
    def record(name, sector, size, directory=False):
        data = bytearray(33 + len(name) + (len(name) % 2 == 0))
        data[0] = len(data)
        data[2:10] = both32(sector); data[10:18] = both32(size)
        data[25] = 2 if directory else 0
        data[28:32] = b'\x01\x00\x00\x01'
        data[32] = len(name); data[33:33 + len(name)] = name
        return data
    disc = bytearray(64 * 2048)
    descriptor = bytearray(2048)
    descriptor[:7] = b'\x01CD001\x01'
    descriptor[8:40] = b'PCSX4ALL LILSMOKE'.ljust(32)
    descriptor[40:72] = b'LILSMOKE ORIGINAL TEST'.ljust(32)
    descriptor[80:88] = both32(64)
    descriptor[128:132] = b'\x00\x08\x08\x00'
    root = record(b'\0', 20, 4096, True)
    descriptor[156:156 + len(root)] = root
    disc[16 * 2048:17 * 2048] = descriptor
    disc[17 * 2048:17 * 2048 + 7] = b'\xffCD001\x01'
    boot = b'BOOT = cdrom:\\SLUS_999.99;1\r\nTCB = 4\r\nEVENT = 10\r\nSTACK = 801fff00\r\n'
    entries = [root, record(b'\x01', 20, 4096, True), record(b'SYSTEM.CNF;1', 22, len(boot)),
               record(b'SLUS_999.99;1', 23, len(executable))]
    offset = 20 * 2048
    for entry in entries:
        disc[offset:offset + len(entry)] = entry; offset += len(entry)
    disc[22 * 2048:22 * 2048 + len(boot)] = boot
    disc[23 * 2048:25 * 2048] = executable
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as f: f.write(disc)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    make_disc(parser.parse_args().output)
