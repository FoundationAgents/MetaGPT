"""Unit tests for ValkeyVectorStore with a mocked synchronous valkey-glide client."""

from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery

from metagpt.rag.vector_stores.valkey import ValkeyVectorStore


@pytest.fixture
def store():
    return ValkeyVectorStore(
        host="localhost",
        port=6379,
        index_name="test_index",
        prefix="test:rag:",
        vector_dimensions=4,
        client_name="metagpt_rag_client",
    )


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.exec = MagicMock(return_value=[b"OK"])
    client.delete = MagicMock(return_value=1)
    client.ping = MagicMock(return_value=b"PONG")
    client.scan = MagicMock()
    client.close = MagicMock()
    return client


def _glide_sync_mock(**overrides):
    """Build a MagicMock standing in for the glide_sync module."""
    base = dict(
        GlideClient=MagicMock(),
        GlideClientConfiguration=MagicMock(),
        NodeAddress=MagicMock(),
        ServerCredentials=MagicMock(),
        Batch=MagicMock(),
        json_batch=MagicMock(),
        glide_json=MagicMock(),
        ft=MagicMock(),
        FtSearchOptions=MagicMock(),
        ReturnField=MagicMock(),
        DataType=MagicMock(),
        DistanceMetricType=MagicMock(COSINE="COSINE", L2="L2", IP="IP"),
        FtCreateOptions=MagicMock(),
        TextField=MagicMock(),
        VectorAlgorithm=MagicMock(HNSW="HNSW", FLAT="FLAT"),
        VectorField=MagicMock(),
        VectorFieldAttributesFlat=MagicMock(),
        VectorFieldAttributesHnsw=MagicMock(),
        VectorType=MagicMock(FLOAT32="FLOAT32"),
    )
    base.update(overrides)
    return MagicMock(**base)


class TestValkeyVectorStoreConnection:
    def test_connect_success(self, store):
        mock_glide_client = MagicMock()
        glide_client_cls = MagicMock()
        glide_client_cls.create = MagicMock(return_value=mock_glide_client)
        config_cls = MagicMock()

        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(GlideClient=glide_client_cls, GlideClientConfiguration=config_cls)},
        ):
            store._connect()

        assert store._client is mock_glide_client
        config_cls.assert_called_once()

    def test_connect_with_tls(self):
        store = ValkeyVectorStore(host="remote.host", port=6380, use_tls=True)
        config_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(GlideClientConfiguration=config_cls)},
        ):
            store._connect()
        assert config_cls.call_args[1]["use_tls"] is True

    def test_connect_with_password(self):
        store = ValkeyVectorStore(host="localhost", port=6379, password="secret123", use_tls=True)
        config_cls = MagicMock()
        creds_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(GlideClientConfiguration=config_cls, ServerCredentials=creds_cls)},
        ):
            store._connect()
        creds_cls.assert_called_once_with(password="secret123")
        assert "credentials" in config_cls.call_args[1]

    def test_connect_password_without_tls_warns(self, caplog):
        store = ValkeyVectorStore(host="localhost", port=6379, password="secret123", use_tls=False)
        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock()}):
            with patch("metagpt.rag.vector_stores.valkey.logger") as mock_logger:
                store._connect()
        assert mock_logger.warning.called
        assert "cleartext" in mock_logger.warning.call_args[0][0]

    def test_request_timeout_configurable(self):
        store = ValkeyVectorStore(request_timeout=10000)
        config_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(GlideClientConfiguration=config_cls)},
        ):
            store._connect()
        assert config_cls.call_args[1]["request_timeout"] == 10000

    def test_client_name_set(self):
        store = ValkeyVectorStore(client_name="metagpt_rag_client")
        config_cls = MagicMock()
        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(GlideClientConfiguration=config_cls)},
        ):
            store._connect()
        assert config_cls.call_args[1]["client_name"] == "metagpt_rag_client"


class TestValkeyPasswordRedaction:
    def test_password_not_in_repr(self):
        store = ValkeyVectorStore(password="topsecret")
        assert "topsecret" not in repr(store)

    def test_none_password_not_redacted_label(self):
        store = ValkeyVectorStore()
        # With no password set, repr should not contain the redaction marker for password.
        assert "topsecret" not in repr(store)


