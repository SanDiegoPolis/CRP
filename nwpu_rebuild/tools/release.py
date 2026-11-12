from pathlib import Path
import json,hashlib,zipfile,shutil,sys
import numpy as np
import nbt
ROOT=Path(__file__).resolve().parent.parent;WORLD=ROOT/'NWPU_Changan_Rebuild_26.2';OLD=ROOT.parent/'nwpu_minecraft'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def evidence(m):
    sources=[
      {'id':'MAP','url':'https://npuinternationalcollege.nwpu.edu.cn/__local/E/6E/25/5F37628D7D0C7315914F51E5518_4F623DF5_1F4A3A2.pdf','file':'layout-2025.png','date':'2025 brochure, printed pp.41-42','kind':'illustrated map; not survey'},
      {'id':'PHOTOS','url':'https://www.nwpu.edu.cn/info/1198/92938.htm','date':'published 2024-10-08; individual photographs 2022-2024','kind':'official real photographs'},
      {'id':'SCENERY','url':'https://yzb.nwpu.edu.cn/new/xxjj/xyfg.htm','date':'viewed 2026-09-24','kind':'official campus photo index'}]
    mapping={'图书馆与启真楼':'library.png','启翔楼':'qixiang.png','翱翔体育馆':'arena.png','东大门':'east-gate.png','军工素质教育实践中心':'aircraft.png'}
    rows=[]
    for obj in m['objects']:
        pic=mapping.get(obj['name'])
        rows.append({'id':obj['object_id'],'name':obj['name'],'map':'MAP','map_uv':obj['map_uv'],
          'facade_source':pic or ('dormitories.png' if '公寓' in obj['name'] else 'aerial.png / map typology'),
          'layout_confidence':'B: interpreted official illustrated map','facade_confidence':'B: identifiable photograph features' if pic else 'C: simplified/inferred typology',
          'interior':'C: designed for exploration, not measured rooms','adaptation':obj['adaptation'],
          'missing_evidence':['survey dimensions','complete side/rear photos','measured interior']})
    data={'sources':sources,'objects':rows,'local_reference_sha256':{p.name:sha(p) for p in (ROOT/'research').glob('*.png')}}
    (ROOT/'planning/evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def difference(m):
    oldm=json.loads((OLD/'build_manifest.json').read_text(encoding='utf-8'))
    old=np.load(OLD/'tools/voxels.npy',mmap_mode='r');new=np.load(ROOT/'tools/final_voxels.npy',mmap_mode='r')
    # Compare canonical states, not local palette indices.
    key=lambda p:json.dumps(p,sort_keys=True);lookup={key(p):i for i,p in enumerate(m['palette'])}
    mp=np.array([lookup.get(key(p),65535) for p in oldm['palette']],np.uint16)
    total=added=removed=replaced=0
    for y in range(old.shape[0]):
        before=mp[old[y]];after=new[y];change=before!=after;total+=int(change.sum())
        added+=int(np.count_nonzero(change&(before==0)&(after!=0)))
        removed+=int(np.count_nonzero(change&(before!=0)&(after==0)))
        replaced+=int(np.count_nonzero(change&(before!=0)&(after!=0)))
    result={'changed_block_positions':total,'added':added,'removed':removed,'replaced':replaced,
      'meaning':'Block edits relative to the original; not a realism or similarity score.'}
    (ROOT/'planning/changes.json').write_text(json.dumps(result,indent=2),encoding='utf-8');return result

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'));r=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
    assert r['official_server']['result']=='PASS' and r['final_saved_world_readback']['result']=='PASS'
    assert r['exterior_paved_routes']['result']=='PASS' and r['building_overlap_review']['result']=='PASS'
    assert all(c['result']=='PASS' for c in r['walking_routes'])
    assert (ROOT/'planning/visual-review.json').is_file()
    visual=json.loads((ROOT/'planning/visual-review.json').read_text(encoding='utf-8'))
    assert visual['delivery_decision']=='READY_WITH_DECLARED_APPROXIMATIONS'
    d=nbt.plain(nbt.C(nbt.load(WORLD/'level.dat')))['Data']
    assert d['DataVersion']==4903 and d['GameType']==1 and d['spawn']['pos']==m['spawn']
    baseline=json.loads((ROOT/'planning/baseline.json').read_text(encoding='utf-8'))
    for name,digest in baseline['baseline_files'].items():assert sha(OLD/name)==digest,'Original project unexpectedly changed'
    evidence(m);delta=difference(m);sx,sy,sz=m['spawn']
    rows=['| '+c['building']+' | `/tp @s '+' '.join(map(str,c['arrival']))+'` |' for c in r['walking_routes'] if 'arrival' in c]
    readme=f'''# 西北工业大学 · 长安校区重制版

Campus Reconstruction Project · 使用 `minecraft-campus-rebuild` 高校复原技能重建

**Minecraft Java 26.2 原版方块** · 约 **1.1:1** · 2026-09-24 重制

## 在游戏里打开

世界文件夹：**NWPU_Changan_Rebuild_26.2**。
游戏菜单名称：**西北工业大学｜长安校区重制版 1.1:1**。

解压 ZIP 后，把上述世界文件夹放进实际实例的 `saves` 中。
本对话已指定的同步目标是 `D:\\MC\\.minecraft\\versions\\26.2-Fabric 0.19.5\\saves`；同步结果以同目录工程中的 `game_sync_manifest.json` 为准。
正确关系为 `saves/NWPU_Changan_Rebuild_26.2/level.dat`。

这是独立重制世界，旧的 `NWPU_Changan_26.2` 保留，可以分别进入比较。无需额外材质包或模组。

## 本次改了什么

- **图书馆与启真楼**：把旧版厚大的整体屋面改为较窄的弧形主楼，重新制作斜坡轮廓、水平遮阳线、细柱、较高端部、低层侧翼与前庭采光体；主楼七层可通行。
- **启翔楼**：重新处理四角较高楼体、深色檐口、分层坡屋顶、入口门厅与中央庭院，增加可连续到达上层的楼梯。
- **翱翔体育馆**：区分双馆屋顶、细构架、圆窗、入口前庭和斜柱，保留室内球场与看台；入口高差采用游戏适配，没有按实测恢复完整台阶。
- **东大门**：重新制作成束立柱、横梁、浅钵柱头与连续校名墙；步行从门区开放通道经过。
- **教学区与普通楼栋**：重做材质节奏、部分院系楼的庭院体量、宿舍窗格与突出窗檐；普通楼体仍属于基于地图的类型化近似。
- **室外路线**：增加入口到校内铺装网络的连接；图书馆前新增步行桥，少量宿舍入口朝向调整，网络空间安全学院西移 16 格以留出通行间距。这些属于游戏游览适配，具体位置不是实测结论。

保留既有北向坐标基准和主要片区关系，完整重新生成全校 **79 组建筑与场地**、**44 个导览地标**，范围 **1536 × 2560 方块**。
相对旧版共改变 **{delta['changed_block_positions']:,} 个方块位置**，其中包含新增、删除及替换；这一数字不是外观相似度。

## 游览

出生点：`{sx} {sy} {sz}`，东门外，向西面对校园。创造模式、和平难度、固定晴天中午，命令已开启。
双击空格飞行，空格上升，Shift 下降。

路线：**东门 → 何尊广场 → 图书馆与启真湖 → 教学东/西楼 → 体育馆与生活区 → 启翔楼与启翔湖 → 博物馆航空展区**。

| 地点 | 传送命令 |
| --- | --- |
| 东门外 | `/tp @s {sx} {sy} {sz}` |
{chr(10).join(rows)}

## 检查结果

- 建筑生成阶段，79 组模型间未发现已有楼体被后放入楼体覆盖。
- 出生点到 **79 组场地的外侧入口**全部通过铺装连通检查：脚下必须为铺装、头顶两格净空；不使用穿草坪替代步道。目标容差 3 格；这不等于全部房间均已逐间检查。
- 图书馆、启翔楼、博物馆、教学西楼、餐厅、体育馆与一栋宿舍通过模板及世界落位后的入口/指定楼层通行检查。
- **{m['chunks']:,} 个预制区块**经官方 Java 26.2 服务端逐批加载、地标核对、光照计算、保存并正常关闭，无世界加载错误。
- 服务端最终保存后重新解码 **{r['final_saved_world_readback']['decoded_block_states_compared']:,} 个创作范围内方块状态**，与设计逐格比对通过；最终预览使用此回读结果。
- 服务端在创作区边缘生成的相邻区块单独计数，不冒充手工创作区块。区域文件摘要见 `planning/final-region-binding.json`。
- 实际客户端画面、夜景和帧率没有测试。离线预览不等于客户端截图，玻璃及树叶采用简化颜色。

## 来源与边界

采用学校官方 2025 招生简章示意地图与 2022—2024 年的建筑照片、航拍。本次沿用已核对的图面到游戏坐标变换，**没有新增测绘级尺寸或高程数据**，也不声称包含 2026 年所有建设变化。

来源与置信度分开记录在 `planning/evidence.json`：主要地标依据照片的识别特征，普通学院楼、宿舍、室内、局部地形与路径含估计或设计补全。资料缺失的背立面和内部房间没有标作实景精确复原。

- [学校官方招生简章，长安校区导览图第 41–42 页](https://npuinternationalcollege.nwpu.edu.cn/__local/E/6E/25/5F37628D7D0C7315914F51E5518_4F623DF5_1F4A3A2.pdf)
- [学校官网建筑照片与航拍：建校 86 周年图片展](https://www.nwpu.edu.cn/info/1198/92938.htm)
- [学校研究生招生信息网：校园风光](https://yzb.nwpu.edu.cn/new/xxjj/xyfg.htm)

对照图分别提供旧版/重制版比较与实景/模型特征核对；不提供未经测量的“还原度百分比”。
'''
    (ROOT/'使用说明.md').write_text(readme,encoding='utf-8');shutil.copyfile(ROOT/'使用说明.md',WORLD/'校园说明.md')
    extras=['使用说明.md','校园导览.png','校园鸟瞰.png','图书馆与启真湖.png','启翔楼与启翔湖.png','翱翔体育馆.png','东门与何尊广场.png','博物馆航空展区.png','重制前后对比.png','实景与模型核对.png','validation_report.json']
    reports=['planning/evidence.json','planning/changes.json','planning/visual-review.json','planning/exterior-route-validation.json','planning/building-collision-review.json','planning/final-region-binding.json','planning/baseline.json','planning/project-brief.md']
    world_files=[p for p in sorted(WORLD.rglob('*')) if p.is_file() and p.name not in {'session.lock','level.dat_old'}]
    all_files=world_files+[ROOT/p for p in extras+reports]
    manifest={'release':m['release'],'coordinate_version':m['coordinate_version'],'minecraft_version':'26.2','files':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in all_files],
       'validation_reports':[{'file':p,'sha256':sha(ROOT/p),'kind':k} for p,k in [('validation_report.json','world-runtime-and-roundtrip'),('planning/exterior-route-validation.json','routes'),('planning/visual-review.json','visual')]]}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    archive=ROOT/'西北工业大学_长安校区_重制版_Java26.2.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in all_files+[ROOT/'manifest.json']:z.write(p,p.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist())=={p.relative_to(ROOT).as_posix() for p in all_files+[ROOT/'manifest.json']}
        for p in all_files:assert hashlib.sha256(z.read(p.relative_to(ROOT).as_posix())).hexdigest()==sha(p)
    out={'archive':str(archive),'bytes':archive.stat().st_size,'files':len(all_files)+1,'sha256':sha(archive),'world':str(WORLD),'validated':True}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'SHA256.txt').write_text(out['sha256']+'  '+archive.name+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
