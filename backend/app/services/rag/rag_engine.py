from pathlib import Path
from typing import List

from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHROMA_PATH, MODEL_LOCAL_FILES_ONLY, RAG_DATA_DIR


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"local_files_only": MODEL_LOCAL_FILES_ONLY},
    )


def create_vector_db():
    documents = []
    for path in sorted(Path(RAG_DATA_DIR).glob("*.txt")):
        loader = TextLoader(str(path), encoding="utf-8")
        loaded = loader.load()
        for doc in loaded:
            doc.metadata["source"] = path.name
        documents.extend(loaded)

    if not documents:
        raise FileNotFoundError(f"No RAG text files found in {RAG_DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=80)
    docs = splitter.split_documents(documents)

    vectordb = Chroma.from_documents(
        docs,
        get_embeddings(),
        persist_directory=CHROMA_PATH,
        collection_name="ats_knowledge",
    )
    vectordb.persist()
    return vectordb


def vector_db_is_stale() -> bool:
    chroma_dir = Path(CHROMA_PATH)
    if not chroma_dir.exists() or not any(chroma_dir.iterdir()):
        return True

    data_files = list(Path(RAG_DATA_DIR).glob("*.txt"))
    if not data_files:
        return True

    db_files = [path for path in chroma_dir.rglob("*") if path.is_file()]
    if not db_files:
        return True

    newest_data = max(path.stat().st_mtime for path in data_files)
    newest_db = max(path.stat().st_mtime for path in db_files)
    return newest_data > newest_db


def get_vector_db():
    if vector_db_is_stale():
        return create_vector_db()
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embeddings(),
        collection_name="ats_knowledge",
    )


def search_rag(query: str, k: int = 4) -> List[str]:
    vectordb = get_vector_db()
    results = vectordb.similarity_search(query, k=k)
    return [doc.page_content for doc in results]
