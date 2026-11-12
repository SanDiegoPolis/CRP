from pathlib import Path
import ast,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
SRC=ROOT.parent/'nwpu_minecraft'
for name in ('geometry.py','nbt.py','voxel_render.py','navigation.py','exporter.py','validate.py'):
    s=(SRC/'tools'/name).read_text(encoding='utf-8').replace('西北工业大学','南京工业大学').replace('长安校区','江浦校区').replace('NWPU_Changan_26.2','NJTech_Jiangpu_26.2')
    if name=='exporter.py':
        s=s.replace("nbt.F(90)","nbt.F(150)").replace("第 41–42 页，2025 PDF","第 75 页，2023 PDF")
    if name=='validate.py':s=s.replace("+' 90 -8'","+' 150 -8'").replace('batch {batch}/60','batch {batch}/80')
    (ROOT/'tools'/name).write_text(s,encoding='utf-8')
source=(SRC/'tools/build_nwpu.py').read_text(encoding='utf-8')
selected=['spiral','block_building','regular','hip_roof','courtyard','stadium','courts']
lines=source.splitlines()
body='import geometry as g\nimport numpy as np\nstonewhite=g.block("quartz_bricks",(210,212,207))\nsilver=g.block("light_gray_concrete",(182,190,192))\nroofgreen=g.block("green_terracotta",(108,119,72))\nteal=g.block("warped_planks",(57,114,113))\n\n'
for node in ast.parse(source).body:
    if isinstance(node,ast.FunctionDef) and node.name in selected:body+='\n'.join(lines[node.lineno-1:node.end_lineno])+'\n\n'
(ROOT/'tools/models.py').write_text(body,encoding='utf-8')
for name in ('libraries','versions'):shutil.copytree(SRC/'validation'/name,ROOT/'validation'/name,dirs_exist_ok=True)
(ROOT/'validation/eula.txt').write_text('eula=true\n')
s=(SRC/'validation/server.properties').read_text().replace('25588','25589').replace('NWPU_Changan_26.2','NJTech_Jiangpu_26.2')
(ROOT/'validation/server.properties').write_text(s)
im=Image.open(ROOT/'research/official-map.png').convert('RGB').resize((1344,1824))
im.save(ROOT/'research/map-reference.png')
for name,box in [('north',(260,295,910,805)),('middle',(460,750,1100,1165)),('south',(595,1125,1170,1585))]:
    im.crop(box).resize(((box[2]-box[0])*2,(box[3]-box[1])*2)).save(ROOT/f'research/map-{name}.png')
print('26.2 engine prepared; official map reference uses 1344 x 1824 coordinates')
