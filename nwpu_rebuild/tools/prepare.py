from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parent.parent
OLD=ROOT.parent/'nwpu_minecraft'
for name in ('research','planning','validation'): (ROOT/name).mkdir(exist_ok=True)
for name in ('geometry.py','nbt.py','navigation.py','exporter.py','validate.py','voxel_render.py'):
    s=(OLD/'tools'/name).read_text(encoding='utf-8').replace('NWPU_Changan_26.2','NWPU_Changan_Rebuild_26.2').replace('西北工业大学｜长安校区 1.1:1','西北工业大学｜长安校区重制版 1.1:1')
    (ROOT/'tools'/name).write_text(s,encoding='utf-8')
s=(OLD/'tools/build_nwpu.py').read_text(encoding='utf-8').replace('NWPU_Changan_26.2','NWPU_Changan_Rebuild_26.2')
# Avoid odd-size cardinal sampling artifacts; control points remain unchanged.
s=s.replace('dx*cs+dz*sn+w/2','dx*cs+dz*sn+w//2').replace('-dx*sn+dz*cs+d/2','-dx*sn+dz*cs+d//2')
s=s.replace("e['x'][1]-w/2,e['z'][1]-d/2","e['x'][1]-w//2,e['z'][1]-d//2")
s=s.replace('[2,8,14,20,26,32,38,44]','[2,8,14,20,26,32,38]')
(ROOT/'tools/base.py').write_text(s,encoding='utf-8')
for name in ('library.png','qixiang.png','arena.png','east-gate.png','aerial.png','aircraft.png','dormitories.png','warriors.png','layout-2025.png'):
    shutil.copyfile(OLD/'research'/name,ROOT/'research'/name)
for name in ('libraries','versions'):shutil.copytree(OLD/'validation'/name,ROOT/'validation'/name,dirs_exist_ok=True)
props=(OLD/'validation/server.properties').read_text().replace('25588','25590').replace('NWPU_Changan_26.2','NWPU_Changan_Rebuild_26.2')
(ROOT/'validation/server.properties').write_text(props)
(ROOT/'validation/eula.txt').write_text('eula=true\n')
hashes={}
for file in ('build_manifest.json','validation_report.json','西北工业大学_长安校区_Java26.2.zip'):
    hashes[file]=hashlib.sha256((OLD/file).read_bytes()).hexdigest()
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'research').iterdir()}
out={'baseline_relative':'../nwpu_minecraft','baseline_files':hashes,'source_files':sources,
     'coordinate_version':'nwpu-illustrated-map-2025-north-up-v1','transform':{'x':'70 + (v - 375) * 2.6','z':'60 + (1690 - u) * 1.7','y':'model_y + 64','map_view_size':[1920,1311]},
     'coordinate_control_points':[{'name':n,'map_uv':[u,v],'world_xz':[round(70+(v-375)*2.6),round(60+(1690-u)*1.7)]} for n,u,v in [('东门',1108,889),('图书馆',1091,650),('启翔楼',635,638),('体育馆',1461,815),('博物馆',463,562)]],
     'limitation':'Control points preserve the established illustrated-map registration, not independent survey accuracy.'}
(ROOT/'planning/baseline.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('Independent rebuild prepared; original source and installed world left intact.')
