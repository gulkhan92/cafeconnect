FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install the CPU-only PyTorch build first. Left to its own resolution, pip
# pulls the default PyPI wheel, which drags in ~1GB of CUDA/cuDNN packages
# that are dead weight here: embeddings run on CPU (there's no GPU on a
# free-tier host), so nothing in this image ever calls into them.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -e .

COPY . .

# Run as a non-root user: a container compromise (e.g. via a dependency CVE)
# then can't write outside its own app directory or touch host-level files.
RUN groupadd --system app && useradd --system --gid app --no-create-home app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
