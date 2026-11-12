# CRP 项目交接

最后整理：2026-11-12。对话原文见 [conversation.md](conversation.md)，机器可读版见 [conversation.json](conversation.json)。

## 用户约定

- 项目名称：Campus Reconstruction Project（CRP），中文“校园复原工程”。
- 目标为 Minecraft Java 26.2 原版、可直接打开的世界存档。
- 比例范围 1:1 至 2.5:1，可合理微调建筑比例和朝向；各项目必须记录估算与设计补全。
- 实际本地工程根目录：`D:/gpt/edu/Campus Reconstruction Project`。早期对话中的 `D:/gpt/outputs` 与 `D:/gpt/Campus Reconstruction Project` 是迁移前路径。
- 用户指定：制作与验证完成后，将游戏世界文件夹同步到 `D:/MC/.minecraft/versions/26.2-Fabric 0.19.5/saves`；源码、研究资料与 ZIP 留在项目目录。更新前保护玩家改动，保留可恢复备份。

## 已交付成果

下表于本次交接时核对了本地 build_manifest.json 和 delivery_manifest.json。世界与 ZIP 仍位于本地，未作为本次对话备份上传。

| 学校及校区 | 本地子目录 | 游戏世界 | 创作区块数 |
| --- | --- | --- | --- |
| 长春中医药大学净月校区 | ccucm_minecraft | CCUCM_Jingyue_26.2 | 4032 |
| 匹兹堡大学奥克兰主校区 | pitt_minecraft | Pitt_Oakland_26.2 | 8960 |
| 西北工业大学长安校区 | nwpu_minecraft | NWPU_Changan_26.2 | 15360 |
| 南京工业大学江浦校区 | njtech_minecraft | NJTech_Jiangpu_26.2 | 20480 |
| 西北工业大学长安校区重制版 | nwpu_rebuild | NWPU_Changan_Rebuild_26.2 | 15360 |

## 最近完成的西工大重制

- 日期：2026-09-24。约 1.1:1，1536×2560 方块，79 组建筑与场地、44 个导览地标。
- 重点修改图书馆、启翔楼、体育馆、东门、类型化普通楼栋，以及室外铺装连接。
- 79 组场地外侧入口通过铺装连通检查；指定重点建筑通过模板与世界落位后的楼层通行检查。
- 官方 Java 26.2 服务端加载并保存全部 15360 个预制区块；最终回读比较 503316480 个创作范围内方块状态。
- 普通外观、未知室内、部分高差为估计或设计补全。客户端画面、夜景和性能未测试，不能把服务端通过称作客户端实测通过。
- 独立重制世界已同步到指定 saves，旧版保留。
- 压缩包：`西北工业大学_长安校区_重制版_Java26.2.zip`。
- 压缩包 SHA-256：`c17c221b8d2f7a5579536f4b2cb17c667cdeb82e8a3e00bd34afbc04bfd48b35`。

## 技能与生成工具

- 已将 `minecraft-campus-rebuild` 整理为“Minecraft 高校校园复原”通用技能；当时通过格式检查及 21 项工具测试。
- 技能约定：先核实校区/版本/比例、冻结坐标、区分来源与估计，先验证代表建筑，检查最终文件与实际通路，按范围交付。
- 此技能包含组件合并、差分、文件审计和项目账本工具，不是自带任意校园模型的完整自动生成引擎。
- 之前位于 Downloads 的技能目录现已无法找到；可检查本地 `D:/gpt/skill-work` 中的整理副本和 ZIP。本次没有上传技能文件。
- 各学校工程有 tools、research、验证报告、预览、世界与交付 ZIP。共享 Java 25、官方 26.2 服务端及注册表原位于 ccucm_minecraft/tools；这些是本地依赖，本次未上传。
- 重制版入口：nwpu_rebuild/tools/build_rebuild.py、validate.py、render.py、release.py。初始化脚本 prepare.py 会覆盖已改工具，已有工程不要重复运行初始化。
- 根目录 sync_world.ps1 用于同步经过验证的世界。

## 继续处理时

先取得所需本地文件或将其另行上传，再核对相应项目 AGENTS.md、正式清单、坐标版本、报告摘要和安装记录。不要把本仓库中的文字记录当作已经存在于云端的存档、源码或技能；不要凭历史 PASS 宣称改动后的新文件已验证。
