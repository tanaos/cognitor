# ---- builder ----
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch must come first to prevent sentence-transformers from pulling
# the CUDA wheels (~2.5 GB).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Strip everything that is irrelevant at runtime.
RUN rm -rf /usr/local/lib/python3.12/site-packages/torch/include \
           /usr/local/lib/python3.12/site-packages/torch/share \
    && find /usr/local/lib/python3.12/site-packages \
            -type d -name "tests" -prune -exec rm -rf {} \; \
    && find /usr/local/lib/python3.12/site-packages \
            -name "*.pyi" -delete \
    && find /usr/local/lib/python3.12/site-packages \
            -type d -name "__pycache__" -prune -exec rm -rf {} \;

# ---- runtime ----
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/

VOLUME ["/app/storage"]

EXPOSE 7530

CMD ["uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "7530"]
