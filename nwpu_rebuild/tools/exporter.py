from pathlib import Path
import numpy as np
import math,json,shutil,time
import nbt

def pack_values(arr,bits):
    a=np.asarray(arr,dtype=np.uint64).ravel();per=64//bits
    b=np.zeros(math.ceil(len(a)/per)*per,dtype=np.uint64);b[:len(a)]=a
    return np.bitwise_or.reduce(b.reshape(-1,per)<<(np.arange(per,dtype=np.uint64)*bits),axis=1).tolist()
def pnbt(p):
    d={'Name':nbt.T(p['Name'])}
    if p.get('Properties'):d['Properties']=nbt.C({k:nbt.T(v) for k,v in p['Properties'].items()})
    return d
def section(sy,arr):
    uniq,inv=np.unique(arr,return_inverse=True);bs={'palette':nbt.LS(10,[pnbt(PAL[int(i)]) for i in uniq])}
    if len(uniq)>1:bs['data']=nbt.LA(pack_values(inv,max(4,(len(uniq)-1).bit_length())))
    return {'Y':nbt.B(sy),'block_states':nbt.C(bs),'biomes':nbt.C({'palette':nbt.LS(8,['minecraft:plains'])})}

def export():
    print('Exporting 26.2 Anvil world...',flush=True)
    assert len(PAL)<256
    registry=json.loads((SHARED/'tools/generated/reports/blocks.json').read_text())
    for p in PAL:
        assert p['Name'] in registry,p
        for k,v in p.get('Properties',{}).items():assert v in registry[p['Name']]['properties'][k],p
    template=SHARED/'validation/template';WORLD.mkdir(exist_ok=True)
    shutil.copytree(template/'data',WORLD/'data',dirs_exist_ok=True)
    level=nbt.load(template/'level.dat');d=level['Data'][1]
    d['LevelName']=nbt.T('西北工业大学｜长安校区重制版 1.1:1');d['GameType']=nbt.I(1);d['allowCommands']=nbt.B(1)
    sx,sz=SPAWN;sy=int(DEM[sz,sx])+65
    d['spawn']=nbt.C({'pos':nbt.IA([sx,sy,sz]),'yaw':nbt.F(90),'pitch':nbt.F(-8),'dimension':nbt.T('minecraft:overworld')})
    d['LastPlayed']=nbt.L(int(time.time()*1000));nbt.save(WORLD/'level.dat',level)
    rules=nbt.load(WORLD/'data/minecraft/game_rules.dat');r=rules['data'][1]
    for k in ['advance_time','advance_weather','spawn_mobs','spawn_monsters','spawn_patrols','spawn_phantoms','spawn_wandering_traders','mob_griefing','raids','pvp']:r['minecraft:'+k]=nbt.B(0)
    r['minecraft:random_tick_speed']=nbt.I(0);r['minecraft:respawn_radius']=nbt.I(0);r['minecraft:fire_spread_radius_around_player']=nbt.I(0)
    nbt.save(WORLD/'data/minecraft/game_rules.dat',rules)
    fixed=[]
    for syc in range(-4,4):
        a=np.full((16,16,16),g.stone,dtype=np.uint8)
        if syc==-4:a[0]=g.bedrock
        if syc==3:a[12:]=g.dirt
        fixed.append(section(syc,a))
    upperair=[section(s,np.zeros((16,16,16),dtype=np.uint8)) for s in range(4+H//16,20)]
    total=0
    # Serialize one region at a time to keep peak memory bounded.
    for rz in range(math.ceil(D/512)):
        for rx in range(math.ceil(W/512)):
            chunks={}
            for cz in range(rz*32,min((rz+1)*32,D//16)):
                for cx in range(rx*32,min((rx+1)*32,W//16)):
                    a=V[:,cz*16:cz*16+16,cx*16:cx*16+16]
                    hm=129+(H-1-np.argmax((a!=0)[::-1],axis=0));height=nbt.LA(pack_values(hm,9))
                    sections=fixed+[section(4+s,a[s*16:(s+1)*16]) for s in range(H//16)]+upperair
                    bes=[e for e in g.BE.get((cx,cz),[]) if PAL[int(V[e['y'][1]-64,e['z'][1],e['x'][1]])]['Name'].endswith('_sign')]
                    c={'DataVersion':nbt.I(4903),'xPos':nbt.I(cx),'zPos':nbt.I(cz),'yPos':nbt.I(-4),'Status':nbt.T('minecraft:full'),'LastUpdate':nbt.L(0),'InhabitedTime':nbt.L(0),'isLightOn':nbt.B(0),
                       'sections':nbt.LS(10,sections),'Heightmaps':nbt.C({k:height for k in ['WORLD_SURFACE','OCEAN_FLOOR','MOTION_BLOCKING','MOTION_BLOCKING_NO_LEAVES']}),
                       'block_entities':nbt.LS(10,bes),'block_ticks':nbt.LS(10,[]),'fluid_ticks':nbt.LS(10,[]),'PostProcessing':nbt.LS(9,[(2,[]) for _ in range(24)]),
                       'structures':nbt.C({'starts':nbt.C({}),'References':nbt.C({})})}
                    chunks[cx%32+32*(cz%32)]=c;total+=1
            nbt.write_region(WORLD/f'dimensions/minecraft/overworld/region/r.{rx}.{rz}.mca',chunks)
            print('Region',rx,rz,'chunks',total,flush=True)
    np.save(ROOT/'tools/voxels.npy',V);np.save(ROOT/'tools/terrain.npy',DEM)
    manifest={'title':'西北工业大学 · 长安校区','version':'26.2','data_version':4903,'scale':'约 1.1 方块 / 米，局部体量适配','dimensions':[W,H,D],'spawn':[sx,sy,sz],'chunks':total,
              'palette':PAL,'colors':COLORS,'landmarks':LANDMARKS,'navigation_checks':CHECKS,'source_map':'官方国际学生招生简章，第 41–42 页，2025 PDF','above_terrain_blocks':int(sum(np.count_nonzero(V[y][DEM<y]) for y in range(1,H)))}
    (ROOT/'build_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Export complete:',total,'chunks',flush=True)

