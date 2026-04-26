# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — ServicePilot Backend
# Target: HuggingFace Spaces (Docker SDK)
#
# HF Spaces automatically sets PORT=7860.
# api.py already reads: port = int(os.environ.get("PORT", 8000))
# So no code changes needed — it binds to 7860 automatically.
#
# Optimization: BGE model download + ChromaDB vectorstore initialization
# both happen at IMAGE BUILD TIME, not at runtime. This means:
#   - Zero cold start delay on first request
#   - Build takes ~12-15 min (one-time cost, never repeated)
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# HuggingFace Spaces requires port 7860
EXPOSE 7860

WORKDIR /app

# Install system-level build dependencies required by sentence-transformers
# (gcc/g++ needed to compile some native C extensions during pip install)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies first (Docker layer cache optimization) ──────
# Copying requirements.txt alone before the full COPY means this expensive
# layer is only rebuilt when dependencies actually change, not on every push.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy full project into the container ─────────────────────────────────────
COPY . .

# ── Suppress telemetry noise ─────────────────────────────────────────────────
ENV ANONYMIZED_TELEMETRY=False
ENV CHROMA_TELEMETRY=False

# ── PRE-BUILD: Download BGE model + Initialize ChromaDB vectorstore ───────────
# Importing chroma_utils triggers MODULE-LEVEL execution:
#   MODEL = SentenceTransformer('BAAI/bge-base-en-v1.5')  → downloads ~438MB
# Then initialize_vector_store() embeds all 100 incident titles and persists
# the ChromaDB index to /app/vectorstore/ inside the image layer.
# Both operations are combined into one RUN step intentionally — importing
# chroma_utils already loads the model, so calling SentenceTransformer again
# separately would be redundant and wasteful.
RUN python -c "from utils.chroma_utils import initialize_vector_store; \
    initialize_vector_store(); \
    print('[Build] BGE model downloaded + vectorstore ready.')"

# ── Start the FastAPI server ──────────────────────────────────────────────────
# api.py reads PORT from environment → binds to 7860 on HF Spaces automatically
# Force PORT=7860 for HuggingFace Spaces
ENV PORT=7860

CMD ["python", "api.py"]