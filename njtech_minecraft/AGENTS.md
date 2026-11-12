# 南京工业大学江浦校区

- 用户指定江浦校区，Minecraft Java 26.2 原版，比例在 1:1 至 2.5:1 内。本项目按约 1.1:1 制作，校园导览图为示意图，局部位置与体量调整记录在 `tools/layout-adjustments.json`。
- 主布局参考 `research/official-guide.pdf` 第 79 页（印刷页码 75）。`research/map-reference.png` 使用 1344 × 1824 坐标系；来源链接记录在 `使用说明.md`。
- 世界为 `NJTech_Jiangpu_26.2`；生成代码 `tools/build_njtech.py`，导出器 `tools/exporter.py`，预览 `tools/render.py`，验证 `tools/validate.py`，打包 `tools/deliver.py`。
- 通过脚本的 `__file__` 推导工程根目录。保持本目录与 `ccucm_minecraft` 同级，使用后者的官方 26.2 服务端、Java 25 及注册表。
- `tools/prepare_engine.py` 只用于初始化，会覆盖部分当前工具，不要在已有工程中重复运行。初始化后的导出器、渲染器等已有本项目改动。
- 方块数组 local y=0 对应 Minecraft y=64；世界 2048 × 2560，数组高 160；共 20480 个预制区块。版本 DataVersion 4903。
- 模型落位使用整数模板中心；奇数尺寸在正北或正东方向落位时，不要重新引入 `.5` 中心和银行家舍入，它会跳过单格宽的楼梯或柱列。
- 验证顺序包括独立 NBT 比对、模板及实际落位世界的两格高通行检查、官方服务端逐区加载与光照保存。服务端仅绑定 localhost:25589，`pause-when-empty-seconds=-1`。
- `validation_report.json` 所有项目通过后再打包，并按父级 AGENTS.md 的约定同步游戏世界文件夹到指定 saves。图片来自方块渲染，不可称为客户端截图。
