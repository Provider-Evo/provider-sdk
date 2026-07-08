"""Manifest 与插件加载测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from provider_sdk.types.manifest import load_manifest_file
from provider_sdk.runtime.loader import PluginLoader, discover_plugin_dirs

EXAMPLES_ROOT = Path(__file__).resolve().parents[1] / "examples"


def test_parse_echo_manifest() -> None:
    manifest = load_manifest_file(EXAMPLES_ROOT / "echo_platform")
    assert manifest.id == "provider-sdk.echo-platform"
    assert manifest.plugin_type == "platform"
    assert manifest.version == "0.1.0"


def test_discover_example_plugins() -> None:
    dirs = discover_plugin_dirs(EXAMPLES_ROOT)
    assert any(d.name == "echo_platform" for d in dirs)


@pytest.mark.asyncio
async def test_load_echo_plugin(aiohttp_client_session) -> None:
    loader = PluginLoader()
    loaded = await loader.discover_and_load(
        EXAMPLES_ROOT,
        aiohttp_client_session,
        get_plugin_config=lambda _pid: {"enabled": True, "prefix": ">> "},
    )
    assert len(loaded) == 1
    record = loaded[0]
    assert record.adapter.name == "echo"
    candidates = await record.adapter.candidates()
    assert len(candidates) == 1
    assert candidates[0].chat is True

    chunks = []
    async for piece in record.adapter.complete(
        candidates[0],
        [{"role": "user", "content": "hello"}],
        "echo",
        stream=False,
    ):
        chunks.append(piece)
    assert "".join(chunks) == ">> hello"

    await loader.unload_all()


@pytest.fixture
async def aiohttp_client_session():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        yield session
