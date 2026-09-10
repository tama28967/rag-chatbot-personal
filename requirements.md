# PRJ-0005 — RAG Chatbot Personal (Document Q&A with Gemini)

Captured 2026-09-10. Personal learning project — not a formal Engineering Blueprint (no Consulting Framework pipeline was run, per ADR-0033's personal-project bypass path).

## Why this exists

Founder-stated goal: learn the practical fundamentals of vector databases and AI automation by building and using a RAG chatbot — not by studying RAG theory in depth. The project prioritizes "how to build it and how to use it" over deep theoretical exploration of chunking strategies, embedding math, etc.

## End-to-end flow

```
User uploads document(s) (PDF/TXT/MD) via Streamlit sidebar
    -> ingest pipeline: load -> split into chunks -> embed (Gemini text-embedding-004)
    -> stored in Chroma (persisted locally in vectorstore/)

User asks a question in the chat UI
    -> question embedded -> similarity search in Chroma (top-K chunks)
    -> retrieved chunks + question sent to Gemini (gemini-2.5-flash) as context
    -> answer streamed back in a ChatGPT-style chat interface, with source chunks shown
```

## Chosen stack (revised 2026-09-10 — production-grade pivot)

Founder revised scope mid-build: the original goal ("belajar dasar, portofolio kecil") was superseded by an explicit ask for **production-grade, portfolio-worthy** output (showable on LinkedIn/Upwork). This drove a stack change from a local single-process Chroma/FAISS setup to a containerized client-server stack.

| Stage | Choice | Why |
|---|---|---|
| Orchestration | LangChain | Practical, well-documented, avoids hand-rolling every RAG component |
| LLM (generation) | Google Gemini (`gemini-3.6-flash`) via `langchain-google-genai` | `gemini-2.5-flash` was deprecated for new API keys mid-build; `gemini-3.6-flash` is the current equivalent |
| Embeddings | Google `gemini-embedding-001` via `langchain-google-genai` | `text-embedding-004` is deprecated; this is the current embedding model. 3072-dim vectors. |
| Vector store | **Qdrant** (Docker container, `qdrant/qdrant:latest`) | Switched from Chroma after Chroma's native binary reproducibly segfaulted (access violation) on the Founder's Windows machine — confirmed across chromadb 1.0.15/1.5.9, a clean venv, and both Git Bash and PowerShell, so it was a genuine native-binary incompatibility, not an environment/shell issue. Qdrant is a real client-server vector DB (production-credible), not just a workaround. |
| Document loaders/splitter | LangChain built-ins (`PyPDFLoader`, `TextLoader` — used for both `.txt` and `.md`, `RecursiveCharacterTextSplitter`) | `UnstructuredMarkdownLoader`/`unstructured` was dropped: it pulled in a heavy spaCy/thinc/blis dependency chain just to parse Markdown, which isn't needed for RAG chunking and was slowing Docker builds on a slow connection |
| Interface | Streamlit chat UI (`st.chat_message`/`st.chat_input`) | ChatGPT-like experience (chat bubbles, history) with minimal frontend work; also hosts the document upload control |
| Containerization | **Docker Compose** (`app` + `qdrant` services) | Founder-requested production-grade requirement; also sidesteps the Windows-native Chroma crash entirely by running in a Linux container |

Explicitly **not** built in this phase: CLI interface (superseded by the Streamlit chat UI), manual/from-scratch chunking or embedding code (Founder chose framework-first, practical approach over fundamentals-from-first-principles), live cloud deployment (planned next — see Open items).

## Structure

```
0004 RAG Chatbot Personal/
├── project.yaml
├── requirements.md
├── data/raw/          # uploaded source documents (bind-mounted into the app container)
├── ingest.py             # load -> split -> embed -> store in Qdrant (importable + standalone script)
├── app.py                 # Streamlit: upload + chat UI
├── requirements.txt
├── Dockerfile
├── docker-compose.yml    # app + qdrant services
├── .dockerignore
├── .env.example
└── .gitignore
```

## Setup (Founder action required before first run)

1. Get a Gemini API key from Google AI Studio, created in a project with **no billing account attached** (a billing-linked project's Gemini prepay wallet can be at $0 and reject requests with 429, even with general GCP trial credit available — a genuinely free-tier key avoids this).
2. Copy `.env.example` to `.env` and set `GOOGLE_API_KEY`.
3. `docker compose up -d --build`
4. Open `http://localhost:8501`, upload a document, click "Proses Dokumen", then chat.

## Verified working (2026-09-10)

Full stack built and tested end-to-end via Docker Compose: document upload -> ingest into Qdrant -> chat query -> correct, source-grounded answer from Gemini. Confirmed with both a `.txt` test file and a real PDF (`PETUNJUK TEKNIS PMB MADRASAH 2026-2027.pdf`).

## Open items / next phase

- **Live deployment** (Founder-requested, not yet done): deploy the Docker Compose stack to a free-tier host (Railway/Render) so there's a shareable link for LinkedIn/Upwork, instead of only "clone and run locally".
- **GitHub public repo**: push this project to a public repo with a portfolio-quality README (architecture diagram, screenshots, setup instructions) — this is what actually gets shown to recruiters/clients, not just working code.
- No automated re-ingestion on file change (manual "Proses Dokumen" button in the sidebar for now).
- No chat history persistence across container restarts (in-memory only; the Qdrant collection itself does persist via the `qdrant_storage` volume).
- Automation layer (e.g. n8n-driven folder watcher) deferred — noted in the original design discussion as a possible later phase, not committed.
