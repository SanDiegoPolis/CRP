"""Fast local geometry navigation check before rebuilding all Anvil files."""
import build_pitt as b
import navigation
for spec in b.SPECS:
    if spec[6] in (b.cathedral,b.chapel,b.hillman,b.arena,b.union):b.place(spec)
m={'palette':b.PAL,'navigation_checks':b.CHECKS}
import json
print(json.dumps(navigation.navigability(None,m),ensure_ascii=False,indent=2))
