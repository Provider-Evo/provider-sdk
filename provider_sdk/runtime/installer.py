"""从 Git URL 安装 Provider-Evo 插件。"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from provider_sdk.types.manifest import resolve_manifest_path

__all__ = ["install_plugin_from_git", "parse_git_url"]

_REF_RE = re.compile(r"^[\w./-]+$")


def parse_git_url(url: str, *, ref: str = "") -> Tuple[str, str]:
    """解析仓库 URL 与 ref（分支/标签）。"""
    raw = url.strip()
    if not raw:
        raise ValueError("git url 不能为空")
    if "#" in raw:
        base, frag = raw.split("#", 1)
        ref = ref or frag.strip()
    else:
        base = raw
    if not ref:
        ref = "main"
    if not _REF_RE.match(ref):
        raise ValueError(f"非法 ref: {ref}")
    return base.strip(), ref


def _git_clone(repo_url: str, git_ref: str, clone_dir: Path) -> None:
    cmd = ["git", "clone", "--depth", "1", "--branch", git_ref, repo_url, str(clone_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return
    cmd = ["git", "clone", "--depth", "1", repo_url, str(clone_dir)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "git clone failed")
    checkout = subprocess.run(
        ["git", "checkout", git_ref],
        cwd=clone_dir,
        capture_output=True,
        text=True,
    )
    if checkout.returncode != 0:
        raise RuntimeError(checkout.stderr or "git checkout failed")


def _resolve_plugin_folder(plugins_root: Path, pid: str) -> Path:
    short = pid.rsplit(".", 1)[-1]
    folder = plugins_root / pid.split(".")[-1].replace("_", "-").title()
    if folder.name.startswith("Provider-"):
        return folder
    folder = plugins_root / f"Provider-{short.replace('.', '-').title()}-Adapter"
    if "fncall" in short:
        return plugins_root / "Provider-Fncall-Util"
    if "webui" in short:
        return plugins_root / "Provider-Webui-Util"
    if "coplan" in short:
        return plugins_root / "Provider-Coplan-Util"
    return folder


def install_plugin_from_git(
    url: str,
    plugins_root: Path,
    *,
    ref: str = "",
    plugin_id: str = "",
) -> Path:
    """克隆 Git 仓库到 plugins/ 并返回插件目录。"""
    repo_url, git_ref = parse_git_url(url, ref=ref)
    plugins_root.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="provider-plugin-") as tmp:
        clone_dir = Path(tmp) / "repo"
        _git_clone(repo_url, git_ref, clone_dir)

        try:
            manifest_path = resolve_manifest_path(clone_dir)
        except FileNotFoundError as exc:
            raise FileNotFoundError("仓库根目录缺少 manifest") from exc

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        pid = plugin_id or str(data.get("id") or "").strip()
        if not pid:
            raise ValueError("manifest 缺少 id")

        folder = _resolve_plugin_folder(plugins_root, pid)
        if folder.exists():
            shutil.rmtree(folder)
        shutil.copytree(clone_dir, folder)
        return folder
