"""Admin package initializer.

When Django imports `community.admin` it will import this package `__init__`.
This file ensures two things:

- Import the package-scoped submodule `videos` (if present).
- Load the legacy top-level `community/admin.py` file (if it exists) by
  executing it under a safe module name so its admin registrations are
  preserved. This keeps backward compatibility with the repository layout
  where `community/admin.py` was used.

We avoid raising at import time and instead log warnings to stderr so
the admin app still loads even if one piece fails.
"""

import os
import sys
import importlib.util

# 1) Import package submodules (e.g. videos.py)
try:
    from . import videos  # noqa: F401
except Exception:
    sys.stderr.write('Warning: failed to import community.admin.videos\n')

# 2) Backwards-compat: if a top-level `community/admin.py` file exists (the
# module used before `community/admin/` became a package), load it by path
# under a non-conflicting module name so its registrations run.
try:
    pkg_dir = os.path.dirname(__file__)
    legacy_admin_path = os.path.abspath(os.path.join(pkg_dir, '..', 'admin.py'))
    if os.path.exists(legacy_admin_path):
        spec = importlib.util.spec_from_file_location('community._legacy_admin', legacy_admin_path)
        if spec and spec.loader:
            legacy_mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(legacy_mod)
            except Exception:
                sys.stderr.write('Warning: failed to execute legacy community/admin.py\n')
except Exception:
    # Be tolerant of any path/import issues at import time
    sys.stderr.write('Warning: error while attempting to load legacy admin module\n')
