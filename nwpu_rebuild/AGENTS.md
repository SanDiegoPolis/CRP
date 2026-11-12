# 西北工业大学长安校区重制版

- 本工程是用户指定用 `minecraft-campus-rebuild` 技能进行的独立重制。旧版在同级 `nwpu_minecraft`，不得用当前结果覆盖旧版制作文件或旧版安装世界。
- 当前世界名 `NWPU_Changan_Rebuild_26.2`，Java 26.2，DataVersion 4903，约 1.1:1，1536×2560，局部数组高128，对应世界Y64起。
- 工程参数和资料边界在 `planning/project-brief.md`；旧版摘要、坐标控制点在 `planning/baseline.json`；本版逐对象来源和置信度在 `planning/evidence.json`。
- `tools/base.py` 保存基础导出/布局逻辑，`tools/build_rebuild.py` 重建建筑与场地，实际修改应写入此脚本。`tools/prepare.py` 仅为首次初始化，会覆盖已改工具，不要重新运行。
- `tools/validate.py` 执行预导出数据对比、室内通路、官方服务端分批加载与光照保存、最终区域回读。`tools/finish_validation.py` 在服务端已经正常保存并通过后执行最终回读和室外铺装检查。
- 区域回读应区分已创作范围与运行时生成的外围区块；计数不能混淆。`tools/final_voxels.npy` 是最终区域文件独立解码的预览缓存，摘要绑定在 `planning/final-region-binding.json`。
- `tools/render.py` 正式预览只能读取最终缓存；`--preflight` 使用生成数组作制作期检查，不用于正式交付证据。
- `tools/check_exterior.py --final` 只证明出生点到场地外侧入口的地面铺装连通，不代表每间房间已检查。
- `tools/release.py` 在最终验证与视觉记录齐全后打包、逐条检查ZIP内容，保留原版哈希并生成发布manifest。实际客户端、夜景和性能尚未测试，不要将服务端通过写成客户端通过。
- 使用父目录 `sync_world.ps1 -Project nwpu_rebuild` 同步独立重制世界到用户既定saves。只有完成复制校验后，才能宣称安装成功。
