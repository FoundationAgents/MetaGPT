"""Valkey retriever."""

from typing import Any, List, Optional

from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle, QueryType
from llama_index.core.vector_stores.types import VectorStoreQuery

from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.vector_stores.valkey import ValkeyVectorStore


class ValkeyRetriever(RAGRetriever):
    """Valkey-based retriever using ValkeyVectorStore for KNN search."""

    def __init__(
        self,
        vector_store: ValkeyVectorStore,
        similarity_top_k: int = 5,
        nodes: Optional[List[BaseNode]] = None,
        embed_model: Any = None,
        **kwargs,
    ):
        super().__init__()
        self._vector_store = vector_store
        self._similarity_top_k = similarity_top_k
        self._embed_model = embed_model

        # If nodes are provided, add them to the store
        if nodes:
            self.add_nodes(nodes)

    @property
    def vector_store(self) -> ValkeyVectorStore:
        """Access the underlying vector store."""
        return self._vector_store

    def _embed_query(self, query: QueryBundle) -> List[float]:
        """Resolve the query embedding, preferring the async embed call when available."""
        if query.embedding is not None:
            return query.embedding
        if self._embed_model is None:
            raise ValueError("Query embedding is required. Provide an embed_model or set query.embedding.")
        return self._embed_model.get_query_embedding(query.query_str)

    async def _aembed_query(self, query: QueryBundle) -> List[float]:
        """Async embedding resolution that does not block the event loop when the model supports it."""
        if query.embedding is not None:
            return query.embedding
        if self._embed_model is None:
            raise ValueError("Query embedding is required. Provide an embed_model or set query.embedding.")
        if hasattr(self._embed_model, "aget_query_embedding"):
            return await self._embed_model.aget_query_embedding(query.query_str)
        return self._embed_model.get_query_embedding(query.query_str)

    def _build_result(self, result) -> List[NodeWithScore]:
        return [
            NodeWithScore(node=node, score=similarity) for node, similarity in zip(result.nodes, result.similarities)
        ]

    async def _aretrieve(self, query: QueryType) -> List[NodeWithScore]:
        """Async retrieve nodes matching the query."""
        if isinstance(query, str):
            query = QueryBundle(query_str=query)

        query_embedding = await self._aembed_query(query)
        store_query = VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=self._similarity_top_k)
        result = self._vector_store.query(store_query)
        return self._build_result(result)

    def _retrieve(self, query: QueryType) -> List[NodeWithScore]:
        """Sync retrieve nodes matching the query."""
        if isinstance(query, str):
            query = QueryBundle(query_str=query)

        query_embedding = self._embed_query(query)
        store_query = VectorStoreQuery(query_embedding=query_embedding, similarity_top_k=self._similarity_top_k)
        result = self._vector_store.query(store_query)
        return self._build_result(result)

    def add_nodes(self, nodes: List[BaseNode], **kwargs) -> None:
        """Add nodes to the underlying vector store."""
        self._vector_store.add(nodes, **kwargs)

    def persist(self, persist_dir: str = "", **kwargs) -> None:
        """Persist is a no-op since Valkey auto-persists.

        Valkey automatically saves data, so there is no need to implement."""

    def query_total_count(self) -> int:
        """Query total count of documents in the store."""
        return len(self._vector_store.scan_all_docs())

    def clear(self, **kwargs) -> None:
        """Clear all documents from the store and recreate the index."""
        self._vector_store.drop_index()
        self._vector_store.ensure_index()
