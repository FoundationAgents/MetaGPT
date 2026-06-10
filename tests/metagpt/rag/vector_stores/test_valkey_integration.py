"""Integration tests for ValkeyVectorStore against a live Valkey instance.

Requires: Valkey container (valkey/valkey-bundle:9.1) with Search module on port 6379.
Run: pytest tests/metagpt/rag/vector_stores/test_valkey_integration.py -v --timeout=60
"""

import time
from uuid import uuid4

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery

from metagpt.rag.vector_stores.valkey import ValkeyVectorStore


def _is_valkey_available():
    """Check if Valkey is reachable on localhost:6379."""
    try:
        store = ValkeyVectorStore(host="localhost", port=6379, vector_dimensions=4)
        store._connect()
        store._client.ping()
        store._client.close()
        return True
    except Exception:
        return False


def _wait_for_indexing(store: ValkeyVectorStore, expected_count: int, timeout: float = 10.0):
    """Poll FT.INFO until num_docs matches expected count."""
    from glide_sync import ft

    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            info = ft.info(store._client, store.index_name)
            if isinstance(info, dict):
                num_docs = int(info.get(b"num_docs", info.get("num_docs", 0)))
            elif isinstance(info, (list, tuple)):
                # Parse flat list [key, value, key, value, ...]
                info_dict = {}
                for i in range(0, len(info) - 1, 2):
                    k = info[i]
                    v = info[i + 1]
                    if isinstance(k, bytes):
                        k = k.decode("utf-8")
                    info_dict[k] = v
                num_docs = int(info_dict.get("num_docs", 0))
            else:
                num_docs = 0

            if num_docs >= expected_count:
                return
        except Exception:
            pass
        time.sleep(0.1)

    raise TimeoutError(f"Indexing did not complete within {timeout}s. Expected {expected_count} docs.")


@pytest.fixture
def valkey_store():
    """Create a ValkeyVectorStore with unique index name and prefix for test isolation."""
    if not _is_valkey_available():
        pytest.skip("Valkey not available on localhost:6379")

    uid = uuid4().hex[:8]
    store = ValkeyVectorStore(
        host="localhost",
        port=6379,
        index_name=f"test_{uid}",
        prefix=f"test:{uid}:",
        vector_dimensions=4,
        client_name="metagpt_rag_client",
        request_timeout=30000,
    )
    store._connect()
    store.ensure_index()
    yield store
    # Cleanup
    try:
        store.drop_index()
    except Exception:
        pass
    try:
        store._client.close()
    except Exception:
        pass


