from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent.parent
PITT=ROOT.parent/'pitt_minecraft';SHARED=ROOT.parent/'ccucm_minecraft'
for name in ('geometry.py','nbt.py','voxel_render.py'):
    src=(PITT/'tools'/name).read_text(encoding='utf-8')
    src=src.replace('匹兹堡大学','西北工业大学').replace('Pitt_Oakland_26.2','NWPU_Changan_26.2')
    (ROOT/'tools'/name).write_text(src,encoding='utf-8')
src=(PITT/'tools/build_pitt.py').read_text(encoding='utf-8')
export=src[src.index('def pack_values('):src.index('def build():')]
export=export.replace("sx,sz=xy(1336,696);sy=int(DEM[sz,sx])+65","sx,sz=SPAWN;sy=int(DEM[sz,sx])+65")
export=export.replace("'yaw':nbt.F(150),'pitch':nbt.F(-12)","'yaw':nbt.F(90),'pitch':nbt.F(-8)")
export=export.replace('匹兹堡大学｜Oakland 1.1:1','西北工业大学｜长安校区 1.1:1').replace('匹兹堡大学 · 奥克兰主校区','西北工业大学 · 长安校区')
export=export.replace("'above_terrain_blocks':", "'source_map':'官方国际学生招生简章，第 41–42 页，2025 PDF','above_terrain_blocks':")
(ROOT/'tools/exporter.py').write_text('from pathlib import Path\nimport numpy as np\nimport math,json,shutil,time\nimport nbt\n\n'+export,encoding='utf-8')
src=(PITT/'tools/validate.py').read_text(encoding='utf-8')
src=src.replace('Pitt_Oakland_26.2','NWPU_Changan_26.2').replace("SHARED=ROOT.parent/'ccucm_minecraft'","SHARED=ROOT.parent/'ccucm_minecraft'")
src=src.replace('匹兹堡大学｜Oakland 1.1:1','西北工业大学｜长安校区 1.1:1').replace("+' 150 -12'","+' 90 -8'")
src=src.replace('batch {batch}/35','batch {batch}/60')
(ROOT/'tools/validate.py').write_text(src,encoding='utf-8')
(ROOT/'tools/navigation.py').write_text((PITT/'tools/navigation.py').read_text(encoding='utf-8'),encoding='utf-8')
(ROOT/'validation/eula.txt').write_text('eula=true\n')
(ROOT/'validation/server.properties').write_text('''server-ip=127.0.0.1
server-port=25588
online-mode=false
level-name=NWPU_Changan_26.2
view-distance=2
simulation-distance=3
gamemode=creative
difficulty=peaceful
max-tick-time=-1
generate-structures=false
spawn-protection=0
enable-query=false
enable-rcon=false
pause-when-empty-seconds=-1
''')
for name in ('libraries','versions'):
    shutil.copytree(PITT/'validation'/name,ROOT/'validation'/name,dirs_exist_ok=True)
print('Vanilla 26.2 export/validation engine ready')