class TestValkeyVectorStoreIndex:
    def test_ensure_index_creates_when_absent(self, store, mock_client):
        store._client = mock_client
        ft = MagicMock()
        ft.list = MagicMock(return_value=[])  # index not present
        ft.create = MagicMock()

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            store.ensure_index()

        ft.create.assert_called_once()
        assert ft.create.call_args[0][1] == "test_index"

    def test_ensure_index_skips_when_present(self, store, mock_client):
        store._client = mock_client
        ft = MagicMock()
        ft.list = MagicMock(return_value=[b"test_index"])
        ft.create = MagicMock()

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            store.ensure_index()

        ft.create.assert_not_called()

    def test_ensure_index_connects_if_needed(self, store):
        # _client is None -> ensure_index must call _connect first (temporal-coupling guard).
        ft = MagicMock()
        ft.list = MagicMock(return_value=[b"test_index"])
        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            with patch.object(ValkeyVectorStore, "_connect", autospec=True) as mock_connect:

                def _set_client(self):
                    self._client = MagicMock()

                mock_connect.side_effect = _set_client
                store.ensure_index()
        mock_connect.assert_called_once()


class TestValkeyVectorStoreOperations:
    def test_add_nodes_batch_atomic(self, store, mock_client):
        store._client = mock_client
        json_batch = MagicMock()
        batch_cls = MagicMock()

        nodes = [
            TextNode(text="hello world", embedding=[0.1, 0.2, 0.3, 0.4], id_="doc1"),
            TextNode(text="foo bar", embedding=[0.5, 0.6, 0.7, 0.8], id_="doc2"),
        ]

        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(json_batch=json_batch, Batch=batch_cls)},
        ):
            ids = store.add(nodes)

        assert ids == ["doc1", "doc2"]
        # One atomic exec for the single chunk, two JSON.SET enqueues.
        mock_client.exec.assert_called_once()
        assert json_batch.set.call_count == 2

    def test_add_nodes_failure_reports_written_count(self, store, mock_client):
        store._client = mock_client
        mock_client.exec.side_effect = Exception("Write failure")
        json_batch = MagicMock()
        batch_cls = MagicMock()

        nodes = [TextNode(text="hello", embedding=[0.1, 0.2, 0.3, 0.4], id_="doc1")]

        with patch.dict(
            "sys.modules",
            {"glide_sync": _glide_sync_mock(json_batch=json_batch, Batch=batch_cls)},
        ):
            with pytest.raises(RuntimeError, match="0 document"):
                store.add(nodes)

    def test_query_knn(self, store, mock_client):
        store._client = mock_client
        results = [
            1,
            {
                b"test:rag:doc1": {
                    b"text": b"hello",
                    b"metadata": b"{}",
                    b"doc_id": b"doc1",
                    b"score": b"0.1",
                }
            },
        ]
        ft = MagicMock()
        ft.search = MagicMock(return_value=results)

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3, 0.4], similarity_top_k=5)
            result = store.query(query)

        assert len(result.nodes) == 1
        assert result.nodes[0].text == "hello"
        assert result.ids[0] == "doc1"
        # COSINE: similarity = 1 - 0.1
        assert abs(result.similarities[0] - 0.9) < 1e-6
        ft.search.assert_called_once()

    def test_query_empty_results(self, store, mock_client):
        store._client = mock_client
        ft = MagicMock()
        ft.search = MagicMock(return_value=[0])

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3, 0.4], similarity_top_k=5)
            result = store.query(query)

        assert len(result.nodes) == 0
        assert len(result.similarities) == 0

    def test_query_dimension_mismatch_raises(self, store, mock_client):
        store._client = mock_client
        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock()}):
            query = VectorStoreQuery(query_embedding=[0.1, 0.2], similarity_top_k=5)
            with pytest.raises(ValueError, match="does not match"):
                store.query(query)

    def test_query_malformed_metadata_logs_and_defaults(self, store, mock_client):
        store._client = mock_client
        results = [
            1,
            {
                b"k": {
                    b"text": b"t",
                    b"metadata": b"{not json",
                    b"doc_id": b"d1",
                    b"score": b"0.2",
                }
            },
        ]
        ft = MagicMock()
        ft.search = MagicMock(return_value=results)
        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            with patch("metagpt.rag.vector_stores.valkey.logger") as mock_logger:
                query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3, 0.4], similarity_top_k=1)
                result = store.query(query)
        assert result.nodes[0].metadata == {}
        assert mock_logger.warning.called

    def test_delete_by_ref_doc_id_removes_matching_chunks(self, store, mock_client):
        store._client = mock_client
        # Two stored chunks share ref_doc_id "src1"; one belongs to another source.
        glide_json = MagicMock()

        # _iter_prefix_keys yields one batch of three keys.
        def fake_scan(cursor, match=None, count=None):
            return (b"0", [b"test:rag:a", b"test:rag:b", b"test:rag:c"])

        mock_client.scan.side_effect = fake_scan

        def fake_get(client, key, path):
            mapping = {
                "test:rag:a": b'[{"doc_id":"a","ref_doc_id":"src1"}]',
                "test:rag:b": b'[{"doc_id":"b","ref_doc_id":"src1"}]',
                "test:rag:c": b'[{"doc_id":"c","ref_doc_id":"src2"}]',
            }
            return mapping[key]

        glide_json.get.side_effect = fake_get

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(glide_json=glide_json)}):
            store.delete("src1")

        deleted_keys = mock_client.delete.call_args[0][0]
        assert set(deleted_keys) == {"test:rag:a", "test:rag:b"}

    def test_delete_fallback_to_direct_key(self, store, mock_client):
        store._client = mock_client
        glide_json = MagicMock()
        mock_client.scan.side_effect = lambda cursor, match=None, count=None: (b"0", [])

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(glide_json=glide_json)}):
            store.delete("orphan")

        mock_client.delete.assert_called_once_with(["test:rag:orphan"])

    def test_drop_index_cleans_orphaned_keys(self, store, mock_client):
        store._client = mock_client
        ft = MagicMock()
        ft.list = MagicMock(return_value=[b"test_index"])
        ft.dropindex = MagicMock()
        # SCAN: one batch then cursor 0
        mock_client.scan.side_effect = [(b"0", [b"test:rag:doc1", b"test:rag:doc2"])]

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            store.drop_index()

        ft.dropindex.assert_called_once()
        mock_client.delete.assert_called_once()

    def test_drop_index_absent_still_cleans_keys(self, store, mock_client):
        store._client = mock_client
        ft = MagicMock()
        ft.list = MagicMock(return_value=[])  # index absent
        ft.dropindex = MagicMock()
        mock_client.scan.side_effect = [(b"0", [b"test:rag:orphan1"])]

        with patch.dict("sys.modules", {"glide_sync": _glide_sync_mock(ft=ft)}):
            store.drop_index()

        ft.dropindex.assert_not_called()
        mock_client.delete.assert_called_once()

    def test_check_connection_disconnects_on_failure(self, store, mock_client):
        store._client = mock_client
        mock_client.ping.side_effect = ConnectionError("Connection refused")

        result = store.check_connection()

        assert result is False
        mock_client.close.assert_called_once()
        assert store._client is None

    def test_scan_max_iterations_safety(self, store, mock_client):
        """Verify SCAN loop is bounded by _MAX_SCAN_ITERATIONS and never spins forever."""
        from metagpt.rag.vector_stores import valkey as valkey_mod

        # Always non-zero cursor + one key -> would loop forever without the guard.
        mock_client.scan.return_value = (b"1", [b"test:rag:doc"])
        store._client = mock_client

        original_limit = valkey_mod._MAX_SCAN_ITERATIONS
        valkey_mod._MAX_SCAN_ITERATIONS = 5
        try:
            keys = store.scan_all_docs()
        finally:
            valkey_mod._MAX_SCAN_ITERATIONS = original_limit

        assert len(keys) <= 5
