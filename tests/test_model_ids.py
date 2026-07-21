from __future__ import annotations

from provider_sdk.types.model_ids import ModelIdRegistry, upstream_to_public_id


class TestUpstreamToPublicId:
    def test_qwen_version_dots(self):
        assert upstream_to_public_id("qwen3.7-max") == "qwen3-7-max"
        assert upstream_to_public_id("qwen3.7-plus") == "qwen3-7-plus"

    def test_qwen_without_dots(self):
        assert upstream_to_public_id("qwen3-235b-a22b") == "qwen3-235b-a22b"

    def test_cloudflare_path(self):
        assert upstream_to_public_id(
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        ) == "cf-meta-llama-3-3-70b-instruct-fp8-fast"

    def test_openrouter_slug(self):
        assert upstream_to_public_id("qwen/qwen3-235b-a22b:free") == (
            "qwen-qwen3-235b-a22b-free"
        )


class TestModelIdRegistry:
    def test_roundtrip(self):
        reg = ModelIdRegistry("test", persist=False)
        public = reg.register_many(["qwen3.7-max", "qwen3-235b-a22b"])
        assert "qwen3-7-max" in public
        assert reg.resolve_upstream("qwen3-7-max") == "qwen3.7-max"
        assert reg.resolve_upstream("qwen3.7-max") == "qwen3.7-max"

    def test_cloudflare_kimi_version_dots(self):
        assert upstream_to_public_id(
            "@cf/moonshotai/kimi-k2.7-code"
        ) == "cf-moonshotai-kimi-k2-7-code"

    def test_catalog_display_name(self):
        reg = ModelIdRegistry("test", persist=False)
        public = reg.register_catalog(
            [{"id": "@cf/vendor/abc123deadbeef", "name": "Kimi K2.7 Code"}]
        )
        assert public == ["kimi-k2-7-code"]
        assert reg.resolve_upstream("kimi-k2-7-code").startswith("@cf/")
