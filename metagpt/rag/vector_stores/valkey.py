"""Valkey Vector Store implementation using the synchronous valkey-glide client.

The synchronous GLIDE client (``glide_sync``, shipped as the ``valkey-glide-sync``
package) is used here to stay consistent with the other RAG backends
(FAISS / Chroma / Elasticsearch), all of which are synchronous. This avoids the
threading / event-loop bridge machinery an async client would otherwise require.
"""

import json
import struct
from typing import Any, List, Literal, Optional

from glide_sync import (
    Batch,
    DataType,
    DistanceMetricType,
    FtCreateOptions,
    FtSearchOptions,
    GlideClient,
    GlideClientConfiguration,
    NodeAddress,
    ReturnField,
    ServerCredentials,
    TextField,
    VectorAlgorithm,
    VectorField,
    VectorFieldAttributesFlat,
    VectorFieldAttributesHnsw,
    VectorType,
    ft,
    glide_json,
    json_batch,
)
from llama_index.core.schema import BaseNode, MetadataMode, TextNode
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)

# llama-index-core (0.10.x) builds BasePydanticVectorStore on pydantic.v1, so its
# subclasses must declare fields with the v1 Field/PrivateAttr. The rest of the
# codebase uses native pydantic v2; this v1 shim is required only for this base
# class and should be revisited when llama-index migrates to pydantic v2.
from pydantic.v1 import Field, PrivateAttr

from metagpt.logs import logger

_MAX_SCAN_ITERATIONS = 10000
_BATCH_SIZE = 100


