# Campus Reconstruction Project（CRP）

Minecraft Java 26.2 高校校园复原工程：生成源码、通用技能、已交付世界存档与项目对话。

| 项目 | 源码目录 | 游戏存档 |
| --- | --- | --- |
| 长春中医药大学净月校区 | [ccucm_minecraft](ccucm_minecraft/tools) | [ZIP](ccucm_minecraft/长春中医药大学_净月校区_Java26.2.zip) |
| 匹兹堡大学奥克兰校区 | [pitt_minecraft](pitt_minecraft/tools) | [ZIP](pitt_minecraft/匹兹堡大学_奥克兰校区_Java26.2.zip) |
| 西北工业大学长安校区 | [nwpu_minecraft](nwpu_minecraft/tools) | [ZIP](nwpu_minecraft/西北工业大学_长安校区_Java26.2.zip) |
| 南京工业大学江浦校区 | [njtech_minecraft](njtech_minecraft/tools) | [ZIP](njtech_minecraft/南京工业大学_江浦校区_Java26.2.zip) |
| 西北工业大学长安校区重制版 | [nwpu_rebuild](nwpu_rebuild/tools) | [ZIP](nwpu_rebuild/西北工业大学_长安校区_重制版_Java26.2.zip) |

下载游戏 ZIP，解压后将其中包含 level.dat 的世界文件夹放进对应 Java 26.2 实例的 saves 目录。

## 在云端继续制作

需要 Python 3.10+；官方服务端验证另需 Java 25。Linux 上准备中文字体，例如 Debian/Ubuntu 的 fonts-noto-cjk。大型校园生成和全量回读需要数 GB 内存及数 GB 磁盘空间。

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python cloud.py restore all
python cloud.py doctor
python cloud.py server
python cloud.py build nwpu_rebuild
python cloud.py validate nwpu_rebuild
python cloud.py render nwpu_rebuild
```

`restore` 逐文件校验摘要；若已有同名文件内容不同，会停止以保留工作。它会解压 NumPy 缓存、地图处理结果、参考图、26.2 模板和方块注册表。运行资料采用 [两个分卷](assets) 保存，脚本会自动合并为 cloud-data.zip 并检查分卷及合并结果的 SHA-256，再进行解压。已有源码可以直接接续，不要重新运行会覆盖自定义工具的 prepare/初始化脚本。

上传副本适配了 Windows/Linux 字体和 Java 路径；原始本地工程未被改写。现有世界的验证报告保留为历史依据，此次打包没有重新宣称做过 Linux 客户端实测。云端需要自行安装 Java/字体，并允许访问官方下载源，才能再次运行服务端验证。

## 技能与历史

- [通用高校复原技能](.agents/skills/minecraft-campus-rebuild/SKILL.md)
- [对话记录](docs/conversation.md) · [机器可读对话](docs/conversation.json)
- [项目交接](docs/HANDOFF.md)
- [上传文件与校验目录](assets/catalog.json)

源码和文档以每个项目当前目录为基准；历史交付清单中的机器路径由 restore 转为当前克隆目录。公开资料引用保留在各项目说明中。普通楼栋、未知室内与部分高差为估算或设计补全；外观准确性、文件回读与客户端体验分别记录。
