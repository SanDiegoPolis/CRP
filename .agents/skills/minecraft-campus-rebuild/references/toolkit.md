# 可移植工具与状态记录

## 环境与范围

以下命令在技能目录执行，或把脚本替换成技能内绝对路径。使用已有合适环境，或在项目自己的虚拟环境安装 `scripts/requirements.txt`；不依赖任何学校的目录。需要 Python 3.10+；文件审计与状态记录只用标准库，构件读写需要 NumPy 和 nbtlib。JSON 按 UTF-8 写出，并兼容带 BOM 的 UTF-8 输入。

```bash
python3 -m venv /absolute/path/to/project/.venv
/absolute/path/to/project/.venv/bin/python -m pip install -r scripts/requirements.txt
```

Windows PowerShell 的虚拟环境解释器通常为 `<项目目录>/.venv/Scripts/python.exe`。路径有空格时引用路径并用 `&` 调用，例如 `& '<项目目录>/.venv/Scripts/python.exe' '<技能目录>/scripts/campus_build.py' inspect '<发布目录>'`。下方多行命令按 shell 改写为单行或使用对应续行方式，不把 POSIX 的反斜杠续行直接复制进 PowerShell。

组合工具仅支持 **Sponge v2 方块原理图**，不转存实体、方块实体或生物群系；遇到这些数据会停止。DataVersion 必须一致；它不会替你转换游戏版本、输出 Anvil 世界或证明游戏可加载。格式依据 [Sponge v2 specification](https://github.com/SpongePowered/Schematic-Specification/blob/master/versions/schematic-2.md)。

## 输入与完整原理图

输入目录含 manifest.json 和构件，最小清单：

```json
{"coordinate_version":"campus-map-v1","files":[
  {"file":"buildings/main.schem","sha256":"实际文件的64位SHA256",
   "offset_xyz":[-100,0,20],"size_xyz":[40,25,30],"non_air_blocks":1200}
]}
```

示例数值只是字段说明，必须从实际原理图读取。路径相对清单目录，禁止越界；清单内路径统一用 `/`。尺寸顺序 XYZ，数组顺序 YZX；Offset 是模型坐标，不擅自加其他项目的游戏高度。没有坐标版本的历史清单，需要先核实并明确命名，不能凭工具参数完成坐标校准；导出工具会拒绝缺失或不一致的坐标版本。

```bash
python scripts/campus_build.py inspect /absolute/path/to/release
python scripts/campus_build.py export /absolute/path/to/release \
  --coordinate-version campus-map-v1 --output /absolute/path/to/new-export
```

先估算包含空气的长方体体积；默认最多 5 亿格，单轴最多 65535。磁盘映射使用约 2 字节/格，另需输出及临时空间。**回读仍会将原理图解压到内存**，须额外预留数倍于体积的内存；磁盘映射不代表全流程恒定内存。大范围优先按可独立导入的区域拆分。提高 `--max-voxels` 前评估设备与导入工具容量。

输出包含 campus-complete.schem、manifest.json、build-validation.json、placement.json。拒绝覆盖已有目录；原组件只读。任意非空气构件重叠会停止，需要先明确资产归属、修正构件边界，不能依赖清单顺序覆盖。

`--anchor X Y Z` 指定模型中的粘贴锚点，默认模型原点。输出 Offset = 模型最小角 − 锚点；先在空测试区核实客户端的粘贴坐标语义，再导入正式世界。原理图内有空气，但忽略空气的粘贴模式不会清除旧世界方块。此工具没有处理客户端专用粘贴元数据。

## 可核验差分

补丁为 NPZ 加 JSON 描述，使用 `--patch /path/patch.json`，可以重复多次。NPZ 必须含：

- xyz：N×3 整数坐标，位于基准模型坐标系；同一补丁内不重复。
- palette：字符串数组，完整 Minecraft 方块状态。
- before、after：长度 N 的整数数组，索引对应 palette；删除明确写为 minecraft:air。

描述字段：`npz`（相对路径）、`sha256`（NPZ 摘要）、`baseline_manifest_sha256`（冻结清单摘要）、`coordinate_version`。所有补丁针对同一未修改基准逐点验证 before；相同修改去重，不同修改冲突即停。连续依赖的补丁应先产出新的基准，再生成下一轮差分。补丁作者还须记录建筑归属与依据；坐标和方块一致不能替代所有权审核。

## 项目状态账本

账本放在交付目录之外；它本身不能包含在被追踪的目录内。以下命令中的名称由项目决定，建议分别挂接 candidate、release、world、installed，不能只记录一个“最新”。

```bash
python scripts/project_state.py init /project/project-state.json \
  --project campus --coordinate-version campus-map-v1 --scope exterior
python scripts/project_state.py attach /project/project-state.json \
  --name release --path /project/output/release
python scripts/project_state.py record /project/project-state.json \
  --name file-readback --kind files --status pass --artifact release \
  --report /project/reports/readback.json
python scripts/project_state.py status /project/project-state.json
```

记录验证不会执行验证。kind 为 files、geometry、routes、visual、game；结果可为 pass、partial、fail、not-run。报告必须真实存在，记录前先检查内容与测试对象。CURRENT 只说明登记的报告和资产未变；它不为报告结论背书。修改资产或报告后，旧检查会显示 STALE；重新挂接新版本不会抹除旧检查，须重新验收后再登记。

账本使用相对路径，可随完整项目迁移；目录快照包含全部文件，游戏运行后存档变化也会使记录失效，这是预期行为。不要把缓存、账本或不断变动的日志放入发布资产目录。大世界完整摘要扫描需要时间。

backlog 可编辑为对象列表，每项记录 `id`、`blocking`、`impact`（项目内一致的整数尺度）、`evidence_gap`、`next_action`、`completion_evidence`。状态工具先列阻塞项，再按影响排序；由执行者根据证据选下一步，不用虚构百分比取代完成条件。

## 文件检查与回归

manifest 可声明 `validation_reports`：每项有 file、sha256、kind。审计器核对报告身份并显示其自报状态。历史清单未声明报告时显示缺口，原报告需另行查看。`--zip` 仅验证结构/CRC，不证明压缩包与发布目录逐文件相同；安装和打包仍需单独核对实际文件清单及摘要。

`--world <世界目录>` 识别传统 `region`、`DIM-1/region`、`DIM1/region` 与 `dimensions/<命名空间>/<维度>/region`，分别列出文件数。它不解析 NBT 或推断游戏版本；只有 `.mca` 文件存在不代表世界可运行。传统和新主世界目录并存会标出缺口；Bedrock 不在这个检查器的支持范围内。没有组件 manifest 的历史工程不必为查询进度强行迁移到此格式。

```bash
python scripts/audit_release.py /project/output/release
python scripts/audit_release.py /project/output/release --world /project/output/campus-world
python scripts/test_toolkit.py
```

测试使用临时小型构件，覆盖外部 NBT 输入、多字节材质索引、坐标、删除与补丁冲突、中文路径与 UTF-8、不同 Java 区块目录、文件身份和状态过期；不会修改正式校园，也不会启动 Minecraft。
