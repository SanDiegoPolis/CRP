#!/usr/bin/env python3
"""Portable block-only component composition, sparse patches and .schem export."""
import argparse
import json
import math
import shutil
import tempfile
from pathlib import Path
import numpy as np
from audit_release import digest, safe_relative
from schematic_io import AIR, canonical, read_schematic, write_schematic, verify_schematic


def relative_file(root, name):
    p = (root / safe_relative(name)).resolve()
    if not p.is_relative_to(root.resolve()):
        raise ValueError('Path escapes its containing directory')
    return p


def triplet(value, label, positive=False):
    if not isinstance(value, (list, tuple)) or len(value) != 3 or any(type(x) is not int for x in value):
        raise ValueError(f'{label}: expected three integers')
    if positive and min(value) <= 0:
        raise ValueError(f'{label}: sizes must be positive')
    return np.array(value, np.int64)


def read_manifest(release):
    root = Path(release).resolve()
    manifest = root / 'manifest.json'
    stamp = digest(manifest)
    data = json.loads(manifest.read_text(encoding='utf-8-sig'))
    if not isinstance(data.get('files'), list) or not data['files']:
        raise ValueError('Manifest needs a nonempty files list')
    seen, lo, hi = set(), [], []
    for r in data['files']:
        file = relative_file(root, r['file'])
        if file in seen:
            raise ValueError(f'Duplicate manifest component: {r["file"]}')
        seen.add(file)
        if digest(file) != r['sha256'].lower():
            raise ValueError(f'Component hash mismatch: {r["file"]}')
        off = triplet(r['offset_xyz'], 'offset_xyz')
        size = triplet(r['size_xyz'], 'size_xyz', positive=True)
        lo.append(off); hi.append(off + size)
    return root, data, stamp, np.min(lo, axis=0), np.max(hi, axis=0)


def read_patch(descriptor, baseline_sha, coordinate_version):
    file = Path(descriptor).resolve()
    d = json.loads(file.read_text(encoding='utf-8-sig'))
    if d['baseline_manifest_sha256'] != baseline_sha or d['coordinate_version'] != coordinate_version:
        raise ValueError(f'Patch baseline/coordinate mismatch: {file}')
    path = relative_file(file.parent, d['npz'])
    if digest(path) != d['sha256']:
        raise ValueError(f'Patch hash mismatch: {file}')
    with np.load(path, allow_pickle=False) as p:
        xyz, before, after, palette = [p[k].copy() for k in ('xyz', 'before', 'after', 'palette')]
    if xyz.ndim != 2 or xyz.shape[1] != 3 or xyz.dtype.kind not in 'iu':
        raise ValueError('Patch xyz must be an integer N x 3 array')
    if not len(xyz) or len(np.unique(xyz, axis=0)) != len(xyz):
        raise ValueError('Empty patch or duplicate coordinates within patch')
    if palette.ndim != 1 or palette.dtype.kind not in 'US' or not len(palette):
        raise ValueError('Patch palette must be a nonempty string array')
    for values in (before, after):
        if values.shape != (len(xyz),) or values.dtype.kind not in 'iu' or values.min() < 0 or values.max() >= len(palette):
            raise ValueError('Invalid patch before/after indices')
    return {'path': str(file), 'descriptor_sha256': digest(file), 'npz_path': str(path),
            'sha256': digest(path), 'xyz': xyz.astype(np.int64), 'before': before,
            'after': after, 'palette': [canonical(s) for s in palette]}


def estimate(release, patches=(), coordinate_version=None):
    root, manifest, stamp, lo, hi = read_manifest(release)
    loaded = [read_patch(p, stamp, coordinate_version) for p in patches]
    for p in loaded:
        lo = np.minimum(lo, p['xyz'].min(axis=0)); hi = np.maximum(hi, p['xyz'].max(axis=0) + 1)
    size = hi - lo
    voxels = math.prod(map(int, size))
    return {'release': str(root), 'manifest_sha256': stamp, 'components': len(manifest['files']),
            'bounds_xyz_half_open': [*map(int, lo), *map(int, hi)], 'size_xyz': size.tolist(),
            'volume_including_air': voxels, 'mmap_bytes': voxels * 2,
            'uncompressed_blockdata_bytes_range': [voxels, voxels * 3],
            'limits': 'Block-only Sponge v2, <=65536 palette states; no entities or biome data',
            'not_a_runtime_performance_estimate': True}


