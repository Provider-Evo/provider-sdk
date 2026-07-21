"""组件装饰器测试。"""

from provider_sdk import API, Hook, ProviderPlugin, Route
from provider_sdk.core.components import collect_components


class DemoPlugin(ProviderPlugin):
    @Route("/demo", methods=["GET"])
    async def demo_route(self) -> dict:
        return {"ok": True}

    @Hook("test.hook")
    async def demo_hook(self) -> None:
        return None

    @API("demo_api", public=True)
    async def demo_api(self) -> dict:
        return {"pong": True}


def test_collect_components() -> None:
    plugin = DemoPlugin()
    comps = collect_components(plugin)
    types = {c["type"] for c in comps}
    assert types == {"route", "hook", "api"}
    names = {c["name"] for c in comps}
    assert "demo" in names or "demo_route" in names
    assert "demo_api" in names
