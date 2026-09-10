"""Streamlit chat UI for the RAG chatbot: upload documents, ask questions."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

import ingest

load_dotenv()

DATA_DIR = Path(__file__).parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="RAG Chatbot Personal", page_icon="💬")
st.title("💬 RAG Chatbot Personal")

if not os.environ.get("GOOGLE_API_KEY"):
    st.error("GOOGLE_API_KEY belum diset. Isi file .env (lihat .env.example) lalu restart aplikasi.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = ingest.load_vectorstore()

with st.sidebar:
    st.header("Dokumen")
    uploaded_files = st.file_uploader(
        "Upload dokumen (PDF/TXT/MD)",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        for file in uploaded_files:
            (DATA_DIR / file.name).write_bytes(file.getvalue())
        st.success(f"{len(uploaded_files)} file disimpan ke data/raw.")

    if st.button("Proses Dokumen", type="primary"):
        with st.spinner("Membangun vectorstore..."):
            vectorstore, chunk_count = ingest.build_vectorstore()
        if vectorstore is None:
            st.warning("Belum ada dokumen di data/raw.")
        else:
            st.session_state.vectorstore = vectorstore
            st.success(f"Selesai: {chunk_count} chunk ter-index.")

    existing_files = sorted(p.name for p in DATA_DIR.iterdir() if p.is_file() and p.name != ".gitkeep")
    if existing_files:
        st.caption("Dokumen tersimpan:")
        for name in existing_files:
            st.caption(f"- {name}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sumber"):
                for source in message["sources"]:
                    st.caption(source)

question = st.chat_input("Tanya sesuatu tentang dokumenmu...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    if st.session_state.vectorstore is None:
        answer = "Belum ada dokumen yang diproses. Upload dokumen di sidebar lalu klik 'Proses Dokumen'."
        sources = []
    else:
        llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Kamu adalah asisten yang menjawab pertanyaan berdasarkan konteks dokumen berikut. "
                    "Jika jawaban tidak ada di konteks, katakan kamu tidak tahu, jangan mengarang.\n\n{context}",
                ),
                ("human", "{input}"),
            ]
        )
        combine_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 4})
        retrieval_chain = create_retrieval_chain(retriever, combine_chain)

        with st.spinner("Berpikir..."):
            result = retrieval_chain.invoke({"input": question})

        answer = result["answer"]
        sources = [
            f"{doc.metadata.get('source', 'unknown')} — {doc.page_content[:150]}..."
            for doc in result.get("context", [])
        ]

    with st.chat_message("assistant"):
        st.markdown(answer)
        if sources:
            with st.expander("Sumber"):
                for source in sources:
                    st.caption(source)

    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
