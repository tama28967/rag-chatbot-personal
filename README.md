# RAG Chatbot Personal

A document Q&A chatbot built on Retrieval-Augmented Generation (RAG): upload a PDF/TXT/MD document, ask questions about it, and get answers grounded in the document's actual content — with source chunks shown for every answer.

## Architecture

```
Document upload (PDF/TXT/MD)
    -> split into chunks
    -> embedded with Google Gemini (gemini-embedding-001)
    -> stored in Qdrant (vector database)

User question
    -> embedded -> similarity search in Qdrant (top-K chunks)
    -> retrieved chunks + question sent to Gemini (gemini-3.6-flash) as context
    -> answer streamed back in a chat UI, with source chunks shown
```

Both the app and the vector database run as separate services under Docker Compose — a client-server setup, not an embedded/in-process vector store.

## Stack

- **Orchestration:** LangChain
- **LLM + Embeddings:** Google Gemini (`langchain-google-genai`)
- **Vector database:** [Qdrant](https://qdrant.tech/) (containerized)
- **Interface:** Streamlit chat UI
- **Containerization:** Docker Compose (`app` + `qdrant` services)

## Running it

Requirements: Docker Desktop, a Gemini API key ([Google AI Studio](https://aistudio.google.com/apikey) — create the key in a project **without** a billing account attached to stay on the free tier).

```bash
cp .env.example .env
# edit .env and set GOOGLE_API_KEY

docker compose up -d --build
```

Open `http://localhost:8501`, upload a document in the sidebar, click **Proses Dokumen**, then ask questions in the chat box.

## Project structure

```
.
├── app.py               # Streamlit chat UI (upload + chat)
├── ingest.py             # document loading, chunking, embedding, Qdrant indexing
├── Dockerfile
├── docker-compose.yml    # app + qdrant services
├── requirements.txt
└── requirements.md       # design notes and decision log
```

## Notes

This is a personal learning project focused on the practical side of building a RAG pipeline — vector database fundamentals, embedding/retrieval flow, and running an AI app as a proper containerized service — rather than a from-scratch implementation of every RAG component.
