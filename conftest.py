"""Top-level pytest conftest.

The repo ships an empty `__init__.py` at the repo root (required by the
hackathon submission layout) and an empty `tests/__init__.py`. That combo
makes pytest walk up from the test file to find the package root, and
because BOTH the tests directory AND the repo root have `__init__.py`,
pytest keeps walking and ends up inserting `/Users/.../test/` (the repo's
parent) into `sys.path`. With the parent on sys.path, `import openenv`
finds `/repo-root/openenv/__init__.py` — the empty local package — which
has no `core` attribute and shadows the installed `openenv-core` package.

We fix this in three steps:
  1. Drop the poisoning sys.path entries (repo root + repo parent).
  2. Evict any `openenv.*` modules pytest's bootstrap already cached.
  3. Re-add the repo root so `server.*` and `models` stay importable, then
     eagerly `import openenv` so the resolution happens NOW with a clean
     sys.modules and a scrubbed sys.path. That import lands on the
     site-packages install, and every later `import openenv` reuses it.
"""

from __future__ import annotations

import os
import sys


_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_REPO_PARENT = os.path.dirname(_REPO_ROOT)


def _norm(p: str) -> str:
    try:
        return os.path.abspath(p)
    except Exception:
        return p


sys.path[:] = [p for p in sys.path if _norm(p) not in (_REPO_ROOT, _REPO_PARENT)]

for _mod in [m for m in list(sys.modules) if m == "openenv" or m.startswith("openenv.")]:
    del sys.modules[_mod]

if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Force resolution now, while sys.modules is clean and sys.path no longer
# contains the repo parent. The landed module (site-packages) then sticks
# in sys.modules for every later import.
import openenv  # noqa: F401,E402
