"""Restore checked-in worlds/assets and run portable campus generators."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,urllib.request,zipfile,tempfile
ROOT=Path(__file__).resolve().parent
PROJECTS={'ccucm_minecraft':'build_campus.py','pitt_minecraft':'build_pitt.py','nwpu_minecraft':'build_nwpu.py','njtech_minecraft':'build_njtech.py','nwpu_rebuild':'build_rebuild.py'}
def checked_file(z,info,target,expected=None):
    resolved=target.resolve()
    if not resolved.is_relative_to(ROOT):raise ValueError('Archive path escapes repository')
    if info.is_dir():resolved.mkdir(parents=True,exist_ok=True);return
    data=z.read(info.filename)
    if expected and hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Asset checksum mismatch: '+info.filename)
    if resolved.exists():
        if resolved.read_bytes()!=data:raise FileExistsError('Existing different file preserved: '+str(resolved))
        return
    resolved.parent.mkdir(parents=True,exist_ok=True);resolved.write_bytes(data)
def restore(project):
    catalog=json.loads((ROOT/'assets/catalog.json').read_text(encoding='utf-8'))
    selected=[p for p in PROJECTS if project in ('all',p)]
    for row in catalog['assets']:
        p=ROOT/row['path']
        if not p.exists() and row.get('parts'):
            p.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=p.parent,prefix='.joining-',delete=False) as stream:
                temporary=Path(stream.name)
                try:
                    for part in row['parts']:
                        data=(ROOT/part['path']).read_bytes()
                        if hashlib.sha256(data).hexdigest()!=part['sha256']:raise ValueError('Part checksum mismatch: '+part['path'])
                        stream.write(data)
                except Exception:
                    stream.close();temporary.unlink();raise
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=row['sha256']:
                temporary.unlink();raise ValueError('Joined archive checksum mismatch')
            if p.exists():temporary.unlink();raise FileExistsError('Archive appeared while joining; preserved it.')
            temporary.rename(p)
        if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Archive SHA256 mismatch: '+row['path'])
        with zipfile.ZipFile(p) as z:
            if row['path']=='assets/cloud-data.zip':
                for item in json.loads(z.read('index.json')):
                    if item['path'].split('/')[0] in selected or item['path'].startswith('ccucm_minecraft/'):
                        checked_file(z,z.getinfo(item['object']),ROOT/item['path'],item['sha256'])
            elif row['path'].split('/')[0] in selected:
                prefix=row['path'].split('/')[0]
                delivered=json.loads((ROOT/prefix/'delivery_manifest.json').read_text(encoding='utf-8'))
                world_name=Path(delivered['world'].replace('\\','/')).name
                for info in z.infolist():
                    # Keep tracked portable docs; extract the actual world and absent previews.
                    target=ROOT/prefix/info.filename
                    if info.filename.startswith(world_name+'/'):
                        checked_file(z,info,target)
                    elif target.suffix.lower()=='.png' and not target.exists():
                        checked_file(z,info,target)
    for project in selected:
        manifest=ROOT/project/'delivery_manifest.json'
        data=json.loads(manifest.read_text(encoding='utf-8'));data['world']=str(ROOT/project/Path(data['world'].replace('\\','/')).name);data['archive']=str(ROOT/project/Path(data['archive'].replace('\\','/')).name)
        manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    baseline=ROOT/'nwpu_rebuild/planning/baseline.json'
    if 'nwpu_rebuild' in selected and baseline.exists():
        data=json.loads(baseline.read_text(encoding='utf-8'))
        data.setdefault('original_local_baseline_files',dict(data['baseline_files']))
        data['baseline_files']={name:hashlib.sha256((ROOT/'nwpu_minecraft'/name).read_bytes()).hexdigest() for name in data['baseline_files']}
        data['cloud_baseline_note']='Original hashes retained; active bindings account for Git text line-ending normalization.'
        baseline.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Restored:',', '.join(selected))
def server():
    p=ROOT/'ccucm_minecraft/tools/server-26.2.jar'
    if p.exists():return
    def get(url):
        with urllib.request.urlopen(url,timeout=90) as r:return r.read()
    versions=json.loads(get('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'))
    v=next(v for v in versions['versions'] if v['id']=='26.2')
    metadata=get(v['url'])
    if hashlib.sha1(metadata).hexdigest()!=v['sha1']:raise ValueError('Version metadata SHA1 differs')
    info=json.loads(metadata)['downloads']['server'];data=get(info['url'])
    if hashlib.sha1(data).hexdigest()!=info['sha1']:raise ValueError('Server SHA1 differs')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);print('Official 26.2 server downloaded and verified.')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('command',choices=['restore','server','build','validate','render','doctor']);ap.add_argument('project',nargs='?',default='all',choices=['all',*PROJECTS]);a=ap.parse_args()
    if a.command=='restore':restore(a.project);return
    if a.command=='server':server();return
    if a.command=='doctor':
        import importlib.util
        sys.path.insert(0,str(ROOT/'ccucm_minecraft/tools'));from crp_runtime import java_executable,font_path
        print('Python',sys.version.split()[0]);print('Dependencies',{n:bool(importlib.util.find_spec(n)) for n in ['numpy','PIL','nbtlib','pdfplumber']})
        print('Font',font_path());print('Java',java_executable());return
    if a.project=='all':ap.error('Choose one project for build/validate/render.')
    script=PROJECTS[a.project] if a.command=='build' else 'preview.py' if a.project=='ccucm_minecraft' and a.command=='render' else a.command+'.py'
    env=dict(os.environ,PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    subprocess.run([sys.executable,str(ROOT/a.project/'tools'/script)],cwd=ROOT/a.project,env=env,check=True)
if __name__=='__main__':main()
