"""Integration tests for ValkeyRetriever against a live Valkey instance.

Requires: Valkey container (valkey/valkey-bundle:9.1) with Search module on port 6379.
Run: pytest tests/metagpt/rag/retrievers/test_valkey_retriever_integration.py -v --timeout=60
"""

import asyncio
import time
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import pytest_asyncio
from llama_index.core.schema import QueryBundle, TextNode

from metagpt.rag.retrievers.valkey_retriever import ValkeyRetriever
from metagpt.rag.vector_stores.valkey import ValkeyVectorStore

pytestmark = pytest.mark.asyncio


async def _is_valkey_available():
    """Check if Valkey is reachable on localhost:6379."""
    try:
        store = ValkeyVectorStore(host="localhost", port=6379, vector_dimensions=4)
        await store._connect()
        await store._client.custom_command(["PING"])
        await store._client.close()
        return True
    except Exception:
        return False


async def _wait_for_indexing(store: ValkeyVectorStore, expected_count: int, timeout: float = 10.0):
    """Poll FT.INFO until num_docs matches expected count."""
    from glide import ft

    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            info = await ft.info(store._client, store.index_name)
            if isinstance(info, dict):
                num_docs = int(info.get(b"num_docs", info.get("num_docs", 0)))
            elif isinstance(info, (list, tuple)):
                info_dict = {}
                for i in range(0, len(info) - 1, 2):
                    k = info[i]
                    if isinstance(k, bytes):
                        k = k.decode("utf-8")
                    info_dict[k] = info[i + 1]
                num_docs = int(info_dict.get("num_docs", 0))
            else:
                num_docs = 0
            if num_docs >= expected_count:
                return
        except Exception:
            pass
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Indexing did not complete within {timeout}s")


@pytest_asyncio.fixture
async def retriever_setup():
    """Create a ValkeyRetriever with a live store for integration testing."""
    available = await _is_valkey_available()
    if not available:
        pytest.skip("Valkey not available on localhost:6379")

    uid = uuid4().hex[:8]
    store = ValkeyVectorStore(
        host="localhost",
        port=6379,
        index_name=f"test_retriever_{uid}",
        prefix=f"test:retriever:{uid}:",
        vector_dimensions=4,
        client_name="metagpt_rag_client",
        request_timeout=30000,
    )
    await store._connect()
    await store._ensure_index()

    mock_embed_model = MagicMock()
    mock_embed_model.get_query_embedding = MagicMock(return_value=[0.5, 0.5, 0.0, 0.0])

    retriever = ValkeyRetriever(
        vector_store=store,
        similarity_top_k=5,
        embed_model=mock_embed_model,
    )

    yield retriever, store

    # Cleanup
    try:
        await store.drop_index()
    except Exception:
        pass
    try:
        await store._client.close()
    except Exception:
        pass


class TestValkeyRetrieverIntegration:
    async def test_retriever_end_to_end(self, retriever_setup):
        """Create retriever, add nodes with embeddings, retrieve."""
        retriever, store = retriever_setup

        nodes = [
            TextNode(text="closest match", embedding=[0.5, 0.5, 0.0, 0.0], id_="r_doc1"),
            TextNode(text="second match", embedding=[0.3, 0.3, 0.3, 0.0], id_="r_doc2"),
            TextNode(text="far away", embedding=[0.0, 0.0, 1.0, 1.0], id_="r_doc3"),
        ]
        await store._async_add(nodes)
        await _wait_for_indexing(store, 3)

        query = QueryBundle(query_str="test query", embedding=[0.5, 0.5, 0.0, 0.0])
        results = await retriever._aretrieve(query)

        assert len(results) >= 1
        # The closest match should be first
        assert results[0].node.id_ == "r_doc1"

    async def test_retriever_add_and_clear(self, retriever_setup):
        """Add nodes, clear, verify empty."""
        retriever, store = retriever_setup

        nodes = [
            TextNode(text="to be cleared", embedding=[1.0, 0.0, 0.0, 0.0], id_="clear_doc"),
        ]
        await store._async_add(nodes)
        await _wait_for_indexing(store, 1)

        await retriever._async_clear()

        # After clear, no keys should remain
        keys = await store._scan_all_docs()
        assert len(keys) == 0

    async def test_retriever_multiple_queries(self, retriever_setup):
        """Verify consistent results across multiple queries."""
        retriever, store = retriever_setup

        nodes = [
            TextNode(text="alpha", embedding=[1.0, 0.0, 0.0, 0.0], id_="mq_1"),
            TextNode(text="beta", embedding=[0.0, 1.0, 0.0, 0.0], id_="mq_2"),
        ]
        await store._async_add(nodes)
        await _wait_for_indexing(store, 2)

        query = QueryBundle(query_str="query", embedding=[1.0, 0.0, 0.0, 0.0])

        results1 = await retriever._aretrieve(query)
        results2 = await retriever._aretrieve(query)

        assert len(results1) == len(results2)
        assert results1[0].node.id_ == results2[0].node.id_
