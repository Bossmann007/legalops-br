# LegalOps BR — container image
# Build: docker build -t legalops:0.3 .
# Run:   docker run --rm -v $(pwd):/work legalops:0.3 redact --input /work/email.txt

FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.5.*

WORKDIR /app

# Copy lock + pyproject first for layer cache
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.11-slim AS runtime

RUN groupadd --system legalops && useradd --system --gid legalops --home /home/legalops --create-home legalops

WORKDIR /app

COPY --from=build /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    LEGALOPS_AUDIT_DB=/data/audit.db

VOLUME ["/data"]
USER legalops

ENTRYPOINT ["legalops"]
CMD ["--help"]
