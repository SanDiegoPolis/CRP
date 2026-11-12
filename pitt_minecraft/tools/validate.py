from crp_runtime import java_executable, font_path
"""Independent NBT round-trip plus official 26.2 load/relight verification."""
from pathlib import Path
from collections import deque
import subprocess,time,json,math,traceback
import numpy as np
import nbt

ROOT=Path(__file__).resolve().parent.parent
WORLD=ROOT/'Pitt_Oakland_26.2'
SHARED=ROOT.parent/'ccucm_minecraft'

def host_diagnostic(line):
    # Host metrics and online chat-auth keys do not affect a localhost offline world test.
    return '/ERROR]' in line and (
        'English counter names in registry Perflib 009' in line or
        '[Yggdrasil Key Fetcher/ERROR]: Failed to request yggdrasil public key' in line)

def unpack(data,bits,size):
    per=64//bits;mask=(1<<bits)-1
    return np.array([(data[i//per]>>((i%per)*bits))&mask for i in range(size)],dtype=np.uint16)

def audit_nbt(v,m):
    regions=sorted((WORLD/'dimensions/minecraft/overworld/region').glob('*.mca'))
    count=states=signs=0
    palette=m['palette'];key=lambda p:json.dumps(p,sort_keys=True)
    lookup={key(p):i for i,p in enumerate(palette)}
    for path in regions:
        for idx,chunk in nbt.read_region(path):
            d=nbt.plain(nbt.C(chunk));cx,cz=d['xPos'],d['zPos'];count+=1
            assert d['DataVersion']==4903 and d['Status']=='minecraft:full'
            assert idx==(cx%32)+(cz%32)*32
            for section in d['sections']:
                sy=section['Y']
                if not 4<=sy<4+v.shape[0]//16:continue
                bs=section['block_states'];pal=bs['palette']
                ids=np.array([lookup[key(p)] for p in pal],dtype=np.uint16)
                if len(pal)==1:arr=np.full(4096,ids[0],dtype=np.uint16)
                else:
                    bits=max(4,(len(pal)-1).bit_length());ind=unpack(bs['data'],bits,4096)
                    assert int(ind.max())<len(pal);arr=ids[ind]
                arr=arr.reshape(16,16,16)
                expected=v[(sy-4)*16:(sy-3)*16,cz*16:cz*16+16,cx*16:cx*16+16]
                assert np.array_equal(arr,expected),(cx,sy,cz)
                states+=4096
            for b in d['block_entities']:
                assert b['id']=='minecraft:sign';assert len(b['front_text']['messages'])==4;signs+=1
    assert count==m['chunks']
    return {'regions':len(regions),'chunks':count,'decoded_block_states_compared':states,'signs':signs,'result':'PASS'}

from navigation import navigability

def server_check(v,m):
    work=ROOT/'validation';props=(work/'server.properties').read_text()
    # The test binds to localhost only; force upgrade discards cached light/height maps.
    props=props.replace('level-name=template','level-name=Pitt_Oakland_26.2').replace('view-distance=3','view-distance=2')
    import re
    props=re.sub(r'(?m)^pause-when-empty-seconds=.*$', 'pause-when-empty-seconds=-1',props)
    if 'pause-when-empty-seconds=' not in props:props+='\npause-when-empty-seconds=-1\n'
    (work/'server.properties').write_text(props)
    java=java_executable()
    logpath=work/'campus-26.2.log';log=open(logpath,'w',encoding='utf-8')
    args=[str(java),'-Xms512M','-Xmx4G','-jar',str(SHARED/'tools/server-26.2.jar'),'--universe',str(ROOT),'--world',WORLD.name,'--forceUpgrade','--eraseCache','nogui']
    p=subprocess.Popen(args,cwd=work,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    def read():return logpath.read_text(encoding='utf-8',errors='replace')
    def command(s):p.stdin.write(s+'\n');p.stdin.flush()
    def until(marker,timeout=180):
        end=time.time()+timeout
        while time.time()<end:
            t=read()
            if marker in t:return
            if p.poll() is not None:raise RuntimeError(t[-6000:])
            time.sleep(.5)
        raise TimeoutError(marker+'\n'+read()[-3000:])
    try:
        until('Done (')
        print('Official 26.2 server loaded world.',flush=True)
        command('forceload remove all')
        # Relight all authored chunks in 16x16-chunk batches, keeping memory bounded.
        batch=0;probes=[]
        for z0 in range(0,m['dimensions'][2],256):
            for x0 in range(0,m['dimensions'][0],256):
                x1=min(m['dimensions'][0]-1,x0+255);z1=min(m['dimensions'][2]-1,z0+255)
                command(f'forceload add {x0} {z0} {x1} {z1}')
                time.sleep(1)
                # Confirm each chunk is available; all probes are checked in-game.
                loaded=[]
                for z in range(z0,z1+1,16):
                    for x in range(x0,x1+1,16):
                        marker=f'LOADED_{x}_{z}'
                        command(f'execute if loaded {x} 64 {z} run say {marker}')
                        loaded.append((x,z,marker))
                time.sleep(1)
                deadline=time.time()+90
                while time.time()<deadline:
                    t=read();missing=[c for c in loaded if c[2] not in t]
                    if not missing:break
                    for x,z,marker in missing:command(f'execute if loaded {x} 64 {z} run say {marker}')
                    time.sleep(1)
                else:raise RuntimeError(f'{len(missing)} chunks failed to load')
                # Check a recorded landmark block in this batch, or terrain.
                for lm in m['landmarks']:
                    x,z=lm['x'],lm['z']
                    if x0<=x<=x1 and z0<=z<=z1:
                        yy=int(np.max(np.flatnonzero(v[:,z,x])))
                        b=m['palette'][int(v[yy,z,x])]['Name'];marker=f'BLOCK_OK_{x}_{z}_{yy}'
                        command(f'execute if block {x} {yy+64} {z} {b} run say {marker}');probes.append(marker)
                command('save-all flush');time.sleep(.7)
                command(f'forceload remove {x0} {z0} {x1} {z1}')
                batch+=1;print(f'Loaded and checked batch {batch}/35',flush=True)
        command('setworldspawn '+' '.join(map(str,m['spawn']))+' 150 -12')
        command('time set noon')
        command('save-all flush');time.sleep(2)
        command('stop');p.wait(timeout=120)
        log.close();t=read()
        missing=[marker for marker in probes if marker not in t]
        errors=[s for s in t.splitlines() if ('/ERROR]' in s and not host_diagnostic(s)) or any(bad in s for bad in ['Failed to load','Unknown block','Invalid palette','Exception loading','Could not load'])]
        assert not missing,missing
        assert not errors,errors[:20]
        assert p.returncode==0
        # Restore user-facing single-player settings after dedicated-server testing.
        level=nbt.load(WORLD/'level.dat');d=level['Data'][1]
        d['allowCommands']=nbt.B(1);d['GameType']=nbt.I(1);d['LevelName']=nbt.T('匹兹堡大学｜Oakland 1.1:1')
        nbt.save(WORLD/'level.dat',level)
        return {'result':'PASS','server_version':'26.2','every_authored_chunk_loaded':m['chunks'],'landmark_blocks_checked':len(probes),'errors':errors,'exit_code':p.returncode,'log':'validation/campus-26.2.log'}
    finally:
        if p.poll() is None:
            try:command('stop');p.wait(timeout=30)
            except Exception:p.terminate()

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    print('Independent region decode...',flush=True)
    result={'nbt_round_trip':audit_nbt(v,m)};print(result['nbt_round_trip'],flush=True)
    result['walking_routes']=navigability(v,m);print(json.dumps(result['walking_routes'],ensure_ascii=False),flush=True)
    (ROOT/'validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(c['result']=='PASS' for c in result['walking_routes']),'Fix stairs before server validation'
    result['official_server']=server_check(v,m)
    (ROOT/'validation_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    review_completed_run()
    print('VALIDATION PASS',flush=True)

def review_completed_run():
    """Review the finished run after classifying Windows performance-counter diagnostics.
    No world-load error is excluded; the one allowlisted host metric diagnostic is retained.
    """
    import re
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    t=(ROOT/'validation/campus-26.2.log').read_text(encoding='utf-8')
    assert 'Done (' in t and 'Stopping server' in t
    assert 'All dimensions are saved' in t.split('Stopping server')[-1]
    loaded=set((int(x),int(z)) for x,z in re.findall(r'LOADED_(\d+)_(\d+)',t))
    expected={(x,z) for x in range(0,m['dimensions'][0],16) for z in range(0,m['dimensions'][2],16)}
    assert loaded==expected,(len(loaded),len(expected))
    probes=[]
    for lm in m['landmarks']:
        x,z=lm['x'],lm['z'];yy=int(np.max(np.flatnonzero(v[:,z,x])))
        marker=f'BLOCK_OK_{x}_{z}_{yy}';assert marker in t,marker;probes.append(marker)
    host=[s for s in t.splitlines() if host_diagnostic(s)]
    errors=[s for s in t.splitlines() if ('/ERROR]' in s and s not in host) or any(k in s for k in ['Failed to load','Unknown block','Invalid palette','Exception loading','Could not load'])]
    assert not errors,errors
    lit=0;seen=set()
    for file in (WORLD/'dimensions/minecraft/overworld/region').glob('*.mca'):
        for _,c in nbt.read_region(file):
            pos=(c['xPos'][1]*16,c['zPos'][1]*16)
            if pos not in expected:continue
            seen.add(pos)
            if c.get('isLightOn')==nbt.B(1):lit+=1
    assert seen==expected
    assert lit==m['chunks'],('lighting',lit)
    level=nbt.load(WORLD/'level.dat');d=level['Data'][1]
    d['allowCommands']=nbt.B(1);d['GameType']=nbt.I(1);d['LevelName']=nbt.T('匹兹堡大学｜Oakland 1.1:1')
    nbt.save(WORLD/'level.dat',level)
    report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
    report['official_server']={'result':'PASS','server_version':'26.2','every_authored_chunk_loaded':len(loaded),'landmark_blocks_checked':len(probes),'authored_chunks_with_saved_lighting':lit,'clean_shutdown':True,'world_errors':errors,'host_diagnostics':host,'log':'validation/campus-26.2.log'}
    (ROOT/'validation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Completed official run verified:',len(loaded),'chunks loaded;',lit,'relit;',len(probes),'landmarks',flush=True)

if __name__=='__main__':main()
