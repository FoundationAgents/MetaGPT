"""Unit tests for ValkeyRetriever."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult

from metagpt.rag.retrievers.valkey_retriever import ValkeyRetriever
from metagpt.rag.vector_stores.valkey import ValkeyVectorStore


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=ValkeyVectorStore)
    store.add = MagicMock(return_value=["doc1", "doc2"])
    store._async_query = AsyncMock(
        return_value=VectorStoreQueryResult(
            nodes=[TextNode(text="result", id_="doc1")],
            similarities=[0.95],
            ids=["doc1"],
        )
    )
    store._scan_all_docs = AsyncMock(return_value=["test:rag:doc1", "test:rag:doc2"])
    store.drop_index = AsyncMock()
    store._ensure_index = AsyncMock()
    return store


@pytest.fixture
def mock_embed_model():
    model = MagicMock()
    model.get_query_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    return model


@pytest.fixture
def retriever(mock_vector_store, mock_embed_model):
    return ValkeyRetriever(
        vector_store=mock_vector_store,
        similarity_top_k=5,
        embed_model=mock_embed_model,
    )


class TestValkeyRetriever:
    def test_add_nodes(self, retriever, mock_vector_store):
        nodes = [TextNode(text="hello", embedding=[0.1, 0.2, 0.3, 0.4])]
        retriever.add_nodes(nodes)

        mock_vector_store.add.assert_called_once_with(nodes)

    def test_persist_is_noop(self, retriever):
        # Should not raise
        retriever.persist("/some/path")

    def test_query_total_count(self, retriever, mock_vector_store):
        count = retriever.query_total_count()
        assert count == 2
        mock_vector_store._scan_all_docs.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_returns_nodes_with_scores(self, retriever, mock_vector_store, mock_embed_model):
        from llama_index.core.schema import QueryBundle

        query = QueryBundle(query_str="test query")
        results = await retriever._aretrieve(query)

        assert len(results) == 1
        assert results[0].node.text == "result"
        assert results[0].score == 0.95

    @pytest.mark.asyncio
    async def test_clear_drops_and_recreates(self, retriever, mock_vector_store):
        await retriever._async_clear()

        mock_vector_store.drop_index.assert_called_once()
        mock_vector_store._ensure_index.assert_called_once()
