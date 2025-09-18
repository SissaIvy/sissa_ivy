#!/usr/bin/env python3
"""
Normalize terminology across a repository.

Features:
- Atomic writes (safe even if interrupted)
- --check (CI-friendly), --dry-run (diffs), summary stats
- Include/exclude filters, optional concurrency
- Encoding resilience and optional newline normalization
"""

from __future__ import annotations

import argparse
import difflib
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, Optional

DEFAULT_EXTS = {".md", ".py"}
DEFAULT_EXCLUDE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
    "node_modules", "venv", ".venv", "build", "dist", ".eggs",
}

try:
    # You already have this — keeping the import explicit and failure-friendly.
    from terminology_normalizer import normalize  # type: ignore
except Exception as e:  # noqa: BLE001
    print(f"Failed to import 'terminology_normalizer.normalize': {e}", file=sys.stderr)
    sys.exit(2)


@dataclass
class FileResult:
    path: Path
    changed: bool
    error: Optional[str] = None


def iter_candidate_files(
    root: Path,
    exts: set[str],
    exclude_dirs: set[str],
    follow_symlinks: bool,
) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        # In-place prune directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for name in filenames:
            if Path(name).suffix.lower() in exts:
                yield Path(dirpath) / name


def read_text_resilient(path: Path, prefer_encoding: str = "utf-8") -> Tuple[str, str]:
    """
    Try a couple of encodings so one weird file doesn't crash the run.
    Returns (text, used_encoding).
    """
    candidates = [prefer_encoding, "utf-8-sig", "latin-1"]
    last_err: Optional[Exception] = None
    for enc in candidates:
        try:
            return path.read_text(encoding=enc), enc
        except UnicodeDecodeError as e:
            last_err = e
    # Final attempt with replacement to avoid hard failure
    try:
        raw = path.read_bytes()
        return raw.decode("utf-8", errors="replace"), "utf-8?replace"
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Could not decode {path} (last error: {last_err or e})") from e


def maybe_normalize_newlines(s: str) -> str:
    # Convert CRLF and CR to LF without touching content.
    return s.replace("\r\n", "\n").replace("\r", "\n")


