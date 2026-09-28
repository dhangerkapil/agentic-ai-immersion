"""Vendor the shared code into hosted/ before azd packages this folder (Lab 2).

Runs on: the learner workstation. azd ships only the folder that holds main.py, so common/ and data/ are
copied here. Paths are chosen so the copied code's own path arithmetic keeps working without edits:
  common/benefits_data.py resolves data/ as Path(__file__).parents[1] / "data"   -> hosted/data
  main.py inserts hosted/ into sys.path last, so hosted/common wins over the checkout's common/ in the container.

    python prepare.py            copy (idempotent)
    python prepare.py --clean    remove the copies again
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                          # foundry-hosted-agents-labs/
SOURCES = {"common": ROOT / "common", "data": ROOT / "data"}
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".session_store_selftest")


def vendor() -> list[str]:
    copied = []
    for name, source in SOURCES.items():
        if not source.exists():
            raise SystemExit(f"[hosted] missing {source}; run from a full checkout of foundry-hosted-agents-labs")
        target = HERE / name
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=IGNORE)
        count = sum(1 for item in target.rglob("*") if item.is_file())
        print(f"[hosted] vendored {name}/ ({count} files)")
        copied.append(name)
    (HERE / ".vendored").write_text("created by prepare.py; safe to delete with --clean\n", encoding="utf-8")
    return copied


def clean() -> None:
    for name in SOURCES:
        target = HERE / name
        if target.exists():
            shutil.rmtree(target)
            print(f"[hosted] removed {name}/")
    marker = HERE / ".vendored"
    if marker.exists():
        marker.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    clean() if args.clean else vendor()
