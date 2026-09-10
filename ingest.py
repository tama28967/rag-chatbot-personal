"""Load documents from data/raw, split, embed with Gemini, store in Qdrant."""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "raw"
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "rag_documents"

LOADERS_BY_SUFFIX = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".md": TextLoader,
}


def load_documents():
    documents = []
    for path in DATA_DIR.iterdir():
        if not path.is_file():
            continue
        loader_cls = LOADERS_BY_SUFFIX.get(path.suffix.lower())
        if loader_cls is None:
            continue
        documents.extend(loader_cls(str(path)).load())
    return documents


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def build_vectorstore():
    """(Re)build the Qdrant collection from every file currently in data/raw."""
    documents = load_documents()
    if not documents:
        return None, 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)

    client = QdrantClient(url=QDRANT_URL)
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
    )
    return vectorstore, len(chunks)


def load_vectorstore():
    """Load the existing Qdrant collection, if any."""
    client = QdrantClient(url=QDRANT_URL)
    try:
        if not client.collection_exists(COLLECTION_NAME):
            return None
    except UnexpectedResponse:
        return None

    return QdrantVectorStore.from_existing_collection(
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        url=QDRANT_URL,
    )


if __name__ == "__main__":
    if not os.environ.get("GOOGLE_API_KEY"):
        raise SystemExit("GOOGLE_API_KEY belum diset. Isi file .env terlebih dahulu.")

    vectorstore, chunk_count = build_vectorstore()
    if vectorstore is None:
        print(f"Tidak ada dokumen ditemukan di {DATA_DIR}. Tambahkan file .pdf/.txt/.md lalu jalankan ulang.")
    else:
        print(f"Vectorstore dibangun: {chunk_count} chunk tersimpan di Qdrant ({QDRANT_URL})")