def unified_diff_str(original: str, normalized: str, path: Path) -> str:
    diff_iter = difflib.unified_diff(
        original.splitlines(keepends=True),
        normalized.splitlines(keepends=True),
        fromfile=f"a/{path}",
        tofile=f"b/{path}",
        n=3,
        lineterm="",
    )
    return "".join(diff_iter)


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Write text atomically: write to a temp file in the same directory, then replace."""
    tmp_fd, tmp_name = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, "w", encoding=encoding, newline="") as tmp:
            tmp.write(text)
            tmp.flush()
            os.fsync(tmp.fileno())
        # Preserve executable bit if present
        try:
            mode = path.stat().st_mode
        except FileNotFoundError:
            mode = None
        if mode is not None:
            os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
    finally:
        # If something exploded before replace, ensure temp is gone.
        try:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)
        except Exception:
            pass


def process_file(
    path: Path,
    dry_run: bool = False,
    normalize_line_endings: bool = False,
    backup: bool = False,
    max_bytes: Optional[int] = None,
) -> FileResult:
    try:
        if max_bytes is not None and path.stat().st_size > max_bytes:
            return FileResult(path, changed=False, error=f"skipped (>{max_bytes} bytes)")
        original, used_enc = read_text_resilient(path)

        normalized = normalize(original)

        if normalize_line_endings:
            original_nl = maybe_normalize_newlines(original)
            normalized_nl = maybe_normalize_newlines(normalized)
        else:
            original_nl = original
            normalized_nl = normalized

        if original_nl == normalized_nl:
            return FileResult(path, changed=False)

        if dry_run:
            diff = unified_diff_str(original_nl, normalized_nl, path)
            # Deliberately print even for parallel runs; ordering isn't guaranteed.
            print(diff)
            return FileResult(path, changed=True)

        if backup and path.exists():
            backup_path = path.with_suffix(path.suffix + ".bak")
            try:
                # copy2 preserves timestamps and mode
                import shutil
                shutil.copy2(path, backup_path)
            except Exception as e:  # noqa: BLE001
                return FileResult(path, changed=False, error=f"backup failed: {e}")

        # Write atomically (prefer the encoding we successfully read with)
        write_enc = used_enc.split("?")[0] if "?" in used_enc else used_enc
        atomic_write_text(path, normalized_nl, encoding=write_enc)
        print(f"Updated: {path}")
        return FileResult(path, changed=True)

    except Exception as e:  # noqa: BLE001
        return FileResult(path, changed=False, error=str(e))


def run(
    directory: Path,
    dry_run: bool,
    check: bool,
    exts: set[str],
    exclude_dirs: set[str],
    follow_symlinks: bool,
    normalize_line_endings: bool,
    backup: bool,
    max_bytes: Optional[int],
    workers: int,
) -> int:
    files = list(iter_candidate_files(directory, exts, exclude_dirs, follow_symlinks))

    changed = 0
    errors = 0

    if workers and workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    process_file,
                    path,
                    dry_run,
                    normalize_line_endings,
                    backup,
                    max_bytes,
                ): path
                for path in files
            }
            for fut in as_completed(futures):
                res = fut.result()
                if res.error:
                    errors += 1
                    print(f"Error: {res.path}: {res.error}", file=sys.stderr)
                elif res.changed:
                    changed += 1
    else:
        for path in files:
            res = process_file(
                path,
                dry_run=dry_run,
                normalize_line_endings=normalize_line_endings,
                backup=backup,
                max_bytes=max_bytes,
            )
            if res.error:
                errors += 1
                print(f"Error: {res.path}: {res.error}", file=sys.stderr)
            elif res.changed:
                changed += 1

    total = len(files)
    unchanged = total - changed - errors
    print(
        f"\nScanned: {total} | Changed: {changed} | Unchanged: {unchanged} | Errors: {errors}"
    )

    # Exit codes: 0 OK/no changes, 1 would-change/changed in --check, 2 had errors
    if errors:
        return 2
    if check and changed:
        return 1
    return 0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Normalize terminology in text files (.md, .py by default).",
        epilog=(
            "Exit codes: 0 = OK/no changes, 1 = would change (with --check), 2 = error. "
            "Examples:\n"
            "  normalize_terminology.py . --check\n"
            "  normalize_terminology.py docs --ext .md --ext .txt -n\n"
            "  normalize_terminology.py src --backup --workers 4"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("directory", help="Directory to scan")
    p.add_argument(
        "-n","--dry-run",
        action="store_true",
        help="Show unified diffs without modifying files (shorthand -n)",
    )
    p.add_argument(
        "--check",
        action="store_true",
        help="Do not modify files; exit with code 1 if changes would be made",
    )
    p.add_argument(
        "--ext",
        dest="exts",
        action="append",
        help="File extension to include (repeatable). Example: --ext .md --ext .py",
    )
    p.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude (repeatable). Example: --exclude-dir node_modules",
    )
    p.add_argument(
        "--follow-symlinks",
        action="store_true",
        help="Follow directory symlinks while walking",
    )
    p.add_argument(
        "--normalize-line-endings",
        action="store_true",
        help="Normalize line endings to LF (\\n) before diff/compare/write",
    )
    p.add_argument(
        "--backup",
        action="store_true",
        help="Write a .bak file next to each changed file before updating it",
    )
    p.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="Skip files larger than this many bytes",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Process files in parallel with N worker threads (0 or 1 = disabled)",
    )
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    directory = Path(args.directory).resolve()

    if not directory.exists() or not directory.is_dir():
        print(f"Not a directory: {directory}", file=sys.stderr)
        sys.exit(2)

    # Normalize extensions: ensure dot prefix & lowercase
    raw_exts = args.exts or list(DEFAULT_EXTS)
    exts = { (e if e.startswith('.') else f'.{e}').lower() for e in raw_exts }
    exclude_dirs = DEFAULT_EXCLUDE_DIRS.union(set(args.exclude_dir or []))

    exit_code = run(
        directory=directory,
        dry_run=args.dry_run or args.check,  # check implies dry-run behavior
        check=args.check,
        exts=exts,
        exclude_dirs=exclude_dirs,
        follow_symlinks=bool(args.follow_symlinks),
        normalize_line_endings=bool(args.normalize_line_endings),
        backup=bool(args.backup),
        max_bytes=args.max_bytes,
        workers=max(0, int(args.workers)),
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
