#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import chromadb
import numpy as np
import requests
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from qdrant_client import QdrantClient, models as qmodels
from sentence_transformers import SentenceTransformer


BEIR_DATASET_URL_PREFIX = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets"


@dataclass
class Config:
    targets: list[str]
    dataset: str
    beir_cache_dir: Path
    output_dir: Path
    collection_name: str
    embedding_model: str
    top_k: int
    max_corpus: int
    max_queries: int
    ingest_batch_size: int
    metadata_filter_track: bool
    metadata_groups: int
    cognitor_url: str
    cognitor_api_key: str | None
    qdrant_url: str
    qdrant_api_key: str | None
    weaviate_url: str


class VectorDBAdapter(Protocol):
    name: str

    def wait_ready(self) -> None:
        ...

    def recreate_collection(self, name: str, dim: int) -> None:
        ...

    def bulk_add(
        self,
        collection_name: str,
        vectors: np.ndarray,
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        ...

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        ...


class CognitorAdapter:
    name = "cognitor"

    def __init__(self, base_url: str, api_key: str | None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"X-API-Key": api_key})

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            timeout=300,
            **kwargs,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Cognitor request failed: {method} {path} -> {response.status_code} {response.text}"
            )
        if response.content:
            return response.json()
        return None

    def wait_ready(self) -> None:
        deadline = time.time() + 300
        while time.time() < deadline:
            response = self.session.get(f"{self.base_url}/health/ready", timeout=10)
            if response.status_code == 200:
                return
            time.sleep(1.0)
        raise TimeoutError("Cognitor readiness probe timed out")

    def recreate_collection(self, name: str, dim: int) -> None:
        response = self.session.delete(f"{self.base_url}/collections/{name}", timeout=60)
        if response.status_code not in (204, 404):
            raise RuntimeError(
                f"Failed to clean collection {name}: {response.status_code} {response.text}"
            )
        self._request("POST", "/collections", json={"name": name, "dim": dim})

    def bulk_add(
        self,
        collection_name: str,
        vectors: np.ndarray,
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        self._request(
            "POST",
            f"/collections/{collection_name}/documents/bulk?batch_size=1024",
            json={
                "vectors": vectors.astype(np.float32).tolist(),
                "texts": texts,
                "metadatas": metadatas,
            },
        )

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        body: dict[str, Any] = {
            "query_vector": query_vector.astype(np.float32).tolist(),
            "top_k": top_k,
            "perform_extractive_qa": False,
            "perform_reranking": False,
        }
        if metadata_filter is not None:
            body["filters"] = metadata_filter
        out = self._request("POST", f"/collections/{collection_name}/search", json=body)
        assert out is not None
        return out.get("results", [])


class QdrantAdapter:
    name = "qdrant"

    def __init__(self, url: str, api_key: str | None) -> None:
        self.client = QdrantClient(url=url, api_key=api_key, check_compatibility=False)

    def wait_ready(self) -> None:
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                _ = self.client.get_collections()
                return
            except Exception:
                time.sleep(1.0)
        raise TimeoutError("Qdrant did not become ready")

    def recreate_collection(self, name: str, dim: int) -> None:
        if self.client.collection_exists(name):
            self.client.delete_collection(name)
        self.client.create_collection(
            collection_name=name,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )

    def bulk_add(
        self,
        collection_name: str,
        vectors: np.ndarray,
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        points = []
        for vector, text, metadata in zip(vectors, texts, metadatas):
            payload = dict(metadata)
            payload["text"] = text
            points.append(
                qmodels.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector.astype(np.float32).tolist(),
                    payload=payload,
                )
            )
        self.client.upsert(collection_name=collection_name, points=points, wait=True)

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if metadata_filter is not None:
            query_filter = qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="bench_group",
                        match=qmodels.MatchValue(value=int(metadata_filter["bench_group"])),
                    )
                ]
            )

        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector.astype(np.float32).tolist(),
            limit=top_k,
            with_payload=True,
            query_filter=query_filter,
        )
        return [{"metadata": (item.payload or {})} for item in (response.points or [])]


