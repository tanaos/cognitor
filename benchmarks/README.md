# Vector DB Benchmark Suite

This folder provides a practical, reproducible BEIR benchmark to compare Cognitor against other vector databases on real document retrieval tasks.

## Targets

Currently supported targets:
- `cognitor`
- `qdrant`
- `weaviate`
- `chroma`

You can run all targets or any subset.

## Setup

1. Install benchmark dependencies:

```bash
.venv/bin/pip install -r benchmarks/requirements.txt
```

2. Start Cognitor (if not already running):

```bash
docker compose up -d
```

3. Start external DBs (Qdrant + Weaviate) if included in `--targets`:

```bash
docker compose -f benchmarks/docker-compose.benchmark.yml up -d
```

## End-to-End Retrieval Benchmark (BEIR)

This benchmark evaluates real retrieval engines (documents + metadata + queries + qrels), not just ANN index quality.

### Why BEIR

BEIR is a widely used IR benchmark suite with heterogeneous datasets and standard relevance metrics.
Typical metrics:
- `nDCG@10`
- `MAP@10`
- `MRR@10`
- `Recall@10`

### Run

```bash
.venv/bin/python benchmarks/run_beir_e2e.py \
  --targets cognitor,qdrant,weaviate,chroma \
  --dataset scifact \
  --max-corpus 20000 \
  --max-queries 1000 \
  --top-k 10
```

Start external DB services first:

```bash
docker compose -f benchmarks/docker-compose.benchmark.yml up -d
```

Optional: evaluate metadata-constrained retrieval quality and filter correctness:

```bash
.venv/bin/python benchmarks/run_beir_e2e.py \
  --targets cognitor,qdrant,weaviate,chroma \
  --dataset scifact \
  --metadata-filter-track \
  --metadata-groups 8
```

### Output

Writes a JSON report to:
- `benchmarks/results/beir-e2e-compare-<dataset>-<timestamp>.json`

Report includes both quality and performance:
- quality: `nDCG@k`, `MAP@k`, `MRR@k`, `Recall@k`
- performance: ingest docs/s, query QPS, p50/p95/p99 latency
- metadata filter track (optional): filtered quality metrics plus `filter_correctness`
