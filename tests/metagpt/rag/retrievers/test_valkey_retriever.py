"""Unit tests for ValkeyRetriever (synchronous client)."""

from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import QueryBundle, TextNode
from llama_index.core.vector_stores.types import VectorStoreQueryResult

from metagpt.rag.retrievers.valkey_retriever import ValkeyRetriever
from metagpt.rag.vector_stores.valkey import ValkeyVectorStore


@pytest.fixture
def mock_vector_store():
    store = MagicMock(spec=ValkeyVectorStore)
    store.add = MagicMock(return_value=["doc1", "doc2"])
    store.query = MagicMock(
        return_value=VectorStoreQueryResult(
            nodes=[TextNode(text="result", id_="doc1")],
            similarities=[0.95],
            ids=["doc1"],
        )
    )
    store.scan_all_docs = MagicMock(return_value=["test:rag:doc1", "test:rag:doc2"])
    store.drop_index = MagicMock()
    store.ensure_index = MagicMock()
    return store


@pytest.fixture
def mock_embed_model():
    model = MagicMock()
    model.get_query_embedding = MagicMock(return_value=[0.1, 0.2, 0.3, 0.4])
    # No aget_query_embedding by default
    if hasattr(model, "aget_query_embedding"):
        del model.aget_query_embedding
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
        retriever.persist("/some/path")

    def test_query_total_count(self, retriever, mock_vector_store):
        assert retriever.query_total_count() == 2
        mock_vector_store.scan_all_docs.assert_called_once()

    def test_sync_retrieve_uses_embed_model(self, retriever, mock_vector_store, mock_embed_model):
        results = retriever._retrieve(QueryBundle(query_str="test query"))
        assert len(results) == 1
        assert results[0].node.text == "result"
        assert results[0].score == 0.95
        mock_embed_model.get_query_embedding.assert_called_once_with("test query")
        mock_vector_store.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_aretrieve_returns_nodes_with_scores(self, retriever, mock_vector_store):
        results = await retriever._aretrieve(QueryBundle(query_str="test query"))
        assert len(results) == 1
        assert results[0].node.text == "result"
        assert results[0].score == 0.95

    @pytest.mark.asyncio
    async def test_aretrieve_prefers_async_embedding(self, mock_vector_store):
        from unittest.mock import AsyncMock

        model = MagicMock()
        model.aget_query_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4])
        model.get_query_embedding = MagicMock(return_value=[9.9, 9.9, 9.9, 9.9])
        retriever = ValkeyRetriever(vector_store=mock_vector_store, similarity_top_k=5, embed_model=model)

        await retriever._aretrieve(QueryBundle(query_str="q"))

        model.aget_query_embedding.assert_awaited_once_with("q")
        model.get_query_embedding.assert_not_called()

    def test_retrieve_uses_provided_embedding(self, retriever, mock_vector_store, mock_embed_model):
        results = retriever._retrieve(QueryBundle(query_str="q", embedding=[0.5, 0.5, 0.5, 0.5]))
        assert len(results) == 1
        # Provided embedding short-circuits the embed model.
        mock_embed_model.get_query_embedding.assert_not_called()

    def test_clear_drops_and_recreates(self, retriever, mock_vector_store):
        retriever.clear()
        mock_vector_store.drop_index.assert_called_once()
        mock_vector_store.ensure_index.assert_called_once()
