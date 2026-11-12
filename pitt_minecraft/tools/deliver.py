"""Package the verified vanilla world, guide and actual-block previews."""
from pathlib import Path
import json,zipfile,hashlib,shutil
import nbt
ROOT=Path(__file__).resolve().parent.parent
WORLD=ROOT/'Pitt_Oakland_26.2'

def main():
    import validate
    report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
    assert report['official_server']['result']=='PASS'
    assert report['official_server']['authored_chunks_with_saved_lighting']==8960
    assert all(x['result']=='PASS' for x in report['walking_routes'])
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    data=nbt.plain(nbt.C(nbt.load(WORLD/'level.dat')))['Data']
    assert data['DataVersion']==4903 and data['GameType']==1 and data['allowCommands']==1
    assert data['spawn']['pos']==m['spawn']
    rules=nbt.plain(nbt.C(nbt.load(WORLD/'data/minecraft/game_rules.dat')))
    assert rules['data']['minecraft:advance_time']==0
    route_rows=[]
    for c in report['walking_routes']:
        if 'arrival' in c:route_rows.append('| '+c['building']+' | `/tp @s '+' '.join(map(str,c['arrival']))+'` |')
    readme=f'''# 匹兹堡大学 · 奥克兰主校区

Minecraft Java 版 **26.2 原版**校园存档 · 约 **1.1:1**

## 打开存档

1. 解压「匹兹堡大学_奥克兰校区_Java26.2.zip」。
2. 把其中的 **Pitt_Oakland_26.2** 文件夹放入你所使用的 **26.2 游戏目录的 saves 文件夹**。
3. 打开 Java 版 26.2 → 单人游戏 →「匹兹堡大学｜Oakland 1.1:1」。

目录关系应当是 `saves/Pitt_Oakland_26.2/level.dat`，同级还有 `dimensions`、`data` 和 `icon.png`。
官方启动器默认存档目录通常为 `%APPDATA%\\.minecraft\\saves`。
开启版本隔离的启动器，请使用 **26.2 实例自己的游戏目录**。

无需模组、材质包或数据包。此包是 Java 版世界，不适用于基岩版。
建议从 16 区块视距开始，按电脑性能调整。首次进入请等待附近建筑加载。

## 进入游戏后

- 创造模式，晴天中午，已开启命令。
- 出生点在 Schenley Plaza（申利广场）：`1350 69 648`，面向学习大教堂方向。
- 双击空格开始飞行；空格上升，Shift 下降。
- 地标附近设有中英文路牌。

建议路线：申利广场 → 学习大教堂与 Commons 公共大厅 → 观景层 →
Heinz Memorial Chapel → William Pitt Union → Litchfield Towers →
Hillman Library → Frick Fine Arts 与喷泉 → 上坡到 Petersen Events Center。

| 地点 | 传送命令 |
|---|---|
| 申利广场 / 出生点 | `/tp @s 1350 69 648` |
{chr(10).join(route_rows)}
| 校园上空 | `/tp @s 1200 275 950 170 35` |

## 还原范围

建造范围 **1792 × 1280 方块**，共 **8960 个预制区块**、约 **{m['above_terrain_blocks']/10000:.1f} 万个地上非空气方块**。
比例约为 **1.1 方块对应现实 1 米**，位于此前要求的 1:1–2.5:1 范围内。
依据官方校园地图安排街道、建筑位置及上校区坡地；个别间距、尺度与朝向作游戏适配。

### 重点建筑

- **Cathedral of Learning 学习大教堂**：约 180 格高的哥特式塔楼，逐级收分的塔身、竖向石肋、尖拱窗、顶部小尖塔；可进入的 Commons 大厅、拱肋、桌椅、设计补全的教室区域，以及可步行登上的观景层。
- **Heinz Memorial Chapel 亨氏纪念礼拜堂**：坡屋顶、中央尖塔、彩色玻璃、长椅与前部讲坛。
- **Litchfield Towers**：三座不同高度的圆柱形学生宿舍塔与公共基座。
- **William Pitt Union**：原 Schenley 酒店的砖石立面、檐口和拱形窗；大堂与多层室内空间。
- **Hillman Library**：混凝土体量、阅览区、玻璃入口，外形参考 2025 年改造资料。
- **Petersen Events Center**：体育馆弧形屋顶、玻璃立面、篮球场和蓝金色看台。
- **Frick Fine Arts**：红色屋顶、中庭回廊、圆顶和前方喷泉。
- 教学、宿舍和医学楼群：Alumni Hall、Posvar Hall、Stephen Foster Memorial、Benedum Hall、Chevron Science Center、Sutherland Hall、Panther Hall、Irvis Hall、Salk Hall、Scaife Hall、Biomedical Science Towers、Sennott Square、Barco Law Building、Mervis Hall、Bellefield Hall。

共 26 处单独布置的重点建筑（包含周边地标）、73 栋根据地图轮廓生成的配景建筑，另有申利广场、喷泉、旋转木马、道路、树木、路灯与蓝金色校色装饰。
Soldiers & Sailors、Carnegie Museum & Library、Mellon Institute 作为**相邻街区地标**加入，不表示它们都属于匹兹堡大学。

## 精度与资料边界

本作品是**公开资料参考还原版**。布局取自官方校园地图，重点建筑外形参考官方照片；不是测绘级模型。
官方地图标注修订日期为 2018 年 12 月，部分建筑照片及 Hillman 改造资料来自 2025 年，未覆盖 2026 年所有建设变化。
坡地高差是游戏中的近似处理。未公开的室内、普通配景建筑和部分立面细节为设计补全；没有声称逐间复刻教室、宿舍或所有真实楼层。
楼梯、入口宽度、建筑体量和少量相对位置作了便于玩家参观的调整。

## 验证结果

- 所有方块名称及属性均核对官方 26.2 方块注册表。
- 独立解码 12 个区域文件、8960 个区块，比对 **477,102,080** 个上部方块状态，结果一致。
- 用**官方 Java 26.2 服务端**逐一确认 8960 个预制区块成功加载，核对 27 处地标方块。
- 全部预制区块完成服务端光照计算并保存，正常关闭；无世界加载错误。
- 对学习大教堂、礼拜堂、学生中心、图书馆和体育馆进行两格高玩家通行检查；同时检查原建筑模型及其旋转后在世界中的入口、室内与指定楼层。
- 本环境完成了服务端验证和离线渲染，未进行桌面游戏客户端画面实测。
- 完整结果见 `validation_report.json`。

包内预览图直接由实际方块数据渲染，**不是游戏截图**；「公共大厅剖面」为了展示室内隐去了上部结构。

## 参考资料

1. [匹兹堡大学官方校园地图](https://www.pc.pitt.edu/sites/default/files/Campus_Map.pdf)
2. [Cathedral of Learning 官方导览](https://www.tour.pitt.edu/tour/cathedral-learning)
3. [Cathedral Commons Room 官方导览](https://www.tour.pitt.edu/tour/cathedral-commons-room)
4. [Heinz Memorial Chapel 官方导览](https://www.tour.pitt.edu/tour/heinz-memorial-chapel)
5. [Litchfield Towers 官方导览](https://www.tour.pitt.edu/tour/litchfield-towers)
6. [William Pitt Union 官方导览](https://www.tour.pitt.edu/tour/william-pitt-union)
7. [Petersen Events Center 官方导览](https://www.tour.pitt.edu/tour/petersen-events-center)
8. [Frick Fine Arts 官方导览](https://www.tour.pitt.edu/tour/frick-fine-arts-building)
9. [Hillman Library 2025 年改造](https://www.sustainable.pitt.edu/initiatives/buildings/leed-certified-buildings/hillman-library)
10. [Pittwire：Hillman 重新开放](https://www.pittwire.pitt.edu/features-articles/2025/09/04/hillman-library-renovation-open-house)
11. [Minecraft Java 26.2 官方说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
12. [Minecraft Java 26.1 官方存档目录变更说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)

验证使用的 Mojang 官方 26.2 服务端 SHA-1：
`823e2250d24b3ddac457a60c92a6a941943fcd6a`。
'''
    (ROOT/'使用说明.md').write_text(readme,encoding='utf-8')
    shutil.copyfile(ROOT/'使用说明.md',WORLD/'校园说明.md')
    target=ROOT/'匹兹堡大学_奥克兰校区_Java26.2.zip'
    extras=['使用说明.md','校园导览.png','校园鸟瞰.png','学习大教堂与礼拜堂.png','学生中心与三塔.png','公共大厅剖面.png','validation_report.json']
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(WORLD.rglob('*')):
            if file.is_file() and file.name not in {'session.lock','level.dat_old','.DS_Store'}:z.write(file,str(file.relative_to(ROOT)))
        for name in extras:z.write(ROOT/name,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert 'Pitt_Oakland_26.2/level.dat' in z.namelist()
        assert any('/dimensions/minecraft/overworld/region/' in n for n in z.namelist())
        files=len(z.namelist())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'SHA256.txt').write_text(digest+'  '+target.name+'\n',encoding='utf-8')
    result={'archive':str(target),'bytes':target.stat().st_size,'files':files,'sha256':digest,'world':str(WORLD),'validated':True}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
