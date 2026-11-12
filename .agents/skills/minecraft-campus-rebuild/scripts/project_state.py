#!/usr/bin/env python3
"""Hash-bound project ledger. Recorded checks are declarations, not executed tests."""
import argparse
import json
import os
import tempfile
from pathlib import Path
from audit_release import digest


def snapshot(path):
    path = Path(path)
    if path.is_symlink():
        raise ValueError('Snapshot targets must not be symlinks')
    if path.is_file():
        return {'type': 'file', 'sha256': digest(path)}
    if not path.is_dir():
        raise ValueError(f'Missing artifact: {path}')
    files = {}
    for f in sorted(path.rglob('*')):
        if f.is_symlink():
            raise ValueError(f'Symlink in artifact: {f}')
        if f.is_file():
            files[f.relative_to(path).as_posix()] = digest(f)
    if not files:
        raise ValueError('Cannot snapshot an empty directory')
    return {'type': 'directory', 'files': files}


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        temporary = Path(f.name)
    temporary.replace(path)


def attach(statefile, name, path):
    statefile, path = Path(statefile).resolve(), Path(path).resolve()
    if path == statefile or (path.is_dir() and statefile.is_relative_to(path)):
        raise ValueError('Artifact cannot contain its own ledger')
    d = json.loads(statefile.read_text(encoding='utf-8-sig'))
    entry = {'path': os.path.relpath(path, statefile.parent), 'snapshot': snapshot(path)}
    # Keep prior validations: their bindings become stale instead of disappearing.
    d['artifacts'][name] = entry
    save(statefile, d)


def record(statefile, name, kind, status, artifacts, report):
    statefile, report = Path(statefile).resolve(), Path(report).resolve()
    if not artifacts or report == statefile:
        raise ValueError('A check needs artifact bindings and a separate report')
    d = json.loads(statefile.read_text(encoding='utf-8-sig'))
    bindings = {}
    for key in artifacts:
        entry = d['artifacts'][key]
        actual = snapshot(statefile.parent / entry['path'])
        if actual != entry['snapshot']:
            raise ValueError(f'Artifact has changed; attach current version first: {key}')
        bindings[key] = actual
    d['checks'][name] = {'kind': kind, 'declared_status': status, 'bindings': bindings,
                         'report': os.path.relpath(report, statefile.parent),
                         'report_sha256': digest(report)}
    save(statefile, d)


def status(statefile):
    statefile = Path(statefile).resolve()
    d = json.loads(statefile.read_text(encoding='utf-8-sig'))
    result = {'project': d['project'], 'coordinate_version': d['coordinate_version'],
              'scope': d['scope'], 'artifacts': {}, 'checks': {},
              'note': 'CURRENT means evidence matches files; it does not independently prove a declared PASS.'}
    current = {}
    for name, entry in d['artifacts'].items():
        try:
            current[name] = snapshot(statefile.parent / entry['path'])
            value = 'CURRENT' if current[name] == entry['snapshot'] else 'CHANGED'
        except (OSError, ValueError):
            value = 'MISSING_OR_UNREADABLE'
        result['artifacts'][name] = value
    for name, check in d['checks'].items():
        valid = all(current.get(k) == v for k, v in check['bindings'].items())
        try:
            valid = valid and digest(statefile.parent / check['report']) == check['report_sha256']
        except OSError:
            valid = False
        result['checks'][name] = {'kind': check['kind'], 'declared_status': check['declared_status'],
                                  'evidence': 'CURRENT' if valid else 'STALE'}
    kinds = {c['kind'] for c in result['checks'].values()
             if c['evidence'] == 'CURRENT' and c['declared_status'] == 'pass'}
    result['missing_current_pass_evidence'] = [k for k in ('files', 'geometry', 'routes', 'visual', 'game') if k not in kinds]
    result['next_actions'] = sorted(d.get('backlog', []), key=lambda x: (not x.get('blocking', False), -x.get('impact', 0)))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['init', 'attach', 'record', 'status'])
    p.add_argument('state', type=Path)
    p.add_argument('--project'); p.add_argument('--coordinate-version'); p.add_argument('--scope')
    p.add_argument('--name'); p.add_argument('--path', type=Path)
    p.add_argument('--kind', choices=['files', 'geometry', 'routes', 'visual', 'game'])
    p.add_argument('--status', choices=['pass', 'partial', 'fail', 'not-run'])
    p.add_argument('--artifact', action='append', default=[]); p.add_argument('--report', type=Path)
    a = p.parse_args()
    try:
        if a.command == 'init':
            if a.state.exists() or not all((a.project, a.coordinate_version, a.scope)):
                raise ValueError('init needs a new path, project, coordinate-version and scope')
            save(a.state, {'schema_version': 1, 'project': a.project, 'coordinate_version': a.coordinate_version,
                          'scope': a.scope, 'artifacts': {}, 'checks': {}, 'backlog': []})
        elif a.command == 'attach':
            if not a.name or not a.path: raise ValueError('attach needs name and path')
            attach(a.state, a.name, a.path)
        elif a.command == 'record':
            if not all((a.name, a.kind, a.status, a.report)): raise ValueError('record needs name, kind, status and report')
            record(a.state, a.name, a.kind, a.status, a.artifact, a.report)
        print(json.dumps(status(a.state), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as e:
        p.exit(1, f'State operation stopped: {e}\n')


if __name__ == '__main__':
    main()
