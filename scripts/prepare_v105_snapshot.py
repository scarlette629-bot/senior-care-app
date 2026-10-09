#!/usr/bin/env python3
"""Prepare an isolated WECARE v1.05 GitHub Pages snapshot.

Run only against a detached worktree of the frozen stable commit.
Never run this script on the main branch or on someone's phone data.
The resulting snapshot is built once and stored on release/v1.05-site.
"""
from __future__ import annotations

import json
import pathlib
import sys


def replace_required(path: pathlib.Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"Cannot make stable snapshot: expected text missing in {path}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def main(directory: str, commit_sha: str) -> None:
    root = pathlib.Path(directory).resolve()
    if len(commit_sha) < 12:
        raise ValueError("A pinned Git commit SHA is required")
    prefix = "/senior-care-app/v1.05/"
    source_prefix = "/senior-care-app/"
    replace_required(root / "index.html", '"' + source_prefix, '"' + prefix)
    replace_required(root / "src/App.jsx",
                     'src="/senior-care-app/wecare-logo.svg"',
                     'src="' + prefix + 'wecare-logo.svg"')
    manifest_path = root / "public/manifest.webmanifest"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["start_url"] = prefix
    manifest["scope"] = prefix
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    sw = root / "public/sw.js"
    replace_required(sw, 'const BASE="/senior-care-app/";',
                     'const BASE="' + prefix + '";')
    replace_required(sw, 'const CACHE="wecare-v1.0.5-shell";',
                     'const CACHE="wecare-v1.05-frozen-shell";')
    # Do not evict the current/live site's service worker cache when the
    # archived copy activates.
    replace_required(sw, 'k.startsWith("wecare-")',
                     'k.startsWith("wecare-v1.05-frozen-")')
    config = root / "vite.config.js"
    replace_required(config,
                     'const BUILD_ID = `${(process.env.GITHUB_SHA || "local").slice(0,12)}-${Date.now().toString(36)}`;',
                     'const BUILD_ID = "v1.05-' + commit_sha[:12] + '";')
    replace_required(config, 'publishedAt: new Date().toISOString()',
                     'publishedAt: "2026-10-09T04:21:00Z"')
    print(f"Prepared frozen snapshot at {prefix} from {commit_sha}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: prepare_v105_snapshot.py <detached-worktree> <commit-sha>")
    main(sys.argv[1], sys.argv[2])
