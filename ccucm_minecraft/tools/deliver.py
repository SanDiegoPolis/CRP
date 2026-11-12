from pathlib import Path
import json,zipfile,hashlib,shutil
import nbt

ROOT=Path(__file__).resolve().parent.parent
WORLD=ROOT/'CCUCM_Jingyue_26.2'

def main():
    import validate
    validate.review_completed_run()
    report=json.loads((ROOT/'validation_report.json').read_text(encoding='utf-8'))
    assert report['official_server']['result']=='PASS'
    assert all(x['result']=='PASS' for x in report['walking_routes'])
    m=json.loads((ROOT/'build_manifest.json').read_text(encoding='utf-8'))
    data=nbt.plain(nbt.C(nbt.load(WORLD/'level.dat')))['Data']
    assert data['DataVersion']==4903 and data['GameType']==1 and data['allowCommands']==1
    assert data['spawn']['pos']==[370,65,800]
    rules=nbt.plain(nbt.C(nbt.load(WORLD/'data/minecraft/game_rules.dat')))
    assert rules['data']['minecraft:advance_time']==0
    readme='''# 长春中医药大学 · 净月校区

Minecraft Java 版 26.2 原版校园存档 · 约 1.25:1

## 打开存档

1. 解压「长春中医药大学_净月校区_Java26.2.zip」。
2. 将里面的 **CCUCM_Jingyue_26.2** 文件夹复制到你所使用的 **26.2 游戏目录的 saves 文件夹**。
3. 打开 Java 版 26.2 → 单人游戏 → 选择「长春中医药大学｜净月校区 1.25:1」。

正确的目录关系：`saves/CCUCM_Jingyue_26.2/level.dat`。
同一文件夹还应包含 `dimensions`、`data` 和 `icon.png`。

官方启动器默认通常位于 `%APPDATA%\\.minecraft\\saves`；
如果启动器开启了版本隔离，请使用该启动器中 **26.2 实例的游戏目录**，再进入 `saves`。
首次加载附近建筑需要一点时间。建议视距 16–24 区块，按电脑性能调整。

## 进入后

- 创造模式，晴天中午，已开启命令。
- 出生点在南门：`370 65 800`，朝向校园。
- 双击空格飞行；按住空格上升，Shift 下降。
- 校园内有中文路牌，教学楼、图书馆、食堂及宿舍配有可进入的室内区域。
- 原版方块与原生存档；无需安装模组、材质包或数据包。

## 建议参观路线

南门校名石 → 校训石 → 九宫喷泉 → 致知楼 → 四象城图书馆 →
七星百草园 → 体育场 → 行德馆与八卦广场 → 格物楼 → 南门。

| 地点 | 传送命令 |
|---|---|
| 南门 | `/tp @s 370 65 800` |
| 四象城图书馆前 | `/tp @s 689 65 339` |
| 致知楼前 | `/tp @s 353 65 568` |
| 杏林餐厅 | `/tp @s 602 65 467` |
| 新公寓半夏居 | `/tp @s 370 65 220` |
| 八卦广场 | `/tp @s 700 65 645` |
| 体育场南侧 | `/tp @s 1005 65 581` |
| 全校俯瞰 | `/tp @s 580 260 700 180 55` |

## 还原内容和尺度

建造范围约 **1152 × 896 方块**，约 **223.7 万个地上非空气方块**，
共 **4032 个预制区块**。比例按约 **1.25 方块对应现实 1 米**安排。
包括：四象城图书馆、致知楼、行知楼、明德楼、仲景楼、时珍楼、启德馆、
格物楼、日新楼、行德馆、杏林餐厅、新公寓与六君子居、运动场地、
七星百草园、青龙河及伏羲桥、九宫喷泉、校训石与校门。

本作品依据公开导览图和建筑照片制作，**属于参考资料还原版，并非测绘级数字孪生**。
以已公开的校园建筑位置图为布局依据，建筑间距、局部体量及朝向作了游戏适配。
比例是估算值；照片无法确认的室内、北部配套建筑和景观细节进行了设计补全。
资料有不同年份，不能保证反映 2026 年每一处校园变化。

图书馆的高柱廊、明德楼玻璃圆塔、格物楼穹顶、教学楼红砖立面、
八卦广场和中医药主题园林作为重点识别特征保留。
植物使用原版作物作景观示意，不代表真实药材形态。

## 验证

- 版本：官方 Java 26.2；DataVersion 4903。
- 独立解码并比对 4032 个区块、99,090,432 个上部方块状态。
- 使用官方 26.2 服务端逐一确认全部 4032 个预制区块成功加载，并验证建筑方块。
- 已用官方服务端保存并重新计算光照/高度缓存。
- 致知楼、图书馆、半夏居和食堂的各层通过两格高玩家通行检查。
- 当前环境以官方服务端加载和离线方块渲染验证；未进行桌面客户端画面实测。
- 完整结果见 `validation_report.json`。

本包鸟瞰图由实际存档方块数据渲染，并非游戏客户端截图。

## 参考来源

1. [校园导览与楼宇实景照片（长春中医药大学招生/党委宣传部内容转载，2022）](https://www.sohu.com/a/585574429_121124211)
2. [汉语桥平台长春中医药大学介绍及净月校区规划总平面图（2023）](https://bridge.chinese.cn/online/camp/school/10347/article/592)
3. [长春中医药大学临床医学院官网，校门及明德楼外观参考](https://lcyxy.ccucm.edu.cn/index.htm)
4. [Minecraft Java 26.2 官方发布说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
5. [Minecraft Java 26.1 官方存档目录变更说明](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)

校园地理布局主要使用第 1 项导览图。第 2 项属于规划图，仅作为辅助参考。
官方服务端由 Mojang 版本清单下载，校验 SHA-1：
`823e2250d24b3ddac457a60c92a6a941943fcd6a`。
'''
    readme=readme.replace('223.7 万',f"{m['block_count_above_ground']/10000:.1f} 万")
    (ROOT/'使用说明.md').write_text(readme,encoding='utf-8')
    shutil.copyfile(ROOT/'使用说明.md',WORLD/'校园说明.md')
    target=ROOT/'长春中医药大学_净月校区_Java26.2.zip'
    exclude={'session.lock','level.dat_old','.DS_Store'}
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for file in sorted(WORLD.rglob('*')):
            if file.is_file() and file.name not in exclude:z.write(file,str(file.relative_to(ROOT)))
        for name in ['使用说明.md','校园导览.png','校园鸟瞰.png','图书馆与教学区.png','南门与八卦广场.png','validation_report.json']:
            z.write(ROOT/name,name)
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        assert 'CCUCM_Jingyue_26.2/level.dat' in z.namelist()
        assert any('/dimensions/minecraft/overworld/region/' in n for n in z.namelist())
        file_count=len(z.namelist())
    digest=hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT/'SHA256.txt').write_text(digest+'  '+target.name+'\n',encoding='utf-8')
    result={'archive':str(target),'bytes':target.stat().st_size,'files':file_count,'sha256':digest,'world':str(WORLD),'validated':True}
    (ROOT/'delivery_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
