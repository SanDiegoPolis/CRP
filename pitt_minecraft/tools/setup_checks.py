from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SHARED=ROOT.parent/'ccucm_minecraft'
src=(SHARED/'tools/preview.py').read_text(encoding='utf-8')
header=src[:src.index('def overview(')]
core=src[src.index('def greedy_rows('):src.index('def main():')]
core=core.replace('长春中医药大学','匹兹堡大学').replace('约 1.25 : 1','约 1.1 : 1')
(ROOT/'tools/voxel_render.py').write_text(header+core,encoding='utf-8')
src=(SHARED/'tools/validate.py').read_text(encoding='utf-8')
src=src.replace("WORLD=ROOT/'CCUCM_Jingyue_26.2'","WORLD=ROOT/'Pitt_Oakland_26.2'\nSHARED=ROOT.parent/'ccucm_minecraft'")
src=src.replace('4<=sy<=9','4<=sy<4+v.shape[0]//16')
start=src.index('def navigability(');end=src.index('def server_check(')
src=src[:start]+"from navigation import navigability\n\n"+src[end:]
src=src.replace("(ROOT/'tools/java25')","(SHARED/'tools/java25')").replace("str(ROOT/'tools/server-26.2.jar')","str(SHARED/'tools/server-26.2.jar')")
src=src.replace('CCUCM_Jingyue_26.2','Pitt_Oakland_26.2').replace('长春中医药大学｜净月校区 1.25:1','匹兹堡大学｜Oakland 1.1:1')
src=src.replace("command('setworldspawn 370 65 800 180 0')","command('setworldspawn '+' '.join(map(str,m['spawn']))+' 150 -12')")
src=src.replace('batch {batch}/20','batch {batch}/35')
src=src.replace("print('VALIDATION PASS',flush=True)","review_completed_run()\n    print('VALIDATION PASS',flush=True)")
(ROOT/'tools/validate.py').write_text(src,encoding='utf-8')
(ROOT/'validation/server.properties').write_text('''server-ip=127.0.0.1
server-port=25587
online-mode=false
level-name=Pitt_Oakland_26.2
view-distance=2
simulation-distance=3
gamemode=creative
difficulty=peaceful
max-tick-time=-1
generate-structures=false
spawn-protection=0
enable-query=false
enable-rcon=false
''')
(ROOT/'validation/eula.txt').write_text('eula=true\n')
import shutil
for folder in ('libraries','versions'):
    if (SHARED/'validation'/folder).exists():shutil.copytree(SHARED/'validation'/folder,ROOT/'validation'/folder,dirs_exist_ok=True)
print('Renderer and official-server validator prepared')
