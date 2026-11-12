# Campus Reconstruction Project

Use this checkout as the project root. Read docs/HANDOFF.md and the requested campus's instructions before editing. Local Windows paths in historical documents are historical installation paths, not cloud workspace paths.

- Minecraft Java 26.2 vanilla; user permits scale from 1 to 2.5 blocks per metre and reasonable local adjustments.
- The reusable skill is `.agents/skills/minecraft-campus-rebuild/SKILL.md`.
- Five deliverables are checked in as ZIPs beside each project's sources. `assets/catalog.json` records SHA256. Run `python cloud.py restore all` to restore world folders, reference assets, template worlds, registry and NumPy caches.
- `python cloud.py build PROJECT`, `validate PROJECT`, and `render PROJECT` run existing generators. Read the project notes before using initialization/prepare scripts: several overwrite customized tools.
- Java 25 is required for official 26.2 server validation. Download that server using `python cloud.py server` when internet is available. It is not bundled with this source repository.
- Install a CJK font (e.g. fonts-noto-cjk on Debian/Ubuntu) or set CRP_FONT. Set CRP_JAVA if java is not on PATH.
- Terrain, ordinary facades and interiors include inferred design; do not claim measured accuracy. Runtime and file validation are distinct from actual client visual/performance testing.
- Existing reports describe the previous released worlds. Changes need affected checks and new final-world readback before publishing an updated save.
- The local-only Windows saves path in docs is not available in a cloud checkout. Do not try to synchronize there from a cloud task. Produce a reviewed world ZIP for download instead.
