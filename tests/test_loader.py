"""Manifest 与插件加载测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from provider_sdk.runtime.loader import PluginLoader, discover_plugin_dirs
from provider_sdk.runtime.manager import PluginManager
from provider_sdk.types.manifest import load_manifest_file

EXAMPLES_ROOT = Path(__file__).resolve().parents[1] / "examples"


def test_parse_hello_manifest() -> None:
    manifest = load_manifest_file(EXAMPLES_ROOT / "hello_plugin")
    assert manifest.id == "provider-sdk.hello-plugin"
    assert manifest.plugin_type == "general"


def test_discover_examples() -> None:
    dirs = discover_plugin_dirs(EXAMPLES_ROOT)
    names = {d.name for d in dirs}
    assert "hello_plugin" in names
    assert "echo_platform" in names


@pytest.mark.asyncio
async def test_load_hello_plugin(aiohttp_client_session) -> None:
    loader = PluginLoader()
    loaded = await loader.discover_and_load(EXAMPLES_ROOT, aiohttp_client_session)
    hello = next(r for r in loaded if r.manifest.id.endswith("hello-plugin"))
    assert hello.adapter is None
    assert any(c["type"] == "route" for c in hello.components)
    await loader.unload_all()


@pytest.mark.asyncio
async def test_load_platform_plugin_only(aiohttp_client_session) -> None:
    loader = PluginLoader(plugin_type_filter="platform")
    loaded = await loader.discover_and_load(
        EXAMPLES_ROOT,
        aiohttp_client_session,
        get_plugin_config=lambda _pid: {"prefix": ">> "},
    )
    assert len(loaded) == 1
    assert loaded[0].adapter is not None
    assert loaded[0].adapter.name == "echo"
    await loader.unload_all()


@pytest.mark.asyncio
async def test_plugin_manager(aiohttp_client_session) -> None:
    mgr = PluginManager()
    await mgr.load_all(EXAMPLES_ROOT, aiohttp_client_session)
    routes = mgr.get_components("route")
    assert any(r["plugin_id"].endswith("hello-plugin") for r in routes)
    assert len(mgr.get_platform_adapters()) == 1
    await mgr.unload_all()


@pytest.fixture
async def aiohttp_client_session():
    import aiohttp

    async with aiohttp.ClientSession() as session:
        yield session
