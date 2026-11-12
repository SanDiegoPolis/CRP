"""Ground-level paved-route connectivity; never treats a walk across grass as a pass."""
from pathlib import Path
from collections import deque
import json,sys
import numpy as np
ROOT=Path(__file__).resolve().parent.parent

def check(v,m):
    names=[p['Name'] for p in m['palette']]
    paved={'minecraft:gray_concrete','minecraft:smooth_stone','minecraft:white_concrete','minecraft:smooth_quartz','minecraft:oak_planks','minecraft:polished_andesite'}
    passing={'minecraft:air','minecraft:oak_sign'}
    valid=np.isin(v[4], [i for i,n in enumerate(names) if n in paved])
    valid&=np.isin(v[5],[i for i,n in enumerate(names) if n in passing])&np.isin(v[6],[i for i,n in enumerate(names) if n in passing])
    sx,_,sz=m['spawn'];assert valid[sz,sx],'Spawn must be on a supported, two-block-clear paved surface'
    seen=np.zeros_like(valid);seen[sz,sx]=True;q=deque([(sz,sx)])
    d,w=valid.shape
    while q:
        z,x=q.popleft()
        for dz,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            nz,nx=z+dz,x+dx
            if 0<=nz<d and 0<=nx<w and valid[nz,nx] and not seen[nz,nx]:seen[nz,nx]=True;q.append((nz,nx))
    results=[]
    for lm in m['building_groups']:
        ex,_,ez=lm['entrance'];choices=[]
        for z in range(max(0,ez-3),min(d,ez+4)):
            for x in range(max(0,ex-3),min(w,ex+4)):
                if seen[z,x]:choices.append(((x-ex)**2+(z-ez)**2,x,z))
        target=None
        if choices:
            _,x,z=min(choices);target=[x,69,z]
        results.append({'name':lm['name'],'outside_entry':lm['entrance'],'reachable_paved_point':target,'result':'PASS' if target else 'FAIL'})
    return {'result':'PASS' if all(r['result']=='PASS' for r in results) else 'FAIL',
            'scope':'Spawn to each plot exterior entry within 3 blocks; feet at y69, 2-block clearance, paved support only. Indoor stairs checked separately.',
            'reachable_paved_cells':int(seen.sum()),'plots_checked':len(results),'routes':results}

if __name__=='__main__':
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    file='final_voxels.npy' if '--final' in sys.argv else 'voxels.npy'
    result=check(np.load(ROOT/'tools'/file,mmap_mode='r'),m)
    (ROOT/'planning/exterior-route-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='routes'},ensure_ascii=False))
    print(json.dumps([r for r in result['routes'] if r['result']!='PASS'],ensure_ascii=False))
    sys.exit(0 if result['result']=='PASS' else 1)
