"""Download the authors' problem instances into data/COSP_Flow_Shop.

Usage (from the project root):  python scripts/fetch_instances.py
The data set belongs to the authors of the paper and is not part of this project.
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import urllib.request
import zipfile
from datetime import date
from pathlib import Path

REPOSITORY = "https://github.com/Julius2627/COSP_Flow_Shop"
# Commit of the data set used for this project (branch main on 2026-11-12).
DEFAULT_REF = "c3d1a4730c994d78749111b84fa7f26b4006a4e8"
DEFAULT_TARGET = Path(__file__).resolve().parent.parent / "data" / "COSP_Flow_Shop"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ref", default=DEFAULT_REF, help="branch, tag or commit to download")
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--force", action="store_true", help="replace an existing download")
    args = parser.parse_args()

    target: Path = args.target
    if target.exists() and any(target.iterdir()):
        if not args.force:
            print(f"{target} already exists; use --force to download again")
            return 0
        shutil.rmtree(target)

    url = f"{REPOSITORY}/archive/{args.ref}.zip"
    print(f"downloading {url}")
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))

    commit = archive.comment.decode("ascii", "replace") or "unknown"  # GitHub stores the commit here
    target.mkdir(parents=True, exist_ok=True)
    root = target.resolve()
    files = 0
    for member in archive.infolist():
        relative = Path(*Path(member.filename).parts[1:])  # drop the top-level folder of the archive
        if member.is_dir() or not relative.parts:
            continue
        destination = (root / relative).resolve()
        if root not in destination.parents:
            raise RuntimeError(f"unexpected path in archive: {member.filename}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(archive.read(member))
        files += 1

    (target / "SOURCE.txt").write_text(
        f"repository: {REPOSITORY}\nref: {args.ref}\ncommit: {commit}\ndownloaded: {date.today().isoformat()}\n",
        encoding="utf-8",
    )
    print(f"{files} files written to {target} (commit {commit})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
