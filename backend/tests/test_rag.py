"""
Tests for RAG pipeline components (no live API calls).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestPromptTemplates:
    """Test the prompt template system."""

    def test_templates_exist(self):
        from rag_pipeline import PROMPT_TEMPLATES
        assert "default" in PROMPT_TEMPLATES
        assert "structured" in PROMPT_TEMPLATES
        assert "bullet_summary" in PROMPT_TEMPLATES

    def test_default_template_has_placeholders(self):
        from rag_pipeline import PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES["default"]
        assert "{context}" in template
        assert "{history}" in template
        assert "{question}" in template

    def test_structured_template_has_format_instructions(self):
        from rag_pipeline import PROMPT_TEMPLATES
        template = PROMPT_TEMPLATES["structured"]
        assert "Summary" in template
        assert "Details" in template
        assert "Sources" in template


class TestConfidenceAssessment:
    """Test confidence scoring logic."""

    def test_high_confidence(self):
        from rag_pipeline import _assess_confidence
        docs = [{"score": 90}, {"score": 85}, {"score": 95}]
        result = _assess_confidence(docs)
        assert result["label"] == "high"
        assert result["score"] > 80

    def test_medium_confidence(self):
        from rag_pipeline import _assess_confidence
        docs = [{"score": 60}, {"score": 55}, {"score": 65}]
        result = _assess_confidence(docs)
        assert result["label"] == "medium"
        assert 50 < result["score"] <= 80

    def test_low_confidence(self):
        from rag_pipeline import _assess_confidence
        docs = [{"score": 20}, {"score": 30}, {"score": 10}]
        result = _assess_confidence(docs)
        assert result["label"] == "low"
        assert result["score"] <= 50

    def test_empty_docs_confidence(self):
        from rag_pipeline import _assess_confidence
        result = _assess_confidence([])
        assert result["label"] == "low"
        assert result["score"] == 0


class TestHistoryManagement:
    """Test session history management."""

    def test_get_empty_history(self):
        from rag_pipeline import _get_history
        history = _get_history("nonexistent_user")
        assert history == []

    def test_add_and_get_history(self):
        from rag_pipeline import _get_history, _add_to_history
        _add_to_history("test_hist_user", "What is X?", "X is Y.")
        history = _get_history("test_hist_user")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "model"

    def test_history_truncation(self):
        from rag_pipeline import _get_history, _add_to_history, MAX_SESSION_TURNS
        username = "test_trunc_user"
        # Add more than MAX_SESSION_TURNS conversations
        for i in range(MAX_SESSION_TURNS + 5):
            _add_to_history(username, f"Q{i}", f"A{i}")
        history = _get_history(username)
        assert len(history) <= MAX_SESSION_TURNS * 2


class TestBuildHistoryText:
    """Test history text formatting."""

    def test_empty_history(self):
        from rag_pipeline import _build_history_text
        result = _build_history_text([])
        assert result == "No prior conversation."

    def test_format_history(self):
        from rag_pipeline import _build_history_text
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "model", "content": "Hi there"},
        ]
        result = _build_history_text(history)
        assert "User: Hello" in result
        assert "Model: Hi there" in result


class TestCacheModule:
    """Test the LRU cache module."""

    def test_set_and_get(self):
        from cache import LRUCache
        cache = LRUCache(max_size=10)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_miss(self):
        from cache import LRUCache
        cache = LRUCache(max_size=10)
        assert cache.get("nonexistent") is None

    def test_cache_eviction(self):
        from cache import LRUCache
        cache = LRUCache(max_size=3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        cache.set("d", 4)  # Should evict "a"
        assert cache.get("a") is None
        assert cache.get("d") == 4

    def test_cache_ttl_expiration(self):
        import time
        from cache import LRUCache
        cache = LRUCache(max_size=10, default_ttl=1)
        cache.set("expire_key", "value", ttl=1)
        assert cache.get("expire_key") == "value"
        time.sleep(1.1)
        assert cache.get("expire_key") is None

    def test_cache_stats(self):
        from cache import LRUCache
        cache = LRUCache(max_size=10)
        cache.set("x", 1)
        cache.get("x")  # hit
        cache.get("y")  # miss
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1


class TestErrorHandlers:
    """Test custom error classes."""

    def test_app_error(self):
        from error_handlers import AppError
        err = AppError(message="test error", error_code="TEST", status_code=400)
        assert err.message == "test error"
        assert err.error_code == "TEST"
        assert err.status_code == 400

    def test_rag_pipeline_error(self):
        from error_handlers import RAGPipelineError
        err = RAGPipelineError("search failed")
        assert err.error_code == "RAG_PIPELINE_ERROR"
        assert err.status_code == 503

    def test_authorization_error(self):
        from error_handlers import AuthorizationError
        err = AuthorizationError()
        assert err.error_code == "AUTHORIZATION_ERROR"
        assert err.status_code == 403
