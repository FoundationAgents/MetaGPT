"""Unit tests for ValkeyVectorStore with mocked valkey-glide client."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import VectorStoreQuery

from metagpt.rag.vector_stores.valkey import (
    ValkeyVectorStore,
    _escape_phrase,
    _escape_tag,
)


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
    client = AsyncMock()
    client.custom_command = AsyncMock()
    client.close = AsyncMock()
    return client


class TestValkeyVectorStoreConnection:
    @pytest.mark.asyncio
    async def test_connect_success(self, store, mocker):
        mock_glide_client = AsyncMock()
        mock_glide_client_cls = MagicMock()
        mock_glide_client_cls.create = AsyncMock(return_value=mock_glide_client)
        mock_config_cls = MagicMock()
        mock_node_address = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    GlideClient=mock_glide_client_cls,
                    GlideClientConfiguration=mock_config_cls,
                    NodeAddress=mock_node_address,
                ),
            },
        ):
            await store._connect()

        assert store._client == mock_glide_client
        mock_config_cls.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_with_tls(self, mocker):
        store = ValkeyVectorStore(host="remote.host", port=6380, use_tls=True)
        mock_glide_client = AsyncMock()
        mock_glide_client_cls = MagicMock()
        mock_glide_client_cls.create = AsyncMock(return_value=mock_glide_client)
        mock_config_cls = MagicMock()
        mock_node_address = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    GlideClient=mock_glide_client_cls,
                    GlideClientConfiguration=mock_config_cls,
                    NodeAddress=mock_node_address,
                ),
            },
        ):
            await store._connect()

        config_call_kwargs = mock_config_cls.call_args[1]
        assert config_call_kwargs["use_tls"] is True

    @pytest.mark.asyncio
    async def test_connect_with_password(self, mocker):
        store = ValkeyVectorStore(host="localhost", port=6379, password="secret123")
        mock_glide_client = AsyncMock()
        mock_glide_client_cls = MagicMock()
        mock_glide_client_cls.create = AsyncMock(return_value=mock_glide_client)
        mock_config_cls = MagicMock()
        mock_node_address = MagicMock()
        mock_server_credentials = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    GlideClient=mock_glide_client_cls,
                    GlideClientConfiguration=mock_config_cls,
                    NodeAddress=mock_node_address,
                    ServerCredentials=mock_server_credentials,
                ),
            },
        ):
            await store._connect()

        # Password should be passed via ServerCredentials in config, not via AUTH command
        mock_server_credentials.assert_called_once_with(password="secret123")
        config_call_kwargs = mock_config_cls.call_args[1]
        assert "credentials" in config_call_kwargs

    @pytest.mark.asyncio
    async def test_request_timeout_configurable(self, mocker):
        store = ValkeyVectorStore(request_timeout=10000)
        mock_glide_client = AsyncMock()
        mock_glide_client_cls = MagicMock()
        mock_glide_client_cls.create = AsyncMock(return_value=mock_glide_client)
        mock_config_cls = MagicMock()
        mock_node_address = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    GlideClient=mock_glide_client_cls,
                    GlideClientConfiguration=mock_config_cls,
                    NodeAddress=mock_node_address,
                ),
            },
        ):
            await store._connect()

        config_call_kwargs = mock_config_cls.call_args[1]
        assert config_call_kwargs["request_timeout"] == 10000

    @pytest.mark.asyncio
    async def test_client_name_set(self, mocker):
        store = ValkeyVectorStore(client_name="metagpt_rag_client")
        mock_glide_client = AsyncMock()
        mock_glide_client_cls = MagicMock()
        mock_glide_client_cls.create = AsyncMock(return_value=mock_glide_client)
        mock_config_cls = MagicMock()
        mock_node_address = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    GlideClient=mock_glide_client_cls,
                    GlideClientConfiguration=mock_config_cls,
                    NodeAddress=mock_node_address,
                ),
            },
        ):
            await store._connect()

        config_call_kwargs = mock_config_cls.call_args[1]
        assert config_call_kwargs["client_name"] == "metagpt_rag_client"


class TestValkeyVectorStoreIndex:
    @pytest.mark.asyncio
    async def test_ensure_index_creates_ft_index(self, store, mock_client, mocker):
        store._client = mock_client
        mock_ft_create = AsyncMock()
        mock_ft_module = MagicMock()
        mock_ft_module.create = mock_ft_create

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    DataType=MagicMock(),
                    DistanceMetricType=MagicMock(COSINE="COSINE", L2="L2", INNER_PRODUCT="IP"),
                    FtCreateOptions=MagicMock(),
                    TextField=MagicMock(),
                    VectorAlgorithm=MagicMock(HNSW="HNSW", FLAT="FLAT"),
                    VectorField=MagicMock(),
                    VectorFieldAttributesHnsw=MagicMock(),
                    VectorType=MagicMock(FLOAT32="FLOAT32"),
                    ft=mock_ft_module,
                ),
            },
        ):
            await store._ensure_index()

        mock_ft_create.assert_called_once()
        args = mock_ft_create.call_args
        assert args[0][1] == "test_index"  # index_name

    @pytest.mark.asyncio
    async def test_ensure_index_already_exists(self, store, mock_client, mocker):
        store._client = mock_client
        mock_ft_create = AsyncMock(side_effect=Exception("Index already exists"))
        mock_ft_module = MagicMock()
        mock_ft_module.create = mock_ft_create

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(
                    DataType=MagicMock(),
                    DistanceMetricType=MagicMock(COSINE="COSINE", L2="L2", INNER_PRODUCT="IP"),
                    FtCreateOptions=MagicMock(),
                    TextField=MagicMock(),
                    VectorAlgorithm=MagicMock(HNSW="HNSW", FLAT="FLAT"),
                    VectorField=MagicMock(),
                    VectorFieldAttributesHnsw=MagicMock(),
                    VectorType=MagicMock(FLOAT32="FLOAT32"),
                    ft=mock_ft_module,
                ),
            },
        ):
            # Should not raise
            await store._ensure_index()


class TestValkeyVectorStoreOperations:
    @pytest.mark.asyncio
    async def test_add_nodes_batch(self, store, mock_client):
        store._client = mock_client
        mock_client.custom_command.return_value = b"OK"

        nodes = [
            TextNode(text="hello world", embedding=[0.1, 0.2, 0.3, 0.4], id_="doc1"),
            TextNode(text="foo bar", embedding=[0.5, 0.6, 0.7, 0.8], id_="doc2"),
        ]

        ids = await store._async_add(nodes)

        assert len(ids) == 2
        assert "doc1" in ids
        assert "doc2" in ids
        # Two JSON.SET calls
        assert mock_client.custom_command.call_count == 2

    @pytest.mark.asyncio
    async def test_add_nodes_partial_failure_raises(self, store, mock_client):
        store._client = mock_client
        mock_client.custom_command.side_effect = [b"OK", Exception("Write failure")]

        nodes = [
            TextNode(text="hello", embedding=[0.1, 0.2, 0.3, 0.4], id_="doc1"),
            TextNode(text="world", embedding=[0.5, 0.6, 0.7, 0.8], id_="doc2"),
        ]

        with pytest.raises(Exception, match="Write failure"):
            await store._async_add(nodes)

    @pytest.mark.asyncio
    async def test_query_knn(self, store, mock_client, mocker):
        store._client = mock_client
        # Mock FT.SEARCH results: [total, {key: {field: value}}]
        mock_results = [
            1,
            {b"test:rag:doc1": {b"text": b"hello", b"metadata": b"{}", b"doc_id": b"doc1", b"score": b"0.1"}},
        ]

        mock_ft_search = AsyncMock(return_value=mock_results)
        mock_ft_module = MagicMock()
        mock_ft_module.search = mock_ft_search

        mock_return_field = MagicMock()
        mock_ft_search_options = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(FtSearchOptions=mock_ft_search_options, ft=mock_ft_module),
                "glide_shared": MagicMock(),
                "glide_shared.commands": MagicMock(),
                "glide_shared.commands.server_modules": MagicMock(),
                "glide_shared.commands.server_modules.ft_options": MagicMock(),
                "glide_shared.commands.server_modules.ft_options.ft_search_options": MagicMock(
                    ReturnField=mock_return_field
                ),
            },
        ):
            query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3, 0.4], similarity_top_k=5)
            result = await store._async_query(query)

        assert len(result.nodes) == 1
        assert result.nodes[0].text == "hello"
        assert result.ids[0] == "doc1"
        mock_ft_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_empty_results(self, store, mock_client, mocker):
        store._client = mock_client
        mock_ft_search = AsyncMock(return_value=[0])
        mock_ft_module = MagicMock()
        mock_ft_module.search = mock_ft_search

        mock_return_field = MagicMock()
        mock_ft_search_options = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "glide": MagicMock(FtSearchOptions=mock_ft_search_options, ft=mock_ft_module),
                "glide_shared": MagicMock(),
                "glide_shared.commands": MagicMock(),
                "glide_shared.commands.server_modules": MagicMock(),
                "glide_shared.commands.server_modules.ft_options": MagicMock(),
                "glide_shared.commands.server_modules.ft_options.ft_search_options": MagicMock(
                    ReturnField=mock_return_field
                ),
            },
        ):
            query = VectorStoreQuery(query_embedding=[0.1, 0.2, 0.3, 0.4], similarity_top_k=5)
            result = await store._async_query(query)

        assert len(result.nodes) == 0
        assert len(result.similarities) == 0

    @pytest.mark.asyncio
    async def test_delete_by_ref_doc_id(self, store, mock_client):
        store._client = mock_client
        mock_client.custom_command.return_value = 1

        await store._async_delete("doc1")

        mock_client.custom_command.assert_called_once_with(["DEL", "test:rag:doc1"])

    @pytest.mark.asyncio
    async def test_drop_index_cleans_orphaned_keys(self, store, mock_client, mocker):
        store._client = mock_client
        mock_ft_dropindex = AsyncMock()
        mock_ft_module = MagicMock()
        mock_ft_module.dropindex = mock_ft_dropindex

        # SCAN returns some keys then cursor 0
        mock_client.custom_command.side_effect = [
            [b"0", [b"test:rag:doc1", b"test:rag:doc2"]],  # SCAN
            2,  # DEL
        ]

        with patch.dict("sys.modules", {"glide": MagicMock(ft=mock_ft_module)}):
            await store.drop_index()

        mock_ft_dropindex.assert_called_once()

    @pytest.mark.asyncio
    async def test_drop_index_not_found_still_cleans_keys(self, store, mock_client, mocker):
        store._client = mock_client
        mock_ft_dropindex = AsyncMock(side_effect=Exception("Unknown Index name"))
        mock_ft_module = MagicMock()
        mock_ft_module.dropindex = mock_ft_dropindex

        mock_client.custom_command.side_effect = [
            [b"0", [b"test:rag:orphan1"]],
            1,
        ]

        with patch.dict("sys.modules", {"glide": MagicMock(ft=mock_ft_module)}):
            # Should not raise
            await store.drop_index()

    @pytest.mark.asyncio
    async def test_check_connection_disconnects_on_failure(self, store, mock_client):
        store._client = mock_client
        mock_client.custom_command.side_effect = Exception("Connection refused")

        result = await store.check_connection()

        assert result is False
        mock_client.close.assert_called_once()
        assert store._client is None

    @pytest.mark.asyncio
    async def test_scan_max_iterations_safety(self, store, mock_client):
        """Verify SCAN loop is bounded by _MAX_SCAN_ITERATIONS and never spins forever."""
        from metagpt.rag.vector_stores import valkey as valkey_mod

        # SCAN always returns a non-zero cursor and one key -> would loop forever without the guard.
        mock_client.custom_command.return_value = [b"1", [b"test:rag:doc"]]
        store._client = mock_client

        # Shrink the safety limit so the test is fast.
        original_limit = valkey_mod._MAX_SCAN_ITERATIONS
        valkey_mod._MAX_SCAN_ITERATIONS = 5
        try:
            keys = await store._scan_all_docs()
        finally:
            valkey_mod._MAX_SCAN_ITERATIONS = original_limit

        # Bounded: at most _MAX_SCAN_ITERATIONS batches of 1 key each.
        assert len(keys) <= 5


class TestValkeySyncPath:
    """Exercise the real sync-over-async path (persistent loop) across sequential calls."""

    @pytest.mark.asyncio
    async def test_sequential_sync_calls_reuse_loop(self, mocker):
        """Two sequential _run_async calls must succeed on the same persistent loop.

        Regression test: a fresh asyncio.run per call would close the loop and
        invalidate a cached client on the second call.
        """
        from metagpt.rag.vector_stores.valkey import _run_async

        async def coro(value):
            await asyncio.sleep(0)
            return value

        # Call _run_async from a worker thread (sync context) twice in a row.
        import concurrent.futures

        def sync_caller():
            first = _run_async(coro(1))
            second = _run_async(coro(2))
            return first, second

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            first, second = ex.submit(sync_caller).result()

        assert first == 1
        assert second == 2


class TestValkeyEscaping:
    def test_escape_tag_special_chars(self):
        assert _escape_tag("hello|world") == "hello\\|world"
        assert _escape_tag("a,b") == "a\\,b"
        assert _escape_tag("test.val") == "test\\.val"
        assert _escape_tag("no_special") == "no_special"

    def test_escape_phrase_special_chars(self):
        assert _escape_phrase("hello|world") == "hello\\|world"
        assert _escape_phrase("a{b}") == "a\\{b\\}"
        assert _escape_phrase("no_special") == "no_special"
