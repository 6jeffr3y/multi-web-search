#!/usr/bin/env python3
import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path

import httpx

from server import SearchEngine


class SearchEngineTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "providers.json"
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 60, "max_concurrency": 4},
            "providers": [{
                "name": "t", "adapter": "tavily", "enabled": True, "priority": 1,
                "endpoint": "https://search.test/search", "api_key": "test-key", "retries": 0
            }]
        }))
        self.engine = SearchEngine(self.path)
        calls = {"count": 0}

        async def handler(request):
            calls["count"] += 1
            return httpx.Response(200, json={"answer": "A", "results": [{"title": "T", "url": "https://x.test", "content": "S"}]})

        self.calls = calls
        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))

    async def asyncTearDown(self):
        await self.engine._client.aclose()
        self.tmp.cleanup()

    async def test_normalize_and_cache(self):
        first = await self.engine.search("q")
        second = await self.engine.search("q")
        self.assertEqual(first["provider"], "t")
        self.assertEqual(first["sources"][0]["url"], "https://x.test")
        self.assertTrue(second["cached"])
        self.assertEqual(self.calls["count"], 1)

    async def test_inflight_coalescing(self):
        a, b = await asyncio.gather(self.engine.search("same"), self.engine.search("same"))
        self.assertEqual(a["answer"], b["answer"])
        self.assertEqual(self.calls["count"], 1)

    async def test_zai_chat_web_search_sources(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [{
                "name": "glm", "adapter": "zai_chat_search", "enabled": True, "priority": 1,
                "endpoint": "https://zai.test/chat/completions", "model": "glm-test",
                "api_key": "test-key", "retries": 0
            }]
        }))
        await self.engine._client.aclose()

        async def handler(request):
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "grounded answer"}}],
                "web_search": [{"title": "source", "link": "https://source.test", "content": "snippet"}],
                "usage": {"total_tokens": 10}
            })

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await self.engine.search("latest", provider="glm", allow_fallback=False)
        self.assertEqual(result["answer"], "grounded answer")
        self.assertEqual(result["sources"][0]["url"], "https://source.test")

    async def test_mimo_selects_payg_endpoint_for_sk_key(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [{
                "name": "mimo", "adapter": "mimo_chat", "enabled": True, "priority": 1,
                "endpoint": "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
                "endpoint_by_key_prefix": {
                    "sk-": "https://api.xiaomimimo.com/v1/chat/completions"
                },
                "model": "mimo-v2.6-flash", "api_key": "sk-test", "retries": 0
            }]
        }))
        await self.engine._client.aclose()

        async def handler(request):
            self.assertEqual(request.url.host, "api.xiaomimimo.com")
            return httpx.Response(200, json={
                "choices": [{"message": {"content": "grounded", "annotations": []}}],
                "usage": {"total_tokens": 1}
            })

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await self.engine.search("latest", provider="mimo", allow_fallback=False)
        self.assertEqual(result["answer"], "grounded")

    async def test_mimo_disabled_plugin_error_is_actionable(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [{
                "name": "mimo", "adapter": "mimo_chat", "enabled": True, "priority": 1,
                "endpoint": "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
                "model": "mimo-v2.6-flash", "api_key": "tp-test", "retries": 0
            }]
        }))
        await self.engine._client.aclose()

        async def handler(request):
            return httpx.Response(400, json={"error": {
                "message": "web search tool found in the request body, but webSearchEnabled is false"
            }})

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with self.assertRaisesRegex(Exception, "MIMO_WEB_SEARCH_API_KEY"):
            await self.engine.search("latest", provider="mimo", allow_fallback=False)

    async def test_deepseek_anthropic_native_search(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [{
                "name": "deepseek-official", "adapter": "deepseek_anthropic_search",
                "enabled": True, "priority": 1,
                "endpoint": "https://api.deepseek.com/anthropic/v1/messages",
                "model": "deepseek-flash", "api_key": "sk-test", "retries": 0
            }]
        }))
        await self.engine._client.aclose()

        async def handler(request):
            sent = json.loads(request.content)
            self.assertEqual(sent["tools"][0]["type"], "web_search_20250305")
            self.assertEqual(request.headers["x-api-key"], "sk-test")
            return httpx.Response(200, json={
                "content": [
                    {"type": "web_search_tool_result", "content": [{
                        "type": "web_search_result", "url": "https://source.test",
                        "title": "source", "page_age": "2026-09-22"
                    }]},
                    {"type": "text", "text": "grounded answer", "citations": [{
                        "url": "https://source.test", "cited_text": "snippet"
                    }]}
                ],
                "usage": {"input_tokens": 5, "output_tokens": 2}
            })

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await self.engine.search("latest", provider="deepseek-official", allow_fallback=False)
        self.assertEqual(result["answer"], "grounded answer")
        self.assertEqual(result["sources"][0]["url"], "https://source.test")
        self.assertEqual(result["sources"][0]["snippet"], "snippet")

    async def test_deepseek_rejects_prose_only_false_positive(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [{
                "name": "deepseek-official", "adapter": "deepseek_anthropic_search",
                "enabled": True, "priority": 1,
                "endpoint": "https://api.deepseek.com/anthropic/v1/messages",
                "model": "deepseek-flash", "api_key": "sk-test", "retries": 0
            }]
        }))
        await self.engine._client.aclose()

        async def handler(request):
            return httpx.Response(200, json={
                "content": [{"type": "text", "text": "I would search the web."}]
            })

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with self.assertRaisesRegex(Exception, "web_search_tool_result"):
            await self.engine.search("latest", provider="deepseek-official", allow_fallback=False)

    def _write_native_config(self):
        self.path.write_text(json.dumps({
            "settings": {"cache_ttl_seconds": 0, "max_concurrency": 2},
            "providers": [
                {
                    "name": "deepseek-native", "family": "deepseek",
                    "adapter": "deepseek_search_api", "route": "native",
                    "produces_answer": False, "enabled": True, "priority": 3,
                    "endpoint": "https://api.deepseek.com/v1/tools/search",
                    "api_key": "sk-test", "retries": 0,
                },
                {
                    "name": "deepseek-official", "family": "deepseek",
                    "adapter": "deepseek_anthropic_search", "route": "model",
                    "produces_answer": True, "enabled": True, "priority": 5,
                    "endpoint": "https://api.deepseek.com/anthropic/v1/messages",
                    "model": "deepseek-flash", "api_key": "sk-test", "retries": 0,
                },
            ],
        }))

    async def test_deepseek_native_search_api(self):
        self._write_native_config()
        await self.engine._client.aclose()
        seen = {}

        async def handler(request):
            seen["host"] = request.url.host
            seen["path"] = request.url.path
            seen["body"] = json.loads(request.content)
            seen["auth"] = request.headers["authorization"]
            return httpx.Response(200, json={"results": [{
                "title": "DeepSeek V4", "url": "https://source.test/v4",
                "summary": "long summary", "snippet": "short",
                "date": "2026-09-10T00:00:00+00:00",
                "authority": 4, "rerank_score": 2.4,
            }]})

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        result = await self.engine.search("v4", provider="deepseek-native", allow_fallback=False)

        self.assertEqual(seen["host"], "api.deepseek.com")
        self.assertEqual(seen["path"], "/v1/tools/search")
        self.assertEqual(seen["body"]["query"], "v4")
        self.assertEqual(seen["body"]["count"], 5)
        self.assertFalse(seen["body"]["need_content"])
        self.assertEqual(seen["auth"], "Bearer sk-test")
        self.assertEqual(result["answer"], "")
        self.assertEqual(result["route"], "native")
        self.assertEqual(result["sources"][0]["snippet"], "long summary")
        self.assertEqual(result["sources"][0]["published_date"], "2026-09-10T00:00:00+00:00")
        self.assertEqual(result["sources"][0]["score"], 2.4)
        self.assertEqual(result["sources"][0]["authority"], 4)

    async def test_deepseek_native_applies_language_and_freshness_operators(self):
        self._write_native_config()
        await self.engine._client.aclose()
        seen = {}

        async def handler(request):
            seen["body"] = json.loads(request.content)
            return httpx.Response(200, json={"results": []})

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        await self.engine.search(
            "deepseek", provider="deepseek-native", allow_fallback=False,
            language="zh", freshness="week",
        )
        self.assertIn("lang:zh", seen["body"]["query"])
        self.assertIn("after:", seen["body"]["query"])

    async def test_family_alias_prefers_native_for_fast_and_model_for_deep(self):
        self._write_native_config()
        await self.engine._client.aclose()
        calls = []

        async def handler(request):
            calls.append(request.url.path)
            if request.url.path.endswith("/tools/search"):
                return httpx.Response(200, json={"results": [
                    {"title": "n", "url": "https://native.test", "summary": "s"}
                ]})
            return httpx.Response(200, json={
                "content": [
                    {"type": "web_search_tool_result", "content": [{
                        "type": "web_search_result", "url": "https://model.test",
                        "title": "m", "page_age": "",
                    }]},
                    {"type": "text", "text": "model answer"},
                ]
            })

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        fast = await self.engine.search("q", provider="dp", allow_fallback=False)
        deep = await self.engine.search("q2", provider="dp", mode="deep", allow_fallback=False)

        self.assertEqual(fast["provider"], "deepseek-native")
        self.assertEqual(fast["sources"][0]["url"], "https://native.test")
        self.assertEqual(deep["provider"], "deepseek-official")
        self.assertEqual(deep["answer"], "model answer")
        self.assertEqual(calls, ["/v1/tools/search", "/anthropic/v1/messages"])

    async def test_auto_prefers_family_from_env(self):
        self._write_native_config()
        config = json.loads(self.path.read_text())
        config["providers"].append({
            "name": "mimo", "family": "mimo", "adapter": "mimo_chat",
            "route": "model", "produces_answer": True, "enabled": True,
            "priority": 1, "endpoint": "https://mimo.test/chat/completions",
            "model": "mimo-test", "api_key": "sk-test", "retries": 0,
        })
        self.path.write_text(json.dumps(config))
        await self.engine._client.aclose()

        async def handler(request):
            if "mimo" in request.url.host:
                raise AssertionError("mimo should not be used")
            return httpx.Response(200, json={"results": [
                {"title": "n", "url": "https://native.test", "summary": "s"}
            ]})

        self.engine._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        os.environ["MULTI_WEB_SEARCH_PREFER"] = "dp"
        try:
            result = await self.engine.search("q")
        finally:
            os.environ.pop("MULTI_WEB_SEARCH_PREFER", None)
        self.assertEqual(result["provider"], "deepseek-native")


if __name__ == "__main__":
    unittest.main()
