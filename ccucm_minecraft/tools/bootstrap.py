from crp_runtime import java_executable, font_path
from pathlib import Path
import subprocess, time, json
BASE=Path(__file__).resolve().parent.parent
ROOT=BASE/'validation'; ROOT.mkdir(exist_ok=True)
(ROOT/'eula.txt').write_text('eula=true\n')
(ROOT/'server.properties').write_text('''server-ip=127.0.0.1
server-port=25586
online-mode=false
enable-status=false
level-name=template
gamemode=creative
difficulty=peaceful
spawn-protection=0
view-distance=3
simulation-distance=3
generate-structures=false
level-type=minecraft:flat
generator-settings={"layers":[{"block":"minecraft:bedrock","height":1},{"block":"minecraft:stone","height":123},{"block":"minecraft:dirt","height":4},{"block":"minecraft:grass_block","height":1}],"biome":"minecraft:plains","lakes":false,"features":false,"structure_overrides":[]}
max-tick-time=-1
''')
java=java_executable()
log=open(ROOT/'bootstrap.log','w',encoding='utf-8')
p=subprocess.Popen([str(java),'-Xms256M','-Xmx2G','-jar',str(BASE/'tools/server-26.2.jar'),'nogui'],cwd=ROOT,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True)
deadline=time.time()+180
while time.time()<deadline:
    time.sleep(1)
    text=(ROOT/'bootstrap.log').read_text(encoding='utf-8',errors='replace')
    if 'Done (' in text:
        p.stdin.write('setworldspawn 370 65 788 180\ntime set noon\ngamerule minecraft:advance_time false\ngamerule minecraft:advance_weather false\ngamerule minecraft:spawn_mobs false\nstop\n');p.stdin.flush()
        p.wait(timeout=90);print('Template server complete:',p.returncode,flush=True);break
    if p.poll() is not None: print(text[-6000:]);raise SystemExit(p.returncode)
else: p.terminate();raise RuntimeError('Template startup timed out')
print(text[-2000:],flush=True)
