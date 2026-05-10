"""Worktree conftest: ensure the local worktree's privguard package takes precedence
over any editable-install finder registered from the main repository.

This is necessary when running pytest inside a git worktree: the system-wide
`__editable__.privguard-0.1.0.pth` installs a meta-path finder that redirects
``import privguard`` to the original editable-install source directory. That
finder is a MetaPathFinder and sits ahead of sys.path, so setting PYTHONPATH
alone is insufficient.

Solution: remove the editable-install finder from sys.meta_path for this
worktree session and insert the worktree root at the front of sys.path so that
plain filesystem imports pick up the local copy.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Worktree root is the directory containing this conftest.py.
_WORKTREE_ROOT = Path(__file__).parent.resolve()


def _remove_editable_finder_for_privguard() -> None:
    """Remove any meta-path finder that would redirect 'privguard' to a different path."""
    to_remove = []
    for finder in sys.meta_path:
        finder_type = type(finder).__name__
        # The setuptools editable install finder is named _EditableFinder and has
        # a MAPPING dict that maps package names to source directories.
        if hasattr(finder, "MAPPING") and "privguard" in getattr(finder, "MAPPING", {}):
            mapped_path = Path(finder.MAPPING["privguard"]).resolve()
            if mapped_path != _WORKTREE_ROOT / "privguard":
                to_remove.append(finder)
    for finder in to_remove:
        sys.meta_path.remove(finder)


def _invalidate_cached_privguard_imports() -> None:
    """Remove any already-cached privguard modules so re-import picks up the worktree copy."""
    to_delete = [key for key in sys.modules if key == "privguard" or key.startswith("privguard.")]
    for key in to_delete:
        del sys.modules[key]


# Execute immediately on conftest load (before any test collection).
_remove_editable_finder_for_privguard()

# Ensure worktree root is first in sys.path.
worktree_str = str(_WORKTREE_ROOT)
if worktree_str not in sys.path:
    sys.path.insert(0, worktree_str)
elif sys.path[0] != worktree_str:
    sys.path.remove(worktree_str)
    sys.path.insert(0, worktree_str)

_invalidate_cached_privguard_imports()
