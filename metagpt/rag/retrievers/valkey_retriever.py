"""Valkey retriever."""

from typing import Any, List, Optional

from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle, QueryType
from llama_index.core.vector_stores.types import VectorStoreQuery

from metagpt.rag.retrievers.base import RAGRetriever
from metagpt.rag.vector_stores.valkey import ValkeyVectorStore, _run_async


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

    async def _aretrieve(self, query: QueryType) -> List[NodeWithScore]:
        """Async retrieve nodes matching the query."""
        if isinstance(query, str):
            query = QueryBundle(query_str=query)

        # Get embedding for query
        if query.embedding is None and self._embed_model is not None:
            query_embedding = self._embed_model.get_query_embedding(query.query_str)
        elif query.embedding is not None:
            query_embedding = query.embedding
        else:
            raise ValueError("Query embedding is required. Provide an embed_model or set query.embedding.")

        store_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=self._similarity_top_k,
        )

        result = await self._vector_store._async_query(store_query)

        nodes_with_scores = []
        for node, similarity, node_id in zip(result.nodes, result.similarities, result.ids):
            nodes_with_scores.append(NodeWithScore(node=node, score=similarity))

        return nodes_with_scores

    def _retrieve(self, query: QueryType) -> List[NodeWithScore]:
        """Sync retrieve nodes matching the query."""
        return _run_async(self._aretrieve(query))

    def add_nodes(self, nodes: List[BaseNode], **kwargs) -> None:
        """Add nodes to the underlying vector store."""
        self._vector_store.add(nodes, **kwargs)

    def persist(self, persist_dir: str = "", **kwargs) -> None:
        """Persist is a no-op since Valkey auto-persists.

        Valkey automatically saves data, so there is no need to implement."""

    def query_total_count(self) -> int:
        """Query total count of documents in the store."""
        keys = _run_async(self._vector_store._scan_all_docs())
        return len(keys)

    def clear(self, **kwargs) -> None:
        """Clear all documents from the store and recreate the index."""
        _run_async(self._async_clear())

    async def _async_clear(self) -> None:
        """Async implementation of clear."""
        await self._vector_store.drop_index()
        await self._vector_store._ensure_index()
