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

    def test_public_id_fed_as_upstream_does_not_clobber(self):
        """公开名被误当 upstream 二次注册时，不得覆盖真实映射。"""
        from provider_sdk.types.model_ids import build_model_id_maps

        # 真实上游在前，公开名在后
        _pub, p2u, _u2p = build_model_id_maps(
            ["qwen3.7-plus", "qwen3-7-plus", "qwen3-max"]
        )
        assert p2u["qwen3-7-plus"] == "qwen3.7-plus"
        assert p2u["qwen3.7-plus"] == "qwen3.7-plus"
        assert "qwen3-7-plus-1df11e" not in p2u or p2u.get("qwen3-7-plus") == "qwen3.7-plus"

        # 公开名在前，真实上游在后 → 夺回映射
        _pub2, p2u2, _ = build_model_id_maps(["qwen3-7-plus", "qwen3.7-plus"])
        assert p2u2["qwen3-7-plus"] == "qwen3.7-plus"

    def test_registry_normalize_public_before_register(self):
        reg = ModelIdRegistry("test", persist=False)
        reg.register_many(["qwen3.7-plus"])
        assert reg.resolve_upstream("qwen3-7-plus") == "qwen3.7-plus"
        # 再喂公开名，映射仍正确
        reg.register_many(["qwen3-7-plus", "qwen3.5-plus"])
        assert reg.resolve_upstream("qwen3-7-plus") == "qwen3.7-plus"
        assert reg.resolve_upstream("qwen3-5-plus") == "qwen3.5-plus"
        assert "qwen3-7-plus" in reg.public_models
        assert "qwen3-5-plus" in reg.public_models

    def test_merge_fallback_keeps_identity_upstream(self):
        reg = ModelIdRegistry("test", persist=False)
        reg.register_many(["qwen3-max", "qwen3.7-plus"])
        out = reg.merge_fallback(["qwen3-max", "qwen-plus-2025-01-25"])
        assert "qwen3-max" in out or "qwen3-max" in reg.public_models
        assert reg.resolve_upstream("qwen3-max") == "qwen3-max"
        assert reg.resolve_upstream("qwen3-7-plus") == "qwen3.7-plus"

    def test_register_many_returns_full_public_list(self):
        reg = ModelIdRegistry("test", persist=False)
        first = reg.register_many(["qwen3.7-plus", "qwen3-max"])
        assert set(first) == {"qwen3-7-plus", "qwen3-max"}
        second = reg.register_many(["qwen3.6-plus"])
        assert set(second) == {"qwen3-7-plus", "qwen3-max", "qwen3-6-plus"}

    def test_register_merge_dedupes_public_and_upstream(self):
        reg = ModelIdRegistry("test", persist=False)
        reg.register_many(["qwen3.7-plus"])
        out = reg.register_merge(
            ["qwen3-7-plus", "qwen3.6-plus"],
            fallback=["qwen3-max"],
        )
        assert set(out) == {"qwen3-7-plus", "qwen3-max", "qwen3-6-plus"}
        assert reg.resolve_upstream("qwen3-7-plus") == "qwen3.7-plus"
