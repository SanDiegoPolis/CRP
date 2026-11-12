from pathlib import Path
from collections import deque
import json,numpy as np
ROOT=Path(__file__).resolve().parent.parent

def walk(a,palette,start,area):
    pas=np.array([p['Name'] in ['minecraft:air','minecraft:oak_sign','minecraft:poppy','minecraft:dandelion','minecraft:azure_bluet','minecraft:short_grass','minecraft:fern'] for p in palette])
    clear=pas[a];valid=np.zeros(a.shape,dtype=bool)
    valid[1:-1]=clear[1:-1]&clear[2:]&(~clear[:-2])
    assert valid[start],('invalid start',start)
    q=deque([start]);seen={start};floorseen=set();positions={}
    while q:
        y,z,x=q.popleft()
        if area(x,z):floorseen.add(y);positions.setdefault(y,(x,y,z))
        for dz,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            nz,nx=z+dz,x+dx
            if not(0<=nz<a.shape[1] and 0<=nx<a.shape[2]):continue
            for dy in (0,1,-1):
                ny=y+dy
                if not(1<=ny<a.shape[0]-1):continue
                st=(ny,nz,nx)
                if st not in seen and valid[st] and (dy!=1 or clear[y+2,z,x]):seen.add(st);q.append(st)
    return floorseen,len(seen),positions

def navigability(v,m):
    results=[]
    for check in m['navigation_checks']:
        name=check['name'];w=check['width'];d=check['depth']
        a=np.load(ROOT/'tools'/('check_'+name.replace(' ','_')+'.npy'))
        # Begin on the surrounding ground, away from the entrance steps.
        start=(1,d-1,2)
        area=lambda x,z:8<x<w-8 and 8<z<d-12
        levels,count,positions=walk(a,m['palette'],start,area)
        missing=[h for h in check['targets'] if h not in levels]
        results.append({'building':name,'check':'template entrance and upper-floor walking; two-block player clearance','target_heights':check['targets'],'missing':missing,'reachable_positions':count,'result':'FAIL' if missing else 'PASS'})
        if v is not None:
            lm=next(l for l in m['landmarks'] if l['name']==name)
            r=int(np.hypot(w,d)/2)+17;cx,cz=lm['x'],lm['z'];base=lm['base']
            x0,z0=max(0,cx-r),max(0,cz-r);x1,z1=min(v.shape[2],cx+r+1),min(v.shape[1],cz+r+1)
            world=v[:,z0:z1,x0:x1]
            pas=np.array([p['Name'] in ['minecraft:air','minecraft:oak_sign','minecraft:short_grass','minecraft:fern'] for p in m['palette']])
            clear=pas[world];valid=np.zeros(world.shape,dtype=bool);valid[1:-1]=clear[1:-1]&clear[2:]&(~clear[:-2])
            ex,_,ez=lm['entrance'];localx,localz=ex-x0,ez-z0
            candidates=[]
            for z in range(max(1,localz-8),min(world.shape[1]-1,localz+9)):
                for x in range(max(1,localx-8),min(world.shape[2]-1,localx+9)):
                    for y in range(max(1,base-10),base+12):
                        if valid[y,z,x]:candidates.append(((x-localx)**2+(z-localz)**2+(y-base-1)**2,(y,z,x)))
            assert candidates,('no arrival',name)
            start=min(candidates)[1]
            angle=np.radians(lm['angle']);cs,sn=np.cos(angle),np.sin(angle)
            def within(x,z):
                dx=x+x0-cx;dz=z+z0-cz;lx=dx*cs+dz*sn+w/2;lz=-dx*sn+dz*cs+d/2
                return 10<lx<w-10 and 10<lz<d-14
            levels,count,positions=walk(world,m['palette'],start,within)
            targets=[base+h for h in check['targets']];missing=[h+64 for h in targets if h not in levels]
            results.append({'building':name,'check':'placed world after rotation: arrival to interior and floors','arrival':[start[2]+x0,start[0]+64,start[1]+z0],'target_world_y':[h+64 for h in targets],'missing':missing,'reachable_positions':count,'result':'FAIL' if missing else 'PASS'})
    return results

if __name__=='__main__':
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    v=np.load(ROOT/'tools/voxels.npy',mmap_mode='r')
    print(json.dumps(navigability(v,m),ensure_ascii=False,indent=2),flush=True)