class ChromaAdapter:
    name = "chroma"

    def __init__(self) -> None:
        self.client = chromadb.EphemeralClient()
        self.collections: dict[str, Any] = {}

    def wait_ready(self) -> None:
        return

    def recreate_collection(self, name: str, dim: int) -> None:
        _ = dim
        try:
            self.client.delete_collection(name)
        except Exception:
            pass
        self.collections[name] = self.client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def bulk_add(
        self,
        collection_name: str,
        vectors: np.ndarray,
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        collection = self.collections[collection_name]
        collection.add(
            ids=[str(uuid.uuid4()) for _ in texts],
            embeddings=vectors.astype(np.float32).tolist(),
            documents=texts,
            metadatas=metadatas,
        )

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        collection = self.collections[collection_name]
        out = collection.query(
            query_embeddings=[query_vector.astype(np.float32).tolist()],
            n_results=top_k,
            where=metadata_filter,
            include=["metadatas"],
        )
        metadatas = (out.get("metadatas") or [[]])[0]
        return [{"metadata": (metadata or {})} for metadata in metadatas]


class WeaviateAdapter:
    name = "weaviate"

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    @staticmethod
    def _class_name(name: str) -> str:
        sanitized = "".join(ch for ch in name if ch.isalnum())
        if not sanitized:
            sanitized = "Bench"
        if not sanitized[0].isalpha():
            sanitized = f"C{sanitized}"
        return sanitized[0].upper() + sanitized[1:]

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any] | None:
        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            timeout=300,
            **kwargs,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"Weaviate request failed: {method} {path} -> {response.status_code} {response.text}"
            )
        if response.content:
            return response.json()
        return None

    def wait_ready(self) -> None:
        deadline = time.time() + 180
        while time.time() < deadline:
            try:
                response = self.session.get(f"{self.base_url}/v1/.well-known/ready", timeout=5)
                if response.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(1.0)
        raise TimeoutError("Weaviate did not become ready")

    def recreate_collection(self, name: str, dim: int) -> None:
        _ = dim
        class_name = self._class_name(name)
        delete_res = self.session.delete(f"{self.base_url}/v1/schema/{class_name}", timeout=30)
        if delete_res.status_code not in (200, 404, 422):
            raise RuntimeError(
                f"Failed to delete class {class_name}: {delete_res.status_code} {delete_res.text}"
            )

        schema = {
            "class": class_name,
            "vectorizer": "none",
            "vectorIndexConfig": {"distance": "cosine"},
            "properties": [
                {"name": "beir_id", "dataType": ["text"]},
                {"name": "dataset", "dataType": ["text"]},
                {"name": "title", "dataType": ["text"]},
                {"name": "char_len", "dataType": ["int"]},
                {"name": "bench_group", "dataType": ["int"]},
                {"name": "text", "dataType": ["text"]},
            ],
        }
        self._request("POST", "/v1/schema", json=schema)

    def bulk_add(
        self,
        collection_name: str,
        vectors: np.ndarray,
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        class_name = self._class_name(collection_name)
        objects = []
        for vector, text, metadata in zip(vectors, texts, metadatas):
            props = dict(metadata)
            props["text"] = text
            objects.append(
                {
                    "class": class_name,
                    "id": str(uuid.uuid4()),
                    "properties": props,
                    "vector": vector.astype(np.float32).tolist(),
                }
            )

        response = self._request("POST", "/v1/batch/objects", json={"objects": objects})
        assert response is not None
        for item in response:
            result = item.get("result") or {}
            if result.get("errors"):
                raise RuntimeError(f"Weaviate insert error: {result['errors']}")

    def search(
        self,
        collection_name: str,
        query_vector: np.ndarray,
        top_k: int,
        metadata_filter: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        class_name = self._class_name(collection_name)
        vector_json = json.dumps(query_vector.astype(np.float32).tolist())

        where_clause = ""
        if metadata_filter is not None:
            where_clause = (
                ', where: {path: ["bench_group"], operator: Equal, valueInt: '
                f"{int(metadata_filter['bench_group'])}" + "}"
            )

        query = (
            "{ Get { "
            f"{class_name}(limit: {top_k}, nearVector: {{vector: {vector_json}}}{where_clause}) "
            "{ beir_id bench_group _additional { distance } }"
            " } }"
        )
        out = self._request("POST", "/v1/graphql", json={"query": query})
        assert out is not None
        rows = (((out.get("data") or {}).get("Get") or {}).get(class_name)) or []
        return [{"metadata": (row or {})} for row in rows]


def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="Run BEIR end-to-end benchmark across cognitor,qdrant,weaviate,chroma."
    )
    parser.add_argument(
        "--targets",
        type=str,
        default="cognitor,qdrant,weaviate,chroma",
        help="Comma-separated targets: cognitor,qdrant,weaviate,chroma",
    )
    parser.add_argument("--dataset", type=str, default="scifact")
    parser.add_argument("--beir-cache-dir", type=Path, default=Path("benchmarks/data/beir"))
    parser.add_argument("--output-dir", type=Path, default=Path("benchmarks/results"))
    parser.add_argument("--collection-name", type=str, default="beir_benchmark_collection")

    parser.add_argument("--embedding-model", type=str, default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--max-corpus", type=int, default=20000)
    parser.add_argument("--max-queries", type=int, default=1000)
    parser.add_argument("--ingest-batch-size", type=int, default=512)
    parser.add_argument("--metadata-filter-track", action="store_true")
    parser.add_argument("--metadata-groups", type=int, default=8)

    parser.add_argument("--cognitor-url", type=str, default=os.getenv("COGNITOR_URL", "http://127.0.0.1:7530"))
    parser.add_argument("--cognitor-api-key", type=str, default=os.getenv("COGNITOR_API_KEY"))
    parser.add_argument("--qdrant-url", type=str, default=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    parser.add_argument("--qdrant-api-key", type=str, default=os.getenv("QDRANT_API_KEY"))
    parser.add_argument("--weaviate-url", type=str, default=os.getenv("WEAVIATE_URL", "http://127.0.0.1:8080"))

    args = parser.parse_args()

    return Config(
        targets=[x.strip() for x in args.targets.split(",") if x.strip()],
        dataset=args.dataset,
        beir_cache_dir=args.beir_cache_dir,
        output_dir=args.output_dir,
        collection_name=args.collection_name,
        embedding_model=args.embedding_model,
        top_k=args.top_k,
        max_corpus=args.max_corpus,
        max_queries=args.max_queries,
        ingest_batch_size=args.ingest_batch_size,
        metadata_filter_track=args.metadata_filter_track,
        metadata_groups=args.metadata_groups,
        cognitor_url=args.cognitor_url,
        cognitor_api_key=args.cognitor_api_key,
        qdrant_url=args.qdrant_url,
        qdrant_api_key=args.qdrant_api_key,
        weaviate_url=args.weaviate_url,
    )


def beir_dataset_path(cache_dir: Path, dataset_name: str) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / dataset_name
    if target.exists():
        return target
    zip_url = f"{BEIR_DATASET_URL_PREFIX}/{dataset_name}.zip"
    downloaded = util.download_and_unzip(zip_url, str(cache_dir))
    return Path(downloaded)


def pick_subset(
    corpus: dict[str, dict[str, str]],
    queries: dict[str, str],
    qrels: dict[str, dict[str, int]],
    max_corpus: int,
    max_queries: int,
) -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, dict[str, int]]]:
    valid_queries: dict[str, str] = {}
    valid_qrels: dict[str, dict[str, int]] = {}

    for qid, text in queries.items():
        rels = qrels.get(qid, {})
        filtered = {doc_id: rel for doc_id, rel in rels.items() if rel > 0 and doc_id in corpus}
        if not filtered:
            continue
        valid_queries[qid] = text
        valid_qrels[qid] = filtered
        if len(valid_queries) >= max_queries:
            break

    required_doc_ids: set[str] = set()
    for rels in valid_qrels.values():
        required_doc_ids.update(rels.keys())

    if len(required_doc_ids) > max_corpus:
        kept_queries: dict[str, str] = {}
        kept_qrels: dict[str, dict[str, int]] = {}
        required_doc_ids = set()
        for qid, text in valid_queries.items():
            rels = valid_qrels[qid]
            candidate_union = required_doc_ids | set(rels.keys())
            if len(candidate_union) > max_corpus:
                continue
            kept_queries[qid] = text
            kept_qrels[qid] = rels
            required_doc_ids = candidate_union
        valid_queries = kept_queries
        valid_qrels = kept_qrels

    selected_doc_ids = list(required_doc_ids)
    if len(selected_doc_ids) < max_corpus:
        for doc_id in corpus.keys():
            if doc_id in required_doc_ids:
                continue
            selected_doc_ids.append(doc_id)
            if len(selected_doc_ids) >= max_corpus:
                break

    selected_corpus = {doc_id: corpus[doc_id] for doc_id in selected_doc_ids}
    return selected_corpus, valid_queries, valid_qrels


def stable_group(value: str, groups: int) -> int:
    if groups <= 0:
        raise ValueError("metadata-groups must be > 0")
    total = 0
    for ch in value:
        total = (total * 131 + ord(ch)) % 2_147_483_647
    return total % groups


def ndcg_at_k(relevances: list[int], k: int) -> float:
    rel = relevances[:k]
    if not rel:
        return 0.0
    dcg = 0.0
    for i, r in enumerate(rel, start=1):
        dcg += (2**r - 1) / np.log2(i + 1)
    ideal = sorted(rel, reverse=True)
    idcg = 0.0
    for i, r in enumerate(ideal, start=1):
        idcg += (2**r - 1) / np.log2(i + 1)
    return (dcg / idcg) if idcg > 0 else 0.0


def average_precision_at_k(relevances: list[int], k: int) -> float:
    rel = relevances[:k]
    num_rel = 0
    ap_sum = 0.0
    for i, r in enumerate(rel, start=1):
        if r > 0:
            num_rel += 1
            ap_sum += num_rel / i
    if num_rel == 0:
        return 0.0
    return ap_sum / num_rel


def reciprocal_rank_at_k(relevances: list[int], k: int) -> float:
    for i, r in enumerate(relevances[:k], start=1):
        if r > 0:
            return 1.0 / i
    return 0.0


def recall_at_k(relevances: list[int], total_relevant: int, k: int) -> float:
    if total_relevant <= 0:
        return 0.0
    return float(sum(1 for r in relevances[:k] if r > 0)) / float(total_relevant)


def evaluate(
    qrels: dict[str, dict[str, int]],
    ranked_results: dict[str, list[str]],
    k: int,
) -> dict[str, float]:
    ndcgs: list[float] = []
    maps: list[float] = []
    mrrs: list[float] = []
    recalls: list[float] = []

    for qid, rels in qrels.items():
        ranked_ids = ranked_results.get(qid, [])
        rel_vector = [int(rels.get(doc_id, 0)) for doc_id in ranked_ids]
        ndcgs.append(ndcg_at_k(rel_vector, k))
        maps.append(average_precision_at_k(rel_vector, k))
        mrrs.append(reciprocal_rank_at_k(rel_vector, k))
        recalls.append(recall_at_k(rel_vector, total_relevant=len(rels), k=k))

    return {
        f"nDCG@{k}": float(np.mean(ndcgs)) if ndcgs else 0.0,
        f"MAP@{k}": float(np.mean(maps)) if maps else 0.0,
        f"MRR@{k}": float(np.mean(mrrs)) if mrrs else 0.0,
        f"Recall@{k}": float(np.mean(recalls)) if recalls else 0.0,
    }


def build_adapters(cfg: Config) -> list[VectorDBAdapter]:
    adapters: list[VectorDBAdapter] = []
    for target in cfg.targets:
        if target == "cognitor":
            adapters.append(CognitorAdapter(cfg.cognitor_url, cfg.cognitor_api_key))
        elif target == "qdrant":
            adapters.append(QdrantAdapter(cfg.qdrant_url, cfg.qdrant_api_key))
        elif target == "weaviate":
            adapters.append(WeaviateAdapter(cfg.weaviate_url))
        elif target == "chroma":
            adapters.append(ChromaAdapter())
        else:
            raise ValueError(f"Unknown target '{target}'. Supported: cognitor,qdrant,weaviate,chroma")
    return adapters


def run_target(
    adapter: VectorDBAdapter,
    cfg: Config,
    dim: int,
    doc_texts: list[str],
    doc_metas: list[dict[str, Any]],
    doc_vectors: np.ndarray,
    q_items: list[tuple[str, str]],
    q_vectors: list[np.ndarray],
    qrels: dict[str, dict[str, int]],
) -> dict[str, Any]:
    adapter.wait_ready()
    collection_name = f"{cfg.collection_name}_{adapter.name}"
    adapter.recreate_collection(collection_name, dim)

    t_ingest_start = time.perf_counter()
    for start in range(0, len(doc_texts), cfg.ingest_batch_size):
        end = min(start + cfg.ingest_batch_size, len(doc_texts))
        adapter.bulk_add(
            collection_name=collection_name,
            vectors=doc_vectors[start:end],
            texts=doc_texts[start:end],
            metadatas=doc_metas[start:end],
        )
    ingest_seconds = time.perf_counter() - t_ingest_start

    ranked_ids: dict[str, list[str]] = {}
    latencies_ms: list[float] = []

    for (qid, _), q_vec in zip(q_items, q_vectors):
        t0 = time.perf_counter()
        results = adapter.search(collection_name, q_vec, cfg.top_k, None)
        latencies_ms.append((time.perf_counter() - t0) * 1000.0)

        ranked = []
        for item in results:
            metadata = item.get("metadata") or {}
            beir_id = metadata.get("beir_id")
            if beir_id is not None:
                ranked.append(str(beir_id))
        ranked_ids[qid] = ranked

    quality = evaluate(qrels, ranked_ids, cfg.top_k)
    query_seconds = float(sum(latencies_ms) / 1000.0)

    metadata_report: dict[str, Any] | None = None
    if cfg.metadata_filter_track:
        filtered_qrels: dict[str, dict[str, int]] = {}
        filtered_ranked_ids: dict[str, list[str]] = {}
        filtered_latencies_ms: list[float] = []
        correctness_scores: list[float] = []

        for (qid, _), q_vec in zip(q_items, q_vectors):
            target_group = stable_group(qid, cfg.metadata_groups)
            rels = qrels.get(qid, {})
            rels_in_group = {
                doc_id: rel
                for doc_id, rel in rels.items()
                if stable_group(doc_id, cfg.metadata_groups) == target_group
            }
            if not rels_in_group:
                continue

            t0 = time.perf_counter()
            results = adapter.search(
                collection_name,
                q_vec,
                cfg.top_k,
                {"bench_group": target_group},
            )
            filtered_latencies_ms.append((time.perf_counter() - t0) * 1000.0)

            ranked = []
            returned_groups = []
            for item in results:
                metadata = item.get("metadata") or {}
                beir_id = metadata.get("beir_id")
                if beir_id is not None:
                    ranked.append(str(beir_id))
                grp = metadata.get("bench_group")
                if isinstance(grp, int):
                    returned_groups.append(grp)

            filtered_qrels[qid] = rels_in_group
            filtered_ranked_ids[qid] = ranked
            if returned_groups:
                correctness_scores.append(
                    sum(1 for g in returned_groups if g == target_group) / len(returned_groups)
                )

        if filtered_qrels:
            filtered_quality = evaluate(filtered_qrels, filtered_ranked_ids, cfg.top_k)
            filtered_query_seconds = float(sum(filtered_latencies_ms) / 1000.0)
            metadata_report = {
                "enabled": True,
                "groups": cfg.metadata_groups,
                "query_count_evaluated": len(filtered_qrels),
                "quality": filtered_quality,
                "query_qps": (
                    len(filtered_qrels) / filtered_query_seconds
                    if filtered_query_seconds > 0
                    else 0.0
                ),
                "query_p50_ms": float(np.percentile(filtered_latencies_ms, 50)),
                "query_p95_ms": float(np.percentile(filtered_latencies_ms, 95)),
                "query_p99_ms": float(np.percentile(filtered_latencies_ms, 99)),
                "filter_correctness": (
                    float(np.mean(correctness_scores)) if correctness_scores else 0.0
                ),
            }
        else:
            metadata_report = {
                "enabled": True,
                "groups": cfg.metadata_groups,
                "query_count_evaluated": 0,
                "quality": {},
                "query_qps": 0.0,
                "query_p50_ms": 0.0,
                "query_p95_ms": 0.0,
                "query_p99_ms": 0.0,
                "filter_correctness": 0.0,
                "note": "No queries had relevant docs in the chosen groups.",
            }

    return {
        "target": adapter.name,
        "corpus_size": len(doc_texts),
        "query_count": len(q_items),
        "ingest_seconds": ingest_seconds,
        "ingest_docs_per_s": (len(doc_texts) / ingest_seconds) if ingest_seconds > 0 else 0.0,
        "query_qps": (len(q_items) / query_seconds) if query_seconds > 0 else 0.0,
        "query_p50_ms": float(np.percentile(latencies_ms, 50)),
        "query_p95_ms": float(np.percentile(latencies_ms, 95)),
        "query_p99_ms": float(np.percentile(latencies_ms, 99)),
        "quality": quality,
        "metadata_filter_track": metadata_report,
    }


def main() -> None:
    cfg = parse_args()

    dataset_dir = beir_dataset_path(cfg.beir_cache_dir, cfg.dataset)
    corpus, queries, qrels = GenericDataLoader(data_folder=str(dataset_dir)).load(split="test")
    corpus, queries, qrels = pick_subset(corpus, queries, qrels, cfg.max_corpus, cfg.max_queries)

    if not corpus or not queries:
        raise RuntimeError("Empty benchmark subset. Increase --max-corpus or --max-queries.")

    model = SentenceTransformer(cfg.embedding_model)
    if hasattr(model, "get_embedding_dimension"):
        dim = int(model.get_embedding_dimension())
    else:
        dim = int(model.get_sentence_embedding_dimension())

    doc_ids = list(corpus.keys())
    doc_texts: list[str] = []
    doc_metas: list[dict[str, Any]] = []
    for doc_id in doc_ids:
        title = (corpus[doc_id].get("title") or "").strip()
        body = (corpus[doc_id].get("text") or "").strip()
        merged = f"{title}\n\n{body}".strip()
        doc_texts.append(merged)
        doc_metas.append(
            {
                "beir_id": doc_id,
                "dataset": cfg.dataset,
                "title": title[:200],
                "char_len": len(merged),
                "bench_group": stable_group(doc_id, cfg.metadata_groups),
            }
        )

    doc_vectors = np.asarray(
        model.encode(doc_texts, convert_to_numpy=True, show_progress_bar=True),
        dtype=np.float32,
    )

    q_items = list(queries.items())
    q_texts = [q for _, q in q_items]
    q_vectors_np = np.asarray(
        model.encode(q_texts, convert_to_numpy=True, show_progress_bar=False),
        dtype=np.float32,
    )
    q_vectors = [q_vectors_np[i] for i in range(len(q_vectors_np))]

    adapters = build_adapters(cfg)

    results: list[dict[str, Any]] = []
    failed: list[dict[str, str]] = []

    for adapter in adapters:
        print(f"\nRunning target={adapter.name} ...")
        try:
            result = run_target(
                adapter=adapter,
                cfg=cfg,
                dim=dim,
                doc_texts=doc_texts,
                doc_metas=doc_metas,
                doc_vectors=doc_vectors,
                q_items=q_items,
                q_vectors=q_vectors,
                qrels=qrels,
            )
            results.append(result)
        except Exception as exc:
            failed.append({"target": adapter.name, "error": str(exc)})
            print(f"Target {adapter.name} failed: {exc}")

    if not results:
        raise RuntimeError("All targets failed")

    report = {
        "benchmark": "BEIR end-to-end retrieval (multi-target)",
        "dataset": cfg.dataset,
        "embedding_model": cfg.embedding_model,
        "top_k": cfg.top_k,
        "corpus_size": len(doc_texts),
        "query_count": len(q_items),
        "targets": cfg.targets,
        "results": results,
        "failed": failed,
    }

    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    out_path = cfg.output_dir / f"beir-e2e-compare-{cfg.dataset}-{timestamp}.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n=== BEIR Multi-Target Benchmark ===")
    header = f"{'target':<10} {'nDCG@k':>10} {'MAP@k':>10} {'MRR@k':>10} {'Recall@k':>10} {'qps':>10} {'p95_ms':>10}"
    print(header)
    print("-" * len(header))
    for result in results:
        quality = result["quality"]
        print(
            f"{result['target']:<10} "
            f"{quality.get(f'nDCG@{cfg.top_k}', 0.0):>10.4f} "
            f"{quality.get(f'MAP@{cfg.top_k}', 0.0):>10.4f} "
            f"{quality.get(f'MRR@{cfg.top_k}', 0.0):>10.4f} "
            f"{quality.get(f'Recall@{cfg.top_k}', 0.0):>10.4f} "
            f"{result['query_qps']:>10.2f} "
            f"{result['query_p95_ms']:>10.2f}"
        )
    if failed:
        print("\nFailed targets:")
        for item in failed:
            print(f"- {item['target']}: {item['error']}")
    print(f"Saved report: {out_path}")


if __name__ == "__main__":
    main()