class ValkeyVectorStore(BasePydanticVectorStore):
    """Valkey-based vector store using the sync valkey-glide client and Valkey Search module."""

    stores_text: bool = True
    flat_metadata: bool = True

    host: str = Field(default="localhost", description="Valkey server host.")
    port: int = Field(default=6379, description="Valkey server port.")
    password: Optional[str] = Field(default=None, description="Valkey server password.", repr=False)
    use_tls: bool = Field(default=False, description="Whether to use TLS for connection.")
    request_timeout: int = Field(default=5000, description="Request timeout in milliseconds.")
    index_name: str = Field(default="metagpt_rag", description="Name of the Valkey Search index.")
    prefix: str = Field(default="metagpt:rag:", description="Key prefix for stored documents.")
    vector_dimensions: int = Field(default=1536, description="Dimensionality of embedding vectors.")
    distance_metric: Literal["COSINE", "L2", "IP"] = Field(
        default="COSINE", description="Distance metric: COSINE, L2, or IP."
    )
    vector_algorithm: Literal["HNSW", "FLAT"] = Field(
        default="HNSW", description="Vector index algorithm: HNSW or FLAT."
    )
    client_name: str = Field(default="metagpt_rag_client", description="Client name for Valkey connection.")

    _client: Any = PrivateAttr(default=None)

    def __repr_args__(self):
        """Redact the password so it never leaks into reprs / tracebacks / logs."""
        redacted = {"password"}
        return [(k, "***" if (k in redacted and v is not None) else v) for k, v in super().__repr_args__()]

    @property
    def client(self) -> Any:
        """Get the underlying Valkey client."""
        return self._client

    def _connect(self) -> None:
        """Create a synchronous GlideClient connection to Valkey."""
        if self.password and not self.use_tls:
            logger.warning(
                "Valkey password is configured but TLS is disabled — credentials will be sent in cleartext. "
                "Set use_tls=true for any non-local deployment."
            )

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
        self._client = GlideClient.create(config)

        logger.info("Connected to Valkey at %s:%s", self.host, self.port)

    def _index_exists(self) -> bool:
        """Return True if the configured index already exists, using FT._LIST.

        Uses ft.list() rather than try/except + error-string matching, which is
        fragile against server-version message changes and can swallow unrelated errors.
        """
        existing = ft.list(self._client)
        names = {i.decode() if isinstance(i, (bytes, bytearray)) else str(i) for i in (existing or [])}
        return self.index_name in names

    def ensure_index(self) -> None:
        """Create the FT.SEARCH index if it does not already exist.

        Guards its own connection so callers cannot misuse it before _connect().
        """
        if self._client is None:
            self._connect()

        if self._index_exists():
            logger.debug("Index %s already exists, skipping creation", self.index_name)
            return

        distance_map = {
            "COSINE": DistanceMetricType.COSINE,
            "L2": DistanceMetricType.L2,
            "IP": DistanceMetricType.IP,
        }
        algorithm_map = {
            "HNSW": VectorAlgorithm.HNSW,
            "FLAT": VectorAlgorithm.FLAT,
        }

        distance = distance_map[self.distance_metric.upper()]
        algorithm = algorithm_map[self.vector_algorithm.upper()]

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
            TextField("$.ref_doc_id", "ref_doc_id"),
            TextField("$.metadata", "metadata"),
            VectorField(
                name="$.vector",
                alias="vector",
                algorithm=algorithm,
                attributes=attributes,
            ),
        ]

        options = FtCreateOptions(DataType.JSON, prefixes=[self.prefix])
        ft.create(self._client, self.index_name, schema=schema, options=options)
        logger.info("Created Valkey search index: %s", self.index_name)

    def add(self, nodes: List[BaseNode], **add_kwargs: Any) -> List[str]:
        """Add nodes to the vector store.

        Each chunk of up to ``_BATCH_SIZE`` JSON.SET writes is sent as a single
        atomic GLIDE transaction (one round-trip, all-or-nothing). On failure the
        raised error reports how many documents were durably written, so callers
        can retry without re-inserting duplicates.
        """
        if self._client is None:
            self._connect()
            self.ensure_index()

        ids: List[str] = []
        written = 0
        for i in range(0, len(nodes), _BATCH_SIZE):
            chunk = nodes[i : i + _BATCH_SIZE]
            batch = Batch(is_atomic=True)
            chunk_ids: List[str] = []
            for node in chunk:
                doc_id = node.node_id
                embedding = node.get_embedding()
                text = node.get_content(metadata_mode=MetadataMode.NONE) or ""
                metadata = node.metadata or {}

                doc_data = {
                    "doc_id": doc_id,
                    "ref_doc_id": node.ref_doc_id or doc_id,
                    "text": text,
                    "metadata": json.dumps(metadata),
                    "vector": list(embedding),
                }

                key = f"{self.prefix}{doc_id}"
                json_batch.set(batch, key, "$", json.dumps(doc_data))
                chunk_ids.append(doc_id)

            try:
                self._client.exec(batch, raise_on_error=True)
            except Exception as e:
                raise RuntimeError(
                    f"Valkey batch insert failed after {written} document(s) were written "
                    f"(failing chunk offset {i}, size {len(chunk)}): {e}"
                ) from e

            written += len(chunk_ids)
            ids.extend(chunk_ids)

        logger.info("Added %s documents to Valkey index %s", len(ids), self.index_name)
        return ids

    def delete(self, ref_doc_id: str, **delete_kwargs: Any) -> None:
        """Delete all nodes belonging to a source document.

        In llama-index, ``ref_doc_id`` is the source-document id and a single
        source may be chunked into many nodes. This deletes every stored key
        whose ``ref_doc_id`` (or ``doc_id``) matches, so no orphaned chunks remain.
        """
        if self._client is None:
            self._connect()

        keys_to_delete: List[str] = []
        for batch in self._iter_prefix_keys():
            for key in batch:
                raw = glide_json.get(self._client, key, "$")
                if raw is None:
                    continue
                raw_str = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else str(raw)
                try:
                    docs = json.loads(raw_str)
                    doc = docs[0] if isinstance(docs, list) else docs
                except (json.JSONDecodeError, TypeError, IndexError):
                    continue
                if doc.get("ref_doc_id") == ref_doc_id or doc.get("doc_id") == ref_doc_id:
                    keys_to_delete.append(key)

        # Fall back to direct key deletion if nothing matched (e.g. legacy docs
        # without a stored ref_doc_id field).
        if not keys_to_delete:
            keys_to_delete = [f"{self.prefix}{ref_doc_id}"]

        deleted = self._client.delete(keys_to_delete)
        logger.debug("Deleted %s key(s) for ref_doc_id %s from Valkey", deleted, ref_doc_id)

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        """Query the vector store with a KNN vector search."""
        if self._client is None:
            self._connect()
            self.ensure_index()

        top_k = query.similarity_top_k or 5
        query_embedding = query.query_embedding or []

        if len(query_embedding) != self.vector_dimensions:
            raise ValueError(
                f"Query embedding dimension {len(query_embedding)} does not match "
                f"index dimension {self.vector_dimensions}."
            )

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

        results = ft.search(self._client, self.index_name, ft_query, options=options)

        nodes: List[TextNode] = []
        similarities: List[float] = []
        ids: List[str] = []

        # FT.SEARCH returns exactly two elements: [count, {key: {field: value}}].
        if not (isinstance(results, (list, tuple)) and len(results) >= 2):
            if results and (not isinstance(results, (list, tuple)) or len(results) != 1):
                logger.warning(
                    "Unexpected FT.SEARCH response shape for index %s: %r",
                    self.index_name,
                    results,
                )
            return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

        if not isinstance(results[0], int):
            logger.warning(
                "FT.SEARCH first element is not an int count for index %s: %r",
                self.index_name,
                results[0],
            )

        docs_dict = results[1]
        if not isinstance(docs_dict, dict):
            logger.warning(
                "FT.SEARCH payload is not a mapping for index %s: %r",
                self.index_name,
                docs_dict,
            )
            return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

        for key, field_dict in docs_dict.items():
            if not isinstance(field_dict, dict):
                continue

            decoded = {}
            for fk, fv in field_dict.items():
                k_str = fk.decode("utf-8") if isinstance(fk, (bytes, bytearray)) else str(fk)
                v_str = fv.decode("utf-8") if isinstance(fv, (bytes, bytearray)) else str(fv)
                decoded[k_str] = v_str

            doc_id = decoded.get("doc_id", "")
            text = decoded.get("text", "")
            metadata_str = decoded.get("metadata", "{}")
            score_str = decoded.get("score", "0")

            metadata = self._parse_metadata(metadata_str, doc_id)
            similarity = self._parse_similarity(score_str, doc_id)

            nodes.append(TextNode(id_=doc_id, text=text, metadata=metadata))
            similarities.append(similarity)
            ids.append(doc_id)

        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

    def _parse_metadata(self, metadata_str: str, doc_id: str) -> dict:
        """Parse stored metadata JSON, logging (not silently swallowing) corruption."""
        try:
            return json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            # Handle escaped JSON that can come back from JSON-path retrieval.
            try:
                return json.loads(metadata_str.replace('\\"', '"'))
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    "Failed to parse metadata for doc %s, raw: %s",
                    doc_id,
                    str(metadata_str)[:200],
                )
                return {}

    def _parse_similarity(self, score_str: str, doc_id: str) -> float:
        """Convert a FT.SEARCH distance score into a similarity, logging parse failures."""
        try:
            score = float(score_str)
        except (ValueError, TypeError):
            logger.warning(
                "Failed to parse score for doc %s, raw: %s",
                doc_id,
                str(score_str)[:200],
            )
            return 0.0
        if self.distance_metric.upper() == "COSINE":
            return 1.0 - score
        return -score

    def check_connection(self) -> bool:
        """Check if the Valkey connection is alive."""
        try:
            if self._client is None:
                self._connect()
            self._client.ping()
            return True
        except (ConnectionError, OSError, TimeoutError) as e:
            logger.error("Valkey connection check failed: %s", e)
            self.disconnect()
            return False

    def disconnect(self) -> None:
        """Disconnect from Valkey."""
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

    def drop_index(self) -> None:
        """Drop the search index and clean up all associated keys."""
        if self._client is None:
            self._connect()

        if self._index_exists():
            ft.dropindex(self._client, self.index_name)
            logger.info("Dropped Valkey search index: %s", self.index_name)
        else:
            logger.debug("Index %s not found, proceeding to clean orphaned keys", self.index_name)

        # Always clean up orphaned keys with prefix
        self._cleanup_prefix_keys()

    def _iter_prefix_keys(self, max_keys: Optional[int] = None):
        """Yield batches of keys matching the configured prefix via SCAN.

        Bounded by _MAX_SCAN_ITERATIONS to guard against unbounded keyspaces.
        Stops early once max_keys keys have been yielded in total.
        """
        cursor = "0"
        iterations = 0
        yielded = 0

        while iterations < _MAX_SCAN_ITERATIONS:
            cursor_val, found_keys = self._client.scan(cursor, match=f"{self.prefix}*", count=100)
            cursor = cursor_val.decode("utf-8") if isinstance(cursor_val, (bytes, bytearray)) else str(cursor_val)

            if found_keys:
                batch = [k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else str(k) for k in found_keys]
                if max_keys is not None and yielded + len(batch) >= max_keys:
                    yield batch[: max_keys - yielded]
                    return
                yielded += len(batch)
                yield batch

            if cursor == "0":
                break

            iterations += 1

    def _cleanup_prefix_keys(self) -> None:
        """Remove all keys with the configured prefix using SCAN with safety limit."""
        total_deleted = 0

        for batch in self._iter_prefix_keys():
            if batch:
                self._client.delete(batch)
                total_deleted += len(batch)

        if total_deleted > 0:
            logger.info("Cleaned up %s orphaned keys with prefix %s", total_deleted, self.prefix)

    def scan_all_docs(self, max_keys: Optional[int] = None) -> List[str]:
        """Scan all document keys with the configured prefix.

        Terminates early once max_keys are collected or _MAX_SCAN_ITERATIONS reached.
        """
        keys: List[str] = []
        for batch in self._iter_prefix_keys(max_keys=max_keys):
            keys.extend(batch)
        return keys
