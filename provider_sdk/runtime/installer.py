"""从 Git URL 安装 Provider-Evo 插件。"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

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
        tmp_path = Path(tmp)
        clone_dir = tmp_path / "repo"
        cmd = ["git", "clone", "--depth", "1", "--branch", git_ref, repo_url, str(clone_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
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

        manifest_path = clone_dir / "_manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError("仓库根目录缺少 _manifest.json")

        import json

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        pid = plugin_id or str(data.get("id") or "").strip()
        if not pid:
            raise ValueError("manifest 缺少 id")

        folder = plugins_root / pid.split(".")[-1].replace("_", "-").title()
        if not folder.name.startswith("Provider-"):
            short = pid.rsplit(".", 1)[-1]
            folder = plugins_root / f"Provider-{short.replace('.', '-').title()}-Adapter"
            if "fncall" in short:
                folder = plugins_root / "Provider-Fncall-Util"
            elif "webui" in short:
                folder = plugins_root / "Provider-Webui-Util"
            elif "coplan" in short:
                folder = plugins_root / "Provider-Coplan-Util"

        if folder.exists():
            shutil.rmtree(folder)
        shutil.copytree(clone_dir, folder)
        return folder
