#!/usr/bin/env python3
"""扫描源码中的禁用外部项目标识。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterator, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]

BANNED_TERMS: Tuple[str, ...] = ("maibot", "maibot-sdk", "maisaka")

# 仅 AGENTS.md 允许出现禁用词（大小写不敏感）
ALLOWED_FILE_NAMES = frozenset({"agents.md"})

DEFAULT_ROOTS: Tuple[str, ...] = (
    "provider_sdk",
    "tests",
    "README.md",
    "pyproject.toml",
    "AGENTS.md",
)

SKIP_PARTS = frozenset({".git", "__pycache__", ".pytest_cache", "dist", "build", ".eggs"})
SKIP_FILES = frozenset({"checkterms.py"})


def _is_allowed_file(path: Path) -> bool:
    return path.name.lower() in ALLOWED_FILE_NAMES


def _iter_files(roots: Sequence[str]) -> Iterator[Path]:
    for root_name in roots:
        base = ROOT / root_name
        if base.is_file():
            if not _is_allowed_file(base):
                yield base
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if _is_allowed_file(path):
                continue
            if path.suffix not in {".py", ".js", ".html", ".css", ".json", ".toml", ".md"}:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.name in SKIP_FILES:
                continue
            yield path


def _scan_file(path: Path, terms: tuple[str, ...]) -> list[tuple[Path, str, int, str]]:
    hits: list[tuple[Path, str, int, str]] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return hits
    lower = content.lower()
    for term in terms:
        if term not in lower:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if term not in line.lower():
                continue
            try:
                rel = path.relative_to(ROOT)
            except ValueError:
                rel = path
            hits.append((rel, term, lineno, line.strip()))
    return hits


def scan(roots: Sequence[str]) -> List[Tuple[Path, str, int, str]]:
    hits: List[Tuple[Path, str, int, str]] = []
    for path in sorted(_iter_files(roots)):
        hits.extend(_scan_file(path, BANNED_TERMS))
    return hits


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="检查禁用外部项目标识")
    parser.add_argument("--roots", nargs="*", default=list(DEFAULT_ROOTS))
    args = parser.parse_args(argv)
    hits = scan(args.roots)
    if not hits:
        print("OK: 未发现禁用标识")
        return 0
    print(f"ERROR: 发现 {len(hits)} 处禁用标识")
    for path, term, lineno, line in hits:
        print(f"  {path}:{lineno}: [{term}] {line[:120]}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
