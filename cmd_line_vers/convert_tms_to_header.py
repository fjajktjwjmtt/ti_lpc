#!/usr/bin/env python3
"""
convert_tms_to_header.py - Convert TMS5xxx chip definition .txt files into tms5k.h

#-----v1.00 27-mar-2026 	#initial version

Reads tms5100.txt, tms5110.txt, tms5200.txt, and tms5220.txt and generates
(or regenerates) the C++ struct initializers used in tms5k.h.

Copyright (C) 2019-2026 BrerDawg, et. al.
License: GPL v2 or later

Usage:
    python3 convert_tms_to_header.py [--output tms5k.h] [--dir .]
"""

import argparse
import os
import re
import sys


MAX_CHIRP_SIZE = 52
MAX_ENERGY_SIZE = 16
MAX_PITCH_SIZE = 64
MAX_K_SIZE = 32


def parse_decimal_list(s):
    """Parse a comma-separated list of decimal integers."""
    vals = []
    for tok in s.split(','):
        tok = tok.strip()
        if tok == '' or tok == '\n':
            continue
        vals.append(int(tok))
    return vals


def parse_hex_list(s):
    """Parse a comma-separated list of hex integers (0x prefixed)."""
    vals = []
    for tok in s.split(','):
        tok = tok.strip()
        if tok == '' or tok == '\n':
            continue
        vals.append(int(tok, 16))
    return vals


def extract_param(content, key):
    """Extract the value string after 'key=' up to the next newline."""
    pattern = re.escape(key) + r'=(.*?)(?:\n|$)'
    m = re.search(pattern, content)
    if m:
        return m.group(1).strip()
    return None


def parse_chip_file(filepath):
    """Parse a TMS chip definition text file and return a dict of params."""
    with open(filepath, 'r') as f:
        content = f.read()

    chip = {}

    # Processor name
    proc = extract_param(content, 'processor')
    if proc:
        chip['name'] = proc.strip()
    else:
        # Derive from filename
        base = os.path.basename(filepath).replace('.txt', '')
        chip['name'] = base

    # Chirp (decimal or hex)
    chirp_dec = extract_param(content, 'chirp')
    chirp_hx = extract_param(content, 'chirp_hx')
    if chirp_hx:
        chip['chirp'] = parse_hex_list(chirp_hx)
        chip['chirp_is_hex'] = True
    elif chirp_dec:
        chip['chirp'] = parse_decimal_list(chirp_dec)
        chip['chirp_is_hex'] = False
    else:
        chip['chirp'] = []
        chip['chirp_is_hex'] = False

    # Energy
    energy_str = extract_param(content, 'energy')
    if energy_str:
        chip['energy'] = parse_decimal_list(energy_str)
    else:
        chip['energy'] = []

    # Pitch count
    pc_str = extract_param(content, 'pitch_count')
    chip['pitch_count'] = int(pc_str) if pc_str else 32

    # Pitch
    pitch_str = extract_param(content, 'pitch')
    if pitch_str:
        chip['pitch'] = parse_decimal_list(pitch_str)
    else:
        chip['pitch'] = []

    # K coefficients (k0 through k9)
    for i in range(10):
        key = f'k{i}'
        val_str = extract_param(content, key)
        if val_str:
            chip[key] = parse_decimal_list(val_str)
        else:
            chip[key] = []

    return chip


def pad_array(vals, max_size, fill=0):
    """Pad an array to max_size with fill value."""
    result = list(vals[:max_size])
    while len(result) < max_size:
        result.append(fill)
    return result


def format_int_array(vals, per_line=16, hex_fmt=False):
    """Format an integer array as a C initializer string."""
    if hex_fmt:
        items = [f'0x{v:02x}' for v in vals]
    else:
        items = [str(v) for v in vals]
    return ', '.join(items)