def build(release, output, coordinate_version, patches=(), anchor=(0, 0, 0), max_voxels=500_000_000):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f'Refusing to replace output: {output}')
    root, manifest, stamp, lo, hi = read_manifest(release)
    if not isinstance(coordinate_version, str) or not coordinate_version.strip():
        raise ValueError('An explicit nonempty coordinate_version is required')
    if manifest.get('coordinate_version') != coordinate_version:
        raise ValueError('Manifest coordinate_version disagrees with requested version')
    loaded = [read_patch(p, stamp, coordinate_version) for p in patches]
    for p in loaded:
        lo = np.minimum(lo, p['xyz'].min(axis=0)); hi = np.maximum(hi, p['xyz'].max(axis=0) + 1)
    size = hi - lo
    volume = math.prod(map(int, size))
    if volume > max_voxels or max(size) > 65535:
        raise ValueError(f'Export volume {volume} exceeds configured or format limit; inspect then split or raise budget')
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < volume * 5 + 64 * 1024 * 1024:
        raise ValueError('Insufficient disk budget for mmap, export and verification')
    temp = Path(tempfile.mkdtemp(prefix='.campus-build-', dir=output.parent))
    blocks = None
    try:
        blocks = np.lib.format.open_memmap(temp/'blocks.npy', mode='w+', dtype=np.uint16,
                                           shape=tuple(size[[1, 2, 0]]))
        palette, lookup = [AIR], {AIR: 0}
        def register(states):
            mapping = []
            for s in states:
                if s is None:
                    mapping.append(0); continue
                s = canonical(s)
                if s not in lookup:
                    if len(palette) >= 65536:
                        raise ValueError('Palette exceeds toolkit limit')
                    lookup[s] = len(palette); palette.append(s)
                mapping.append(lookup[s])
            return np.array(mapping, np.uint16)
        data_version = None
        for r in manifest['files']:
            path = relative_file(root, r['file'])
            if digest(path) != r['sha256']:
                raise ValueError('Source changed during build')
            a, off, local_palette, dv = read_schematic(path)
            if off != r['offset_xyz'] or list(a.shape)[::1] != [r['size_xyz'][i] for i in (1, 2, 0)]:
                raise ValueError(f'Component geometry differs from manifest: {r["file"]}')
            if data_version is not None and data_version != dv:
                raise ValueError('Mixed Minecraft DataVersions; convert explicitly first')
            data_version = dv
            a = register(local_palette)[a]
            q = np.array(off) - lo; h, length, width = a.shape
            dest = blocks[q[1]:q[1]+h, q[2]:q[2]+length, q[0]:q[0]+width]
            occupied = a != 0
            if np.any(dest[occupied] != 0):
                raise ValueError(f'Overlapping component solids: {r["file"]}')
            if 'non_air_blocks' in r and int(np.count_nonzero(a)) != r['non_air_blocks']:
                raise ValueError(f'non_air_blocks differs: {r["file"]}')
            dest[occupied] = a[occupied]
        edits, duplicate_count = {}, 0
        for p in loaded:
            mapping = register(p['palette'])
            before, after = mapping[p['before']], mapping[p['after']]
            q = p['xyz'] - lo
            if not np.array_equal(blocks[q[:,1], q[:,2], q[:,0]], before):
                raise ValueError(f'Patch before differs from composed baseline: {p["path"]}')
            for xyz, b, a in zip(p['xyz'], before, after):
                key = tuple(map(int, xyz))
                if key in edits:
                    if edits[key] != (int(b), int(a)):
                        raise ValueError(f'Conflicting patches at {key}')
                    duplicate_count += 1
                else:
                    edits[key] = (int(b), int(a))
        for xyz, (_, after) in edits.items():
            x, y, z = np.array(xyz) - lo
            blocks[y,z,x] = after
        blocks.flush()
        if digest(root/'manifest.json') != stamp:
            raise ValueError('Baseline manifest changed during build')
        for r in manifest['files']:
            if digest(relative_file(root, r['file'])) != r['sha256']:
                raise ValueError('Source changed during build')
        for p in loaded:
            if digest(Path(p['path'])) != p['descriptor_sha256'] or digest(Path(p['npz_path'])) != p['sha256']:
                raise ValueError('Patch changed during build')
        offset = (lo - triplet(list(anchor), 'anchor')).tolist()
        file = temp/'campus-complete.schem'
        write_schematic(file, blocks, offset, palette, data_version)
        verification = verify_schematic(file, blocks, offset, palette, data_version)
        nonair = sum(int(np.count_nonzero(blocks[y])) for y in range(blocks.shape[0]))
        report = {'status': 'PASS', 'baseline_manifest_sha256': stamp,
                  'source_coordinate_version': coordinate_version, 'anchor_model_xyz': list(anchor),
                  'source_bounds_xyz_half_open': [*map(int, lo), *map(int, hi)],
                  'components': len(manifest['files']), 'overlap_count': 0,
                  'patches': [{k:p[k] for k in ('sha256','descriptor_sha256')} for p in loaded],
                  'unique_patch_positions': len(edits), 'duplicate_identical_patch_positions': duplicate_count,
                  'changed_positions': sum(b != a for b,a in edits.values()),
                  'output_sha256': digest(file), 'readback': verification,
                  'physical_routes_checked': False, 'game_engine_tested': False}
        new_coordinate = coordinate_version if not any(anchor) else coordinate_version + ':anchor=' + ','.join(map(str,anchor))
        new_manifest = {'schema_version':1,'release':output.name,'coordinate_version':new_coordinate,
                        'data_version': data_version, 'palette': palette,
                        'files':[{'file':file.name,'sha256':digest(file),'offset_xyz':offset,
                                  'size_xyz':size.tolist(),'non_air_blocks':nonair}],
                        'validation_reports':[{'file':'build-validation.json','sha256':None,'kind':'file-roundtrip'}]}
        (temp/'build-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        new_manifest['validation_reports'][0]['sha256'] = digest(temp/'build-validation.json')
        (temp/'manifest.json').write_text(json.dumps(new_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
        (temp/'placement.json').write_text(json.dumps({'format':'Sponge v2','data_version':data_version,
             'array_order':'Y,Z,X','schematic_offset_xyz':offset,'paste_anchor_model_xyz':list(anchor),
             'placement_rule':'Pasting at P places minimum block at P + Offset; verify client offset semantics in an empty test area',
             'example_paste_anchor_xyz':list(anchor),'expected_minimum_at_example':lo.tolist(),
             'air_deletions_included':True,'ignore_air_cannot_clear_existing_world_blocks':True},indent=2),encoding='utf-8')
        del dest, blocks
        blocks = None
        (temp/'blocks.npy').unlink()
        if output.exists():
            raise FileExistsError(output)
        temp.rename(output)
        return report
    except Exception:
        if blocks is not None:
            del blocks
        shutil.rmtree(temp, ignore_errors=True)
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['inspect','export'])
    parser.add_argument('release',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--coordinate-version')
    parser.add_argument('--patch',action='append',default=[],type=Path)
    parser.add_argument('--anchor',nargs=3,type=int,default=[0,0,0])
    parser.add_argument('--max-voxels',type=int,default=500_000_000)
    args=parser.parse_args()
    try:
        if args.command=='inspect':
            result=estimate(args.release,args.patch,args.coordinate_version)
        else:
            if not args.output or not args.coordinate_version:
                parser.error('export requires --output and --coordinate-version')
            result=build(args.release,args.output,args.coordinate_version,args.patch,args.anchor,args.max_voxels)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as exc:
        parser.exit(1,f'Build stopped: {exc}\n')


if __name__=='__main__':
    main()