class TestValkeyIntegration:
    def test_create_index_and_verify_ft_info(self, valkey_store):
        """Create index, verify via FT.INFO."""
        from glide_sync import ft

        info = ft.info(valkey_store._client, valkey_store.index_name)
        assert info is not None

    def test_add_single_document_and_retrieve(self, valkey_store):
        """Add 1 doc, KNN search, verify match."""
        node = TextNode(text="hello valkey", embedding=[1.0, 0.0, 0.0, 0.0], id_="single_doc")
        ids = valkey_store.add([node])
        assert len(ids) == 1

        _wait_for_indexing(valkey_store, 1)

        query = VectorStoreQuery(query_embedding=[1.0, 0.0, 0.0, 0.0], similarity_top_k=1)
        result = valkey_store.query(query)

        assert len(result.nodes) >= 1
        assert result.ids[0] == "single_doc"

    def test_add_batch_documents(self, valkey_store):
        """Add multiple docs, verify all stored."""
        nodes = [TextNode(text=f"doc {i}", embedding=[float(i), 0.0, 0.0, 0.0], id_=f"batch_{i}") for i in range(5)]
        ids = valkey_store.add(nodes)
        assert len(ids) == 5

        _wait_for_indexing(valkey_store, 5)

        keys = valkey_store.scan_all_docs()
        assert len(keys) == 5

    def test_knn_retrieval_ordering(self, valkey_store):
        """Add docs with known vectors, verify COSINE ordering."""
        nodes = [
            TextNode(text="very close", embedding=[0.9, 0.1, 0.0, 0.0], id_="close"),
            TextNode(text="medium", embedding=[0.5, 0.5, 0.0, 0.0], id_="medium"),
            TextNode(text="far away", embedding=[0.0, 0.0, 0.0, 1.0], id_="far"),
        ]
        valkey_store.add(nodes)
        _wait_for_indexing(valkey_store, 3)

        query = VectorStoreQuery(query_embedding=[1.0, 0.0, 0.0, 0.0], similarity_top_k=3)
        result = valkey_store.query(query)

        # The closest should come first
        assert len(result.nodes) == 3
        assert result.ids[0] == "close"

    def test_knn_similarity_top_k(self, valkey_store):
        """Verify only top_k results returned."""
        nodes = [
            TextNode(
                text=f"doc {i}",
                embedding=[float(i) / 10.0, 0.0, 0.0, 1.0],
                id_=f"topk_{i}",
            )
            for i in range(10)
        ]
        valkey_store.add(nodes)
        _wait_for_indexing(valkey_store, 10)

        query = VectorStoreQuery(query_embedding=[0.5, 0.0, 0.0, 1.0], similarity_top_k=3)
        result = valkey_store.query(query)

        assert len(result.nodes) == 3

    def test_delete_document(self, valkey_store):
        """Add doc, delete, verify not found."""
        node = TextNode(text="to be deleted", embedding=[1.0, 1.0, 0.0, 0.0], id_="del_doc")
        valkey_store.add([node])
        _wait_for_indexing(valkey_store, 1)

        valkey_store.delete("del_doc")

        # Should have no keys
        keys = valkey_store.scan_all_docs()
        assert len(keys) == 0

    def test_delete_removes_all_chunks_of_source(self, valkey_store):
        """Multiple nodes sharing one ref_doc_id must all be removed by delete(ref_doc_id)."""
        from llama_index.core.schema import NodeRelationship, RelatedNodeInfo

        src = "source_doc_42"
        nodes = []
        for i in range(3):
            n = TextNode(text=f"chunk {i}", embedding=[float(i), 0.1, 0.2, 0.3], id_=f"chunk_{i}")
            n.relationships = {NodeRelationship.SOURCE: RelatedNodeInfo(node_id=src)}
            nodes.append(n)
        valkey_store.add(nodes)
        _wait_for_indexing(valkey_store, 3)

        valkey_store.delete(src)

        keys = valkey_store.scan_all_docs()
        assert len(keys) == 0

    def test_drop_index_cleans_all_keys(self, valkey_store):
        """Create index + docs, drop, verify no keys remain."""
        nodes = [TextNode(text=f"doc {i}", embedding=[0.1, 0.2, 0.3, float(i)], id_=f"drop_{i}") for i in range(3)]
        valkey_store.add(nodes)
        _wait_for_indexing(valkey_store, 3)

        valkey_store.drop_index()

        keys = valkey_store.scan_all_docs()
        assert len(keys) == 0

    def test_query_empty_index(self, valkey_store):
        """Query index with no docs, verify empty result."""
        query = VectorStoreQuery(query_embedding=[1.0, 0.0, 0.0, 0.0], similarity_top_k=5)
        result = valkey_store.query(query)

        assert len(result.nodes) == 0

    def test_connection_with_wrong_host_raises(self):
        """Verify connection error handling."""
        store = ValkeyVectorStore(host="nonexistent.invalid.host", port=9999, request_timeout=1000)
        with pytest.raises(Exception):
            store._connect()

    def test_metadata_preserved_in_retrieval(self, valkey_store):
        """Verify metadata fields round-trip correctly."""
        metadata = {"source": "test_file.pdf", "page": 42, "author": "test_author"}
        node = TextNode(
            text="metadata test",
            embedding=[0.5, 0.5, 0.5, 0.5],
            id_="meta_doc",
            metadata=metadata,
        )
        valkey_store.add([node])
        _wait_for_indexing(valkey_store, 1)

        query = VectorStoreQuery(query_embedding=[0.5, 0.5, 0.5, 0.5], similarity_top_k=1)
        result = valkey_store.query(query)

        assert len(result.nodes) == 1
        assert result.nodes[0].metadata.get("source") == "test_file.pdf"
        assert result.nodes[0].metadata.get("page") == 42

    def test_large_batch_insert(self, valkey_store):
        """Add many docs in batches, verify all indexed."""
        nodes = [
            TextNode(
                text=f"large batch doc {i}",
                embedding=[float(i % 10) / 10.0, float(i % 5) / 5.0, 0.1, 0.1],
                id_=f"large_{i}",
            )
            for i in range(20)
        ]
        ids = valkey_store.add(nodes)
        assert len(ids) == 20

        _wait_for_indexing(valkey_store, 20, timeout=30.0)

        keys = valkey_store.scan_all_docs()
        assert len(keys) == 20