def generate_chip_struct(chip, chip_enum):
    """Generate a C++ ChipParams struct initializer."""
    name = chip['name']

    chirp_padded = pad_array(chip['chirp'], MAX_CHIRP_SIZE)
    energy_padded = pad_array(chip['energy'], MAX_ENERGY_SIZE)
    pitch_padded = pad_array(chip['pitch'], MAX_PITCH_SIZE)

    is_hex_chirp = chip.get('chirp_is_hex', False)

    k_arrays = []
    k_sizes_map = {0: 32, 1: 32, 2: 16, 3: 16, 4: 16, 5: 16, 6: 16, 7: 8, 8: 8, 9: 8}
    for i in range(10):
        k_vals = chip.get(f'k{i}', [])
        k_padded = pad_array(k_vals, MAX_K_SIZE)
        k_arrays.append((k_padded, len(chip.get(f'k{i}', []))))

    lines = []
    var_name = name.upper() + '_PARAMS'
    lines.append(f'// {name.upper()} chip parameters')
    lines.append(f'static const ChipParams {var_name} = {{')
    lines.append(f'    {chip_enum},')
    lines.append(f'    "{name}",')

    # chirp
    lines.append('    // chirp')
    chirp_str = format_int_array(chirp_padded, hex_fmt=is_hex_chirp)
    lines.append(f'    {{{chirp_str}}},')
    lines.append(f'    {len(chip["chirp"])},')

    # energy
    lines.append('    // energy')
    energy_str = format_int_array(energy_padded)
    lines.append(f'    {{{energy_str}}},')
    lines.append(f'    {len(chip["energy"])},')

    # pitch
    lines.append('    // pitch')
    pitch_str = format_int_array(pitch_padded)
    lines.append(f'    {{{pitch_str}}},')
    lines.append(f'    {chip["pitch_count"]},')

    # k0 - k9
    for i in range(10):
        k_padded, k_actual_size = k_arrays[i]
        lines.append(f'    // k{i}')
        k_str = format_int_array(k_padded)
        lines.append(f'    {{{k_str}}},')
        if i < 9:
            lines.append(f'    {k_actual_size},')
        else:
            lines.append(f'    {k_actual_size}')

    lines.append('};')
    return '\n'.join(lines)


