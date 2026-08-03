"""Answer-key isolation.

The assignment's non-negotiable rule (Section 7 / Section 12 "Automatic hard
failure"): if the runner can access restricted/ or an answer-key field
appears in the request payload sent to the model, the run must stop before
any model call and record an isolation failure.

This module gives that rule two independent layers of enforcement:

1. `read_allowlisted()` -- every runner code path that reads a case file MUST
   go through this function. It resolves the path and rejects anything
   outside RUNNER_READABLE_ROOTS (paths.py), including anything under
   restricted/.

2. `RestrictedAccessGuard` -- a context manager that monkeypatches
   `builtins.open`, `io.open`, and `pathlib.Path.open` for the duration of a
   `with` block, raising IsolationViolation the instant ANY code (runner
   code, a library, a future contributor's shortcut) touches a path under
   restricted/. Wrap the entire "build prompt -> call model" sequence in this
   guard in runner.py.

Layer 2 exists because layer 1 only protects call sites that remember to use
it. A one-week trial harness cannot afford OS-level process sandboxing, so
this is the documented, testable substitute -- see README "Known
limitations" for what real production hardening would add (separate OS
user/container, no shared filesystem access at all).
"""
from __future__ import annotations

import builtins
import io
import pathlib
from contextlib import contextmanager
from pathlib import Path

from rebelan_eval.paths import RESTRICTED_DIR, RUNNER_READABLE_ROOTS


class IsolationViolation(RuntimeError):
    """Raised the instant the runner process attempts to read a restricted path."""


def _is_allowlisted(path: Path) -> bool:
    resolved = path.resolve()
    return any(
        resolved == root.resolve() or root.resolve() in resolved.parents
        for root in RUNNER_READABLE_ROOTS
    )


def _is_restricted(path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    restricted_root = RESTRICTED_DIR.resolve()
    return resolved == restricted_root or restricted_root in resolved.parents


def read_allowlisted(path: Path) -> str:
    """Read a text file, raising IsolationViolation if it is not under an
    allowlisted runner-readable root (paths.RUNNER_READABLE_ROOTS)."""
    path = Path(path)
    if not _is_allowlisted(path):
        raise IsolationViolation(
            f"Refusing to read '{path}': not under an allowlisted runner-readable "
            f"root. Allowlisted roots: {[str(r) for r in RUNNER_READABLE_ROOTS]}"
        )
    return path.read_text(encoding="utf-8")


@contextmanager
def RestrictedAccessGuard():
    """Block any file open under restricted/ for the duration of the block.

    Usage:
        with RestrictedAccessGuard():
            packet = read_allowlisted(case_path)
            response = model.generate(prompt)
    """
    real_builtin_open = builtins.open
    real_io_open = io.open
    real_path_open = pathlib.Path.open

    def _check(path_like) -> None:
        try:
            p = Path(path_like)
        except TypeError:
            return
        if _is_restricted(p):
            raise IsolationViolation(
                f"Isolation guard blocked an attempt to open a restricted path: {p}"
            )

    def guarded_builtin_open(file, *args, **kwargs):
        _check(file)
        return real_builtin_open(file, *args, **kwargs)

    def guarded_io_open(file, *args, **kwargs):
        _check(file)
        return real_io_open(file, *args, **kwargs)

    def guarded_path_open(self, *args, **kwargs):
        _check(self)
        return real_path_open(self, *args, **kwargs)

    builtins.open = guarded_builtin_open
    io.open = guarded_io_open
    pathlib.Path.open = guarded_path_open
    try:
        yield
    finally:
        builtins.open = real_builtin_open
        io.open = real_io_open
        pathlib.Path.open = real_path_open
