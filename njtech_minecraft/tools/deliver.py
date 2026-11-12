from pathlib import Path
import json,zipfile,hashlib,shutil
import nbt
ROOT=Path(__file__).resolve().parent.parent
WORLD=ROOT/'NJTech_Jiangpu_26.2'

def main():
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    r=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
    assert r['nbt_round_trip']['result']=='PASS'
    assert r['official_server']['result']=='PASS'
    assert r['official_server']['authored_chunks_with_saved_lighting']==m['chunks']
    assert all(c['result']=='PASS' for c in r['walking_routes'])
    data=nbt.plain(nbt.C(nbt.load(WORLD/'level.dat')))['Data']
    assert data['DataVersion']==4903 and data['GameType']==1 and data['allowCommands']==1
    assert data['spawn']['pos']==m['spawn'] and data['spawn']['yaw']==150
    rows=[]
    for c in r['walking_routes']:
        if 'arrival' in c:rows.append('| '+c['building']+' | `/tp @s '+' '.join(map(str,c['arrival']))+'` |')
    sx,sy,sz=m['spawn']
    readme=f'''# 南京工业大学 · 江浦校区

**Campus Reconstruction Project · 校园复原工程**

Minecraft Java **26.2 原版方块存档** · 约 **1.1:1** · 创造模式

## 打开存档

解压「南京工业大学_江浦校区_Java26.2.zip」，将其中的 **NJTech_Jiangpu_26.2** 文件夹放入所用游戏实例的 `saves` 目录。

本对话指定同步位置：`D:\\MC\\.minecraft\\versions\\26.2-Fabric 0.19.5\\saves`。
正确关系是 `saves/NJTech_Jiangpu_26.2/level.dat`，不要把外层项目目录当成世界文件夹。

启动对应的 Java 26.2 实例 → 单人游戏 → **南京工业大学｜江浦校区 1.1:1**。
世界不依赖模组、材质包或额外数据包；本项目使用官方原版服务端验证，未运行 Fabric 客户端实测。

## 参观

- 南门外出生点：`{sx} {sy} {sz}`，朝向西北侧校园。
- 双击空格飞行；空格上升，Shift 下降；已开启命令。
- 创造模式、和平难度、晴天中午，停止昼夜和天气循环，关闭随机刻及生物生成。
- 中文路牌和「校园导览.png」标出主要地点。
- 推荐路线：**南门 → 厚学楼 → 明德楼 → 笃学楼 → 行健体育馆 → 逸夫图书馆 → 镜湖 → 同和楼 → 仁智楼 → 天宝阁**。

| 地点 | 传送命令 |
| --- | --- |
| 南门出生点 | `/tp @s {sx} {sy} {sz}` |
{chr(10).join(rows)}
| 校园上空 | `/tp @s 1300 240 1550 150 40` |

## 制作范围

- 世界覆盖 **2048 × 2560 方块**，**{m['chunks']:,} 个预制区块**、20 个区域文件。
- **{len(m['building_groups'])} 组建筑和场地**，含教学、科研、公寓、住宅、食堂与体育场地。
- **{len(m['landmarks'])} 个导览地标**、**{m['trees']:,} 棵景观树**。
- 地上非空气方块约 **{m['above_terrain_blocks']/10000:.1f} 万个**。

### 主要模型

- **逸夫图书馆**：长条组合体量、突出主立面的玻璃阅览空间、白色框架与立柱，内部设书架、阅览桌和六层可通行楼梯。
- **天宝阁（南工塔）**：底部基座、竖向塔身、上部观景层和坡顶；中央步行楼梯可进入上部。
- **仁智楼、同和楼**：多翼教学组团、连接通道和灰色坡屋顶。
- **厚学楼、笃学楼**：依据公开照片区别白色与米色外观，设教室、走廊和楼梯。
- **明德楼**：对称办公楼与红色屋顶的小塔楼。
- **行健体育馆及游泳馆**：弧形屋顶、玻璃外墙、室内球场、看台、泳池与分道线。
- **亚青村、象山苑、檀香苑、北苑、东苑、西苑、南苑、景星苑、学府苑**：依导览图分组放置公寓与住宅，并补充食堂及运动设施。
- **镜湖、同济湖、北部湖区、行知湖**：水系、沿岸步道、观景平台及山地园林。
- **崇德楼、尚德楼、弘毅楼、笃行楼、沉毅楼、科研中心等**：以导览图的位置与体量为依据补充。

## 还原精度说明

这是以公开校园地图和建筑照片为依据的**近似复原**，不是测绘模型。
主布局使用学校 2023 年学业指南第 75 页（PDF 第 79 页）的导览图；较新的考点资料辅助核对厚学楼、笃学楼。
外观参考包括学校设计院、档案馆、英文官网以及校园航拍文章。公开照片的年份不一，不能据此保证包含 2026 年全部新增或改建内容。

整体比例约 1.1 方块对应 1 米，但示意地图本身不提供统一精确比例。
部分建筑体量、朝向、间距及地形高差已按游戏尺度调整，以避免楼栋相互覆盖。
地形保留主要山地与湖区关系，高程为设计补全。普通住宅、公寓和部分学科楼采用相应类型的简化外观；公寓和住宅组团的数字是模型管理编号，不作为现实楼号对照。
室内、楼梯、门洞、庭院和部分景观属于游览用途的补全设计，没有逐间复刻实际空间。

## 验证结果

- 全部方块名称、状态属性已核对官方 26.2 注册表。
- 独立读取区域文件，比对 **{r['nbt_round_trip']['decoded_block_states_compared']:,} 个方块状态**，结果通过。
- 官方 Java 26.2 服务端逐批加载全部 **{m['chunks']:,} 个预制区块**，核对全部导览地标，计算并保存所有预制区块的光照。
- 图书馆、天宝阁、仁智楼、厚学楼、笃学楼、明德楼、体育馆和一栋宿舍通过两格高玩家的入口与楼层通行检查；模型与旋转落位后的世界均检查。
- 官方服务端正常保存并关闭，无世界加载错误。
- 未进行桌面游戏客户端画面实测。预览图由实际方块数据渲染，玻璃和树叶采用简化颜色显示，**不是客户端截图**。
- 完整记录见 `validation_report.json`。

## 参考资料

1. [学校学业指南：江浦校区功能导览图，第 75 页](https://jwc.njtech.edu.cn/xyzn.pdf)
2. [学校研究生院：2026 年硕士研究生招生考试考点说明及建筑照片](https://gra.njtech.edu.cn/zsw/info/1021/1605.htm)
3. [学校建筑设计研究院：江浦校区图书馆](https://ngsj.njtech.edu.cn/info/1067/1947.htm)
4. [学校档案馆：2004 年鉴彩页，仁智楼、同和楼与天宝阁](https://dag.njtech.edu.cn/info/1060/1422.htm)
5. [学校英文官网：体育设施](https://en.njtech.edu.cn/index/Arts___Athletics/Athletics/Stadium.htm)
6. [南京工业大学发布的校园航拍文章：在南工大，起飞！](https://www.thepaper.cn/newsDetail_forward_18898064)
7. [明德楼辅助外观照片](https://www.meet99.com/jingdian-nanjinggongda-31590.html)

官方 Java 26.2 服务端 SHA-1：`823e2250d24b3ddac457a60c92a6a941943fcd6a`。
'''
    (ROOT/'使用说明.md').write_text(readme,encoding='utf-8');shutil.copyfile(ROOT/'使用说明.md',WORLD/'校园说明.md')
    extras=['使用说明.md','校园导览.png','校园鸟瞰.png','逸夫图书馆与镜湖.png','天宝阁与仁智楼.png','南门与教学区.png','行健体育馆与田径场.png','validation_report.json']
    target=ROOT/'南京工业大学_江浦校区_Java26.2.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(WORLD.rglob('*')):
            if p.is_file() and p.name not in {'session.lock','level.dat_old','.DS_Store'}:z.write(p,p.relative_to(ROOT).as_posix())
        for name in extras:z.write(ROOT/name,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert WORLD.name+'/level.dat' in z.namelist();count=len(z.namelist())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'SHA256.txt').write_text(digest+'  '+target.name+'\n',encoding='utf-8')
    out={'archive':str(target),'bytes':target.stat().st_size,'files':count,'sha256':digest,'world':str(WORLD),'validated':True}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
