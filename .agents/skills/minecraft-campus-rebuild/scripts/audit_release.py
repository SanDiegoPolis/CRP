#!/usr/bin/env python3
"""Read-only file audit. Does NOT validate voxel geometry or execute a game."""
import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_relative(value):
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError('Expected a nonempty relative POSIX path')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or ':' in value or str(p) == '.':
        raise ValueError('Absolute, parent-traversal or invalid path')
    return str(p)


def audit(release, world=None, archives=()):
    root = Path(release).resolve()
    result = {'scope': 'Read-only file identity and archive integrity; no voxel or game validation',
              'release': str(root), 'errors': [], 'gaps': [], 'verified_components': 0,
              'component_groups': {}, 'recorded_reports_not_revalidated': {}, 'archives': []}
    errors, gaps = result['errors'], result['gaps']
    try:
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8-sig'))
        rows = manifest['files']
        if not isinstance(rows, list) or not rows:
            raise ValueError('manifest.files must be a nonempty list')
        result['manifest_sha256'] = digest(root / 'manifest.json')
        result['declared_release'] = manifest.get('release')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f'Manifest unavailable/invalid: {exc}')
        rows = []
    seen, groups = set(), Counter()
    for index, row in enumerate(rows):
        try:
            if not isinstance(row, dict):
                raise ValueError('Entry must be an object')
            rel = safe_relative(row.get('file'))
            if rel in seen:
                raise ValueError(f'Duplicate component path: {rel}')
            seen.add(rel)
            target = (root / rel).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f'Component resolves outside release: {rel}')
            expected = row.get('sha256')
            if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-fA-F]{64}', expected):
                raise ValueError(f'Missing/invalid SHA-256: {rel}')
            if digest(target) != expected.lower():
                raise ValueError(f'SHA-256 mismatch: {rel}')
            result['verified_components'] += 1
            groups[PurePosixPath(rel).parts[0] if '/' in rel else 'root'] += 1
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'Component {index}: {exc}')
    result['component_groups'] = dict(groups)
    unlisted = sorted(p.relative_to(root).as_posix() for p in root.rglob('*.schem')
                      if p.relative_to(root).as_posix() not in seen)
    if unlisted:
        gaps.append({'unlisted_schem_files_not_audited': unlisted})
    for record in manifest.get('validation_reports', []) if rows else []:
        try:
            name = safe_relative(record['file'])
            p = (root / name).resolve()
            if not p.is_relative_to(root) or digest(p) != record['sha256']:
                raise ValueError('Report identity mismatch or escaping path')
            data = json.loads(p.read_text(encoding='utf-8-sig'))
            result['recorded_reports_not_revalidated'][name] = {
                'sha256': digest(p), 'kind': record.get('kind'), 'declared_status': data.get('status')}
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            errors.append(f'Invalid declared report: {exc}')
    if not result['recorded_reports_not_revalidated']:
        gaps.append('No hash-bound validation_reports declared; inspect project reports separately')
    if world:
        w = Path(world).resolve()
        folders = [w / 'region', w / 'DIM-1/region', w / 'DIM1/region']
        if (w / 'dimensions').is_dir():
            folders.extend(p for p in (w / 'dimensions').rglob('region') if p.is_dir())
        dimension_counts = {}
        for folder in folders:
            if not folder.resolve().is_relative_to(w):
                errors.append(f'Region directory resolves outside world: {folder}')
                continue
            regions = [p for p in folder.glob('*.mca') if p.is_file()]
            if regions:
                dimension_counts[folder.relative_to(w).as_posix()] = len(regions)
        result['world_files'] = {'path': str(w), 'format_checked': 'Java Anvil directory layout only',
                                 'region_files': sum(dimension_counts.values()),
                                 'dimension_region_files': dimension_counts,
                                 'nbt_or_runtime_validated': False}
        if not (w / 'level.dat').is_file():
            errors.append('World must contain level.dat')
        if not dimension_counts:
            errors.append('No Java Anvil region files found in legacy or namespaced dimension directories')
            if (w / 'db').is_dir():
                gaps.append('Possible Bedrock world: this auditor only checks Java Anvil layouts')
        if 'region' in dimension_counts and 'dimensions/minecraft/overworld/region' in dimension_counts:
            gaps.append('Both legacy and namespaced Overworld files exist; establish the active version before delivery')
        p = w / 'world-validation.json'
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding='utf-8-sig'))
                result['recorded_reports_not_revalidated']['world-validation.json'] = {
                    'sha256': digest(p),
                    'declared_section_readback': data.get('section_readback'),
                    'declared_latest_in_game': data.get('latest_in_game')}
            except (OSError, ValueError, AttributeError) as exc:
                errors.append(f'Invalid world report: {exc}')
        else:
            gaps.append('World readback report absent; no game or chunk validation inferred')
    for archive in archives:
        try:
            path = Path(archive)
            with zipfile.ZipFile(path) as z:
                members = [safe_relative(i.filename.rstrip('/')) for i in z.infolist()]
                if len(set(members)) != len(members):
                    raise ValueError('Duplicate ZIP members')
                bad = z.testzip()
                if bad:
                    raise ValueError(f'Bad CRC: {bad}')
                result['archives'].append({'file': str(path.resolve()), 'sha256': digest(path),
                                           'entries': len(members), 'integrity': 'PASS',
                                           'matches_release_contents': 'NOT_CHECKED'})
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as exc:
            errors.append(f'Archive {archive}: {exc}')
    result['status'] = 'FAIL' if errors else ('FILE_CHECKS_PASS_WITH_GAPS' if gaps else 'FILE_CHECKS_PASS')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('release', type=Path)
    parser.add_argument('--world', type=Path)
    parser.add_argument('--zip', action='append', default=[], dest='archives', type=Path)
    args = parser.parse_args()
    result = audit(args.release, args.world, args.archives)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
