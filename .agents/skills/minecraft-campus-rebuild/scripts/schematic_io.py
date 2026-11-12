"""Block-only Sponge v2 I/O. NumPy + nbtlib; no project-specific imports."""
import gzip
import math
import struct
from pathlib import Path
import numpy as np
import nbtlib

AIR = 'minecraft:air'


def canonical(state):
    state = str(state)
    if '[' not in state:
        return state if ':' in state else 'minecraft:' + state
    name, props = state.split('[', 1)
    if not props.endswith(']'):
        raise ValueError(f'Invalid block state: {state}')
    props = props[:-1].split(',')
    if any('=' not in p for p in props) or len({p.split('=')[0] for p in props}) != len(props):
        raise ValueError(f'Invalid properties: {state}')
    return canonical(name) + '[' + ','.join(sorted(props)) + ']'


def decode_varints(raw, count):
    raw = np.asarray(raw, dtype=np.int8).view(np.uint8)
    if len(raw) == count and not np.any(raw & 128):
        return raw.astype(np.uint16)
    result = np.empty(count, np.uint16)
    value = shift = index = 0
    for byte in raw:
        value |= (int(byte) & 127) << shift
        if byte & 128:
            shift += 7
            if shift >= 35:
                raise ValueError('Invalid VarInt longer than five bytes')
        else:
            if index >= count or value >= 65536:
                raise ValueError('Too many blocks or palette index exceeds toolkit uint16 limit')
            result[index] = value
            index += 1
            value = shift = 0
    if shift or index != count:
        raise ValueError('Truncated block data')
    return result


def read_schematic(path):
    nbt = nbtlib.load(str(path))
    if int(nbt.get('Version', -1)) != 2:
        raise ValueError('Only block-only Sponge schematic Version 2 is supported')
    for key in ('Entities', 'BlockEntities', 'TileEntities', 'BiomeData', 'BiomePalette'):
        if len(nbt.get(key, [])):
            raise ValueError(f'{key} data would be lost; use a format-aware converter instead')
    size = [int(nbt[k]) & 65535 for k in ('Width', 'Height', 'Length')]
    if any(v == 0 for v in size):
        raise ValueError('Empty schematic dimension')
    pairs = [(canonical(k), int(v)) for k, v in nbt['Palette'].items()]
    indices = [v for _, v in pairs]
    if not pairs or len(set(indices)) != len(indices) or min(indices) < 0 or max(indices) >= 65536:
        raise ValueError('Invalid or oversized palette')
    palette = [None] * (max(indices) + 1)
    for state, index in pairs:
        palette[index] = state
    blocks = decode_varints(nbt['BlockData'], math.prod(size))
    if blocks.max() >= len(palette) or any(palette[int(i)] is None for i in np.unique(blocks)):
        raise ValueError('BlockData references undefined palette entry')
    blocks = blocks.reshape(size[1], size[2], size[0])
    offset = [int(v) for v in nbt.get('Offset', [0, 0, 0])]
    if len(offset) != 3:
        raise ValueError('Offset must have three coordinates')
    return blocks, offset, palette, int(nbt['DataVersion'])


def _text(value):
    b = value.encode('utf-8')
    if len(b) > 65535:
        raise ValueError('NBT string too long')
    return struct.pack('>H', len(b)) + b


def _tag(kind, name, payload):
    return bytes([kind]) + _text(name) + payload


def _chunks(blocks, size=1024 * 1024):
    flat = blocks.reshape(-1)
    for start in range(0, flat.size, size):
        yield np.asarray(flat[start:start + size])


def _encode(chunk):
    if chunk.max(initial=0) < 128:
        return chunk.astype(np.uint8).tobytes()
    out = bytearray()
    for value in chunk:
        value = int(value)
        while value >= 128:
            out.append((value & 127) | 128)
            value >>= 7
        out.append(value)
    return out


def write_schematic(path, blocks, offset, palette, data_version):
    """Stream compressed BlockData; refuses overwrites. Array order is Y,Z,X."""
    path = Path(path)
    if path.exists():
        raise FileExistsError(path)
    if blocks.ndim != 3 or blocks.dtype.kind not in 'ui' or not blocks.size:
        raise ValueError('Expected a nonempty integer YZX block array')
    h, length, width = blocks.shape
    if max(blocks.shape) > 65535 or len(palette) > 65536 or not palette:
        raise ValueError('Schematic dimensions or toolkit palette limit exceeded')
    palette = [canonical(s) for s in palette]
    if len(set(palette)) != len(palette):
        raise ValueError('Duplicate canonical palette states')
    byte_count = 0
    for chunk in _chunks(blocks):
        if chunk.min() < 0 or chunk.max() >= len(palette):
            raise ValueError('Invalid block palette index')
        byte_count += chunk.size + int(np.count_nonzero(chunk >= 128)) + int(np.count_nonzero(chunk >= 16384))
    if byte_count > 2147483647:
        raise ValueError('NBT ByteArray exceeds signed int length; split the export')
    if len(offset) != 3 or data_version <= 0:
        raise ValueError('Explicit Offset XYZ and positive DataVersion are required')
    header = bytes([10]) + _text('Schematic')
    header += _tag(3, 'Version', struct.pack('>i', 2))
    header += _tag(3, 'DataVersion', struct.pack('>i', data_version))
    for key, value in [('Width', width), ('Height', h), ('Length', length)]:
        header += _tag(2, key, struct.pack('>H', value))
    header += _tag(11, 'Offset', struct.pack('>iiii', 3, *map(int, offset)))
    header += _tag(3, 'PaletteMax', struct.pack('>i', len(palette)))
    header += _tag(10, 'Palette', b''.join(_tag(3, s, struct.pack('>i', i)) for i, s in enumerate(palette)) + b'\0')
    header += _tag(7, 'BlockData', struct.pack('>i', byte_count))
    path.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with path.open('xb') as stream:
            created = True
            with gzip.GzipFile(fileobj=stream, mode='wb', mtime=0) as compressed:
                compressed.write(header)
                for chunk in _chunks(blocks):
                    compressed.write(_encode(chunk))
                compressed.write(_tag(9, 'BlockEntities', b'\x0a\0\0\0\0'))
                compressed.write(_tag(9, 'Entities', b'\x0a\0\0\0\0') + b'\0')
    except Exception:
        # Only this newly created output, never an input or existing release.
        if created:
            path.unlink(missing_ok=True)
        raise


def verify_schematic(path, expected, offset, palette, data_version):
    """Parse output via nbtlib and compare all blocks with remapped palettes."""
    actual, actual_offset, actual_palette, dv = read_schematic(path)
    if actual.shape != expected.shape or actual_offset != list(offset) or dv != data_version:
        raise ValueError('Output metadata readback mismatch')
    lookup = {canonical(s): i for i, s in enumerate(palette)}
    mapping = np.array([lookup[s] if s is not None else 0 for s in actual_palette], np.uint16)
    af, ef = actual.reshape(-1), expected.reshape(-1)
    for start in range(0, actual.size, 1024 * 1024):
        if not np.array_equal(mapping[af[start:start + 1024 * 1024]], ef[start:start + 1024 * 1024]):
            raise ValueError(f'Output block readback mismatch near linear index {start}')
    return {'status': 'PASS', 'blocks_checked_including_air': int(actual.size),
            'method': 'nbtlib parse plus palette-aware comparison of every block',
            'game_engine_tested': False}