def generate_header(chips_data):
    """Generate the full tms5k.h header file content."""

    chip_names = ['tms5100', 'tms5110', 'tms5200', 'tms5220']
    chip_enums = ['CHIP_TMS5100', 'CHIP_TMS5110', 'CHIP_TMS5200', 'CHIP_TMS5220']

    header = []
    header.append('/*')
    header.append(' * tms5k.h - TMS5xxx Speech Synthesizer Chip Definitions')
    header.append(' *')
    header.append(' * This header provides compile-time chip parameter definitions for')
    header.append(' * TMS5100, TMS5110, TMS5200, and TMS5220 speech synthesizer chips.')
    header.append(' *')
    header.append(' * Based on chip definition files from the ti_lpc project.')
    header.append(' * Reference: https://github.com/mamedev/mame/blob/master/src/devices/sound/tms5110r.hxx')
    header.append(' *')
    header.append(' * Copyright (C) 2019-2026 BrerDawg, et. al.')
    header.append(' * License: GPL v2 or later')
    header.append(' */')
    header.append('')
    header.append('#ifndef TMS5K_H')
    header.append('#define TMS5K_H')
    header.append('')
    header.append('#include <cstdint>')
    header.append('#include <cstring>')
    header.append('')
    header.append('namespace tms5k {')
    header.append('')
    header.append('// Chip type enumeration')
    header.append('enum ChipType {')
    header.append('    CHIP_TMS5100,')
    header.append('    CHIP_TMS5110,')
    header.append('    CHIP_TMS5200,')
    header.append('    CHIP_TMS5220,')
    header.append('    CHIP_UNKNOWN')
    header.append('};')
    header.append('')
    header.append('// Maximum array sizes')
    header.append(f'static const int MAX_CHIRP_SIZE = {MAX_CHIRP_SIZE};')
    header.append(f'static const int MAX_ENERGY_SIZE = {MAX_ENERGY_SIZE};')
    header.append(f'static const int MAX_PITCH_SIZE = {MAX_PITCH_SIZE};')
    header.append(f'static const int MAX_K_SIZE = {MAX_K_SIZE};')
    header.append('')
    header.append('// Chip parameter structure')
    header.append('struct ChipParams {')
    header.append('    ChipType type;')
    header.append('    const char* name;')
    header.append('    ')
    header.append('    // Chirp table')
    header.append('    uint8_t chirp[MAX_CHIRP_SIZE];')
    header.append('    int chirp_size;')
    header.append('    ')
    header.append('    // Energy table')
    header.append('    int16_t energy[MAX_ENERGY_SIZE];')
    header.append('    int energy_size;')
    header.append('    ')
    header.append('    // Pitch table')
    header.append('    int16_t pitch[MAX_PITCH_SIZE];')
    header.append('    int pitch_count;')
    header.append('    ')
    header.append('    // K coefficient tables')
    for i in range(10):
        header.append(f'    int16_t k{i}[MAX_K_SIZE];')
        header.append(f'    int k{i}_size;')
    header.append('};')
    header.append('')

    # Generate each chip's params
    for i, name in enumerate(chip_names):
        if name in chips_data:
            header.append(generate_chip_struct(chips_data[name], chip_enums[i]))
            header.append('')

    # Utility functions
    header.append('// Get chip parameters by type')
    header.append('inline const ChipParams* getChipParams(ChipType type) {')
    header.append('    switch (type) {')
    header.append('        case CHIP_TMS5100: return &TMS5100_PARAMS;')
    header.append('        case CHIP_TMS5110: return &TMS5110_PARAMS;')
    header.append('        case CHIP_TMS5200: return &TMS5200_PARAMS;')
    header.append('        case CHIP_TMS5220: return &TMS5220_PARAMS;')
    header.append('        default: return nullptr;')
    header.append('    }')
    header.append('}')
    header.append('')
    header.append('// Get chip type from name string')
    header.append('inline ChipType getChipTypeFromName(const char* name) {')
    header.append('    if (!name) return CHIP_UNKNOWN;')
    header.append('    ')
    header.append('    // Check for various name formats')
    header.append('    if (strstr(name, "5100") != nullptr) return CHIP_TMS5100;')
    header.append('    if (strstr(name, "5110") != nullptr) return CHIP_TMS5110;')
    header.append('    if (strstr(name, "5200") != nullptr) return CHIP_TMS5200;')
    header.append('    if (strstr(name, "5220") != nullptr) return CHIP_TMS5220;')
    header.append('    ')
    header.append('    return CHIP_UNKNOWN;')
    header.append('}')
    header.append('')
    header.append('// Get chip parameters by name string')
    header.append('inline const ChipParams* getChipParamsByName(const char* name) {')
    header.append('    return getChipParams(getChipTypeFromName(name));')
    header.append('}')
    header.append('')
    header.append('} // namespace tms5k')
    header.append('')
    header.append('#endif // TMS5K_H')
    header.append('')

    return '\n'.join(header)


def main():
    parser = argparse.ArgumentParser(
        description='Convert TMS5xxx chip definition .txt files into tms5k.h C++ header')
    parser.add_argument('--dir', default='.', help='Directory containing tms5xxx.txt files (default: .)')
    parser.add_argument('--output', default='tms5k.h', help='Output header file (default: tms5k.h)')
    parser.add_argument('--dry-run', action='store_true', help='Print output to stdout instead of writing file')
    args = parser.parse_args()

    chip_files = {
        'tms5100': os.path.join(args.dir, 'tms5100.txt'),
        'tms5110': os.path.join(args.dir, 'tms5110.txt'),
        'tms5200': os.path.join(args.dir, 'tms5200.txt'),
        'tms5220': os.path.join(args.dir, 'tms5220.txt'),
    }

    chips_data = {}
    for name, filepath in chip_files.items():
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping {name}", file=sys.stderr)
            continue
        print(f"Parsing {filepath}...", file=sys.stderr)
        chips_data[name] = parse_chip_file(filepath)

    if not chips_data:
        print("ERROR: No chip definition files found.", file=sys.stderr)
        sys.exit(1)

    header_content = generate_header(chips_data)

    if args.dry_run:
        print(header_content)
    else:
        output_path = os.path.join(args.dir, args.output) if not os.path.isabs(args.output) else args.output
        with open(output_path, 'w') as f:
            f.write(header_content)
        print(f"Generated {output_path} with {len(chips_data)} chip definitions.", file=sys.stderr)


if __name__ == '__main__':
    main()
