"""Valkey Vector Store implementation using valkey-glide."""

import asyncio
import json
import struct
import threading
from typing import Any, List, Optional

from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from pydantic.v1 import Field, PrivateAttr

from metagpt.logs import logger

_MAX_SCAN_ITERATIONS = 10000
_BATCH_SIZE = 100

_TAG_SPECIAL_CHARS = set(",.<>{}[]\"':;!@#$%^&*()-+=~|")
_PHRASE_SPECIAL_CHARS = set(",.<>{}[]\"':;!@#$%^&*()-+=~|")


class _PersistentLoop:
    """A single persistent event loop running on a dedicated background thread.

    All sync-over-async calls dispatch to this one loop so that any cached
    GlideClient always operates on the same loop it was created on. Using a
    fresh ``asyncio.run`` per call would close the loop and invalidate the
    cached client on subsequent calls.
    """

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def _ensure_started(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is None or not self._loop.is_running():
                self._loop = asyncio.new_event_loop()
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
            return self._loop

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run(self, coro):
        """Run a coroutine to completion on the persistent loop and return its result."""
        loop = self._ensure_started()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()


_PERSISTENT_LOOP = _PersistentLoop()


def _escape_tag(value: str) -> str:
    """Escape special characters for Valkey tag field queries."""
    return "".join(f"\\{c}" if c in _TAG_SPECIAL_CHARS else c for c in value)


def _escape_phrase(value: str) -> str:
    """Escape special characters for Valkey phrase queries."""
    return "".join(f"\\{c}" if c in _PHRASE_SPECIAL_CHARS else c for c in value)


def _run_async(coro):
    """Run an async coroutine from a sync context on a single persistent event loop.

    All coroutines are dispatched to one long-lived loop on a dedicated thread via
    ``run_coroutine_threadsafe``. This guarantees a cached GlideClient always runs on
    the loop it was created on, even across multiple sequential sync calls.
    """
    return _PERSISTENT_LOOP.run(coro)


class ValkeyVectorStore(BasePydanticVectorStore):
    """Valkey-based vector store using valkey-glide and Valkey Search module."""

    stores_text: bool = True
    flat_metadata: bool = True

    host: str = Field(default="localhost", description="Valkey server host.")
    port: int = Field(default=6379, description="Valkey server port.")
    password: Optional[str] = Field(default=None, description="Valkey server password.")
    use_tls: bool = Field(default=False, description="Whether to use TLS for connection.")
    request_timeout: int = Field(default=5000, description="Request timeout in milliseconds.")
    index_name: str = Field(default="metagpt_rag", description="Name of the Valkey Search index.")
    prefix: str = Field(default="metagpt:rag:", description="Key prefix for stored documents.")
    vector_dimensions: int = Field(default=1536, description="Dimensionality of embedding vectors.")
    distance_metric: str = Field(default="COSINE", description="Distance metric: COSINE, L2, or IP.")
    vector_algorithm: str = Field(default="HNSW", description="Vector index algorithm: HNSW or FLAT.")
    client_name: str = Field(default="metagpt_rag_client", description="Client name for Valkey connection.")

    _client: Any = PrivateAttr(default=None)

    @property
    def client(self) -> Any:
        """Get the underlying Valkey client."""
        return self._client

    async def _connect(self) -> None:
        """Create a GlideClient connection to Valkey."""
        from glide import GlideClient, GlideClientConfiguration, NodeAddress, ServerCredentials

        addresses = [NodeAddress(host=self.host, port=self.port)]
        config_kwargs = {
            "addresses": addresses,
            "client_name": self.client_name,
            "use_tls": self.use_tls,
            "request_timeout": self.request_timeout,
        }

        if self.password:
            config_kwargs["credentials"] = ServerCredentials(password=self.password)

        config = GlideClientConfiguration(**config_kwargs)
        self._client = await GlideClient.create(config)

        logger.info("Connected to Valkey at %s:%s", self.host, self.port)

    async def _ensure_index(self) -> None:
        """Create the FT.SEARCH index if it does not already exist."""
        from glide import (
            DataType,
            DistanceMetricType,
            FtCreateOptions,
            TextField,
            VectorAlgorithm,
            VectorField,
            VectorFieldAttributesFlat,
            VectorFieldAttributesHnsw,
            VectorType,
            ft,
        )

        distance_map = {
            "COSINE": DistanceMetricType.COSINE,
            "L2": DistanceMetricType.L2,
            "IP": DistanceMetricType.IP,
        }
        algorithm_map = {
            "HNSW": VectorAlgorithm.HNSW,
            "FLAT": VectorAlgorithm.FLAT,
        }

        distance = distance_map.get(self.distance_metric.upper(), DistanceMetricType.COSINE)
        algorithm = algorithm_map.get(self.vector_algorithm.upper(), VectorAlgorithm.HNSW)

        # Select the attribute class that matches the chosen algorithm so that
        # FLAT indexes are not incorrectly created with HNSW parameters.
        if algorithm == VectorAlgorithm.FLAT:
            attributes = VectorFieldAttributesFlat(
                dimensions=self.vector_dimensions,
                distance_metric=distance,
                type=VectorType.FLOAT32,
            )
        else:
            attributes = VectorFieldAttributesHnsw(
                dimensions=self.vector_dimensions,
                distance_metric=distance,
                type=VectorType.FLOAT32,
            )

        schema = [
            TextField("$.text", "text"),
            TextField("$.doc_id", "doc_id"),
            TextField("$.metadata", "metadata"),
            VectorField(
                name="$.vector",
                alias="vector",
                algorithm=algorithm,
                attributes=attributes,
            ),
        ]

        options = FtCreateOptions(DataType.JSON, prefixes=[self.prefix])

        try:
            await ft.create(self._client, self.index_name, schema=schema, options=options)
            logger.info("Created Valkey search index: %s", self.index_name)
        except Exception as e:
            error_msg = str(e)
            if "Index already exists" in error_msg:
                logger.debug("Index %s already exists, skipping creation", self.index_name)
            else:
                raise

    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Add nodes to the vector store."""
        return _run_async(self._async_add(nodes, **add_kwargs))

    async def _async_add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Async implementation of add nodes."""
        if self._client is None:
            await self._connect()
            await self._ensure_index()

        ids = []
        # Batch processing
        for i in range(0, len(nodes), _BATCH_SIZE):
            batch = nodes[i : i + _BATCH_SIZE]
            tasks = []
            for node in batch:
                doc_id = node.node_id
                embedding = node.get_embedding()
                text = node.get_content(metadata_mode=MetadataMode.NONE) or ""
                metadata = node.metadata or {}

                doc_data = {
                    "doc_id": doc_id,
                    "text": text,
                    "metadata": json.dumps(metadata),
                    "vector": list(embedding),
                }

                key = f"{self.prefix}{doc_id}"
                tasks.append(self._client.custom_command(["JSON.SET", key, "$", json.dumps(doc_data)]))
                ids.append(doc_id)

            # Gather with exception propagation
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    raise result

        logger.info("Added %s documents to Valkey index %s", len(ids), self.index_name)
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """Delete a document by ref_doc_id."""
        _run_async(self._async_delete(ref_doc_id, **delete_kwargs))

    async def _async_delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """Async implementation of delete."""
        if self._client is None:
            await self._connect()

        key = f"{self.prefix}{ref_doc_id}"
        await self._client.custom_command(["DEL", key])
        logger.debug("Deleted document %s from Valkey", ref_doc_id)

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Query the vector store."""
        return _run_async(self._async_query(query, **kwargs))

    async def _async_query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Async implementation of query."""
        from glide import FtSearchOptions, ReturnField, ft

        if self._client is None:
            await self._connect()
            await self._ensure_index()

        top_k = query.similarity_top_k or 5
        query_embedding = query.query_embedding

        vector_bytes = struct.pack(f"{len(query_embedding)}f", *query_embedding)

        # KNN query using FT.SEARCH
        ft_query = f"*=>[KNN {top_k} @vector $query_vec AS score]"
        options = FtSearchOptions(
            return_fields=[
                ReturnField("text"),
                ReturnField("metadata"),
                ReturnField("doc_id"),
                ReturnField("score"),
            ],
            params={"query_vec": vector_bytes},
        )

        results = await ft.search(self._client, self.index_name, ft_query, options=options)

        nodes = []
        similarities = []
        ids = []

        # Parse results format: [total_count, {key: {field: value, ...}}, ...]
        if results and len(results) > 1:
            for entry in results[1:]:
                if isinstance(entry, dict):
                    for key, field_dict in entry.items():
                        if isinstance(field_dict, dict):
                            # Decode bytes to strings
                            decoded = {}
                            for fk, fv in field_dict.items():
                                k_str = fk.decode("utf-8") if isinstance(fk, bytes) else str(fk)
                                v_str = fv.decode("utf-8") if isinstance(fv, bytes) else str(fv)
                                decoded[k_str] = v_str

                            text = decoded.get("text", "")
                            doc_id = decoded.get("doc_id", "")
                            metadata_str = decoded.get("metadata", "{}")
                            score_str = decoded.get("score", "0")

                            try:
                                metadata = json.loads(metadata_str)
                            except (json.JSONDecodeError, TypeError):
                                # Handle escaped JSON from JSON path retrieval
                                try:
                                    unescaped = metadata_str.replace('\\"', '"')
                                    metadata = json.loads(unescaped)
                                except (json.JSONDecodeError, TypeError):
                                    metadata = {}

                            try:
                                score = float(score_str)
                                # Convert distance to similarity
                                if self.distance_metric.upper() == "COSINE":
                                    similarity = 1.0 - score
                                else:
                                    similarity = -score
                            except (ValueError, TypeError):
                                similarity = 0.0

                            node = TextNode(
                                id_=doc_id,
                                text=text,
                                metadata=metadata,
                            )
                            nodes.append(node)
                            similarities.append(similarity)
                            ids.append(doc_id)

        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

    async def check_connection(self) -> bool:
        """Check if the Valkey connection is alive."""
        try:
            if self._client is None:
                await self._connect()
            await self._client.custom_command(["PING"])
            return True
        except Exception as e:
            logger.error("Valkey connection check failed: %s", e)
            await self.disconnect()
            return False

    async def disconnect(self) -> None:
        """Disconnect from Valkey."""
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                pass
            self._client = None

    async def drop_index(self) -> None:
        """Drop the search index and clean up all associated keys."""
        if self._client is None:
            await self._connect()

        from glide import ft

        # Try to drop the index
        try:
            await ft.dropindex(self._client, self.index_name)
            logger.info("Dropped Valkey search index: %s", self.index_name)
        except Exception as e:
            error_msg = str(e)
            if "Unknown Index name" in error_msg or "Unknown index" in error_msg.lower():
                logger.debug("Index %s not found, proceeding to clean orphaned keys", self.index_name)
            else:
                raise

        # Always clean up orphaned keys with prefix
        await self._cleanup_prefix_keys()

    async def _iter_prefix_keys(self, max_keys: Optional[int] = None):
        """Yield batches of keys matching the configured prefix via SCAN.

        Bounded by _MAX_SCAN_ITERATIONS to guard against unbounded keyspaces.
        Stops early once max_keys keys have been yielded in total.
        """
        cursor = "0"
        iterations = 0
        yielded = 0

        while iterations < _MAX_SCAN_ITERATIONS:
            result = await self._client.custom_command(["SCAN", cursor, "MATCH", f"{self.prefix}*", "COUNT", "100"])
            if not (isinstance(result, (list, tuple)) and len(result) == 2):
                break

            cursor_val, found_keys = result[0], result[1]
            cursor = cursor_val.decode("utf-8") if isinstance(cursor_val, bytes) else str(cursor_val)

            if found_keys:
                batch = [k.decode("utf-8") if isinstance(k, bytes) else str(k) for k in found_keys]
                if max_keys is not None and yielded + len(batch) >= max_keys:
                    yield batch[: max_keys - yielded]
                    return
                yielded += len(batch)
                yield batch

            if cursor == "0":
                break

            iterations += 1

    async def _cleanup_prefix_keys(self) -> None:
        """Remove all keys with the configured prefix using SCAN with safety limit."""
        total_deleted = 0

        async for batch in self._iter_prefix_keys():
            if batch:
                await self._client.custom_command(["DEL", *batch])
                total_deleted += len(batch)

        if total_deleted > 0:
            logger.info("Cleaned up %s orphaned keys with prefix %s", total_deleted, self.prefix)

    async def _scan_all_docs(self, max_keys: Optional[int] = None) -> List[str]:
        """Scan all document keys with the configured prefix.

        Terminates early once max_keys are collected or _MAX_SCAN_ITERATIONS reached.
        """
        keys: List[str] = []
        async for batch in self._iter_prefix_keys(max_keys=max_keys):
            keys.extend(batch)
        return keys
