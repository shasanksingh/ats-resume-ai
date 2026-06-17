import re
from pathlib import Path
from typing import Dict, List

import chromadb
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHROMA_PATH, MODEL_LOCAL_FILES_ONLY, RAG_DATA_DIR


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "ats_knowledge"
SEARCH_STOPWORDS = {
    "and", "the", "with", "for", "from", "that", "this", "role", "job",
    "experience", "required", "requirements", "responsibilities", "skills",
    "candidate", "team", "work", "years", "will", "our", "your", "engineer",
    "developer", "analyst", "manager", "specialist",
}
GENERIC_GUIDANCE_SOURCES = {"ats_rules", "recruiter_rules"}


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"local_files_only": MODEL_LOCAL_FILES_ONLY},
    )


def create_vector_db():
    documents = load_documents()
    if not documents:
        raise FileNotFoundError(f"No RAG text files found in {RAG_DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=520, chunk_overlap=90)
    docs = splitter.split_documents(documents)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass

    return Chroma.from_documents(
        docs,
        get_embeddings(),
        client=client,
        collection_name=COLLECTION_NAME,
    )


def guidance_corpus_available() -> bool:
    return any(Path(RAG_DATA_DIR).glob("*.txt"))


def load_documents():
    documents = []
    for path in sorted(Path(RAG_DATA_DIR).glob("*.txt")):
        loader = TextLoader(str(path), encoding="utf-8")
        loaded = loader.load()
        for doc in loaded:
            doc.metadata["source"] = path.name
        documents.extend(loaded)
    return documents


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
        collection_name=COLLECTION_NAME,
    )


def search_rag(query: str, k: int = 4) -> List[str]:
    return [item["content"] for item in search_rag_detailed(query, k)]


def search_rag_detailed(query: str, k: int = 4) -> List[Dict[str, str]]:
    combined: List[Dict[str, str]] = keyword_search(query, max(k, 4))
    try:
        vectordb = get_vector_db()
        query_terms = tokenize(query)
        for document in vectordb.similarity_search(query, k=max(k * 2, 6)):
            source = str(document.metadata.get("source") or "local_knowledge")
            if not source_relevant(source, query_terms):
                continue
            combined.append(
                {
                    "content": clean_content(document.page_content),
                    "source": source,
                    "retrieval": "semantic",
                }
            )
    except Exception:
        pass

    return deduplicate_results(combined)[:k]


def keyword_search(query: str, k: int) -> List[Dict[str, str]]:
    query_terms = tokenize(query)
    candidates = []

    for path in sorted(Path(RAG_DATA_DIR).glob("*.txt")):
        if not source_relevant(path.name, query_terms):
            continue
        text = path.read_text(encoding="utf-8")
        raw_chunks = [chunk for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
        chunks = (
            split_lines_into_chunks(text)
            if len(raw_chunks) == 1
            else [clean_content(chunk) for chunk in raw_chunks]
        )

        source_terms = tokenize(path.stem.replace("_", " "))
        for chunk in chunks:
            chunk_terms = tokenize(chunk)
            overlap = len(query_terms.intersection(chunk_terms))
            source_overlap = len(query_terms.intersection(source_terms))
            phrase_bonus = 3 if any(term in path.stem for term in query_terms if len(term) > 4) else 0
            score = overlap + (source_overlap * 3) + phrase_bonus
            if score:
                candidates.append(
                    {
                        "content": chunk,
                        "source": path.name,
                        "retrieval": "keyword",
                        "score": score,
                    }
                )

    candidates.sort(key=lambda item: (-int(item["score"]), item["source"]))
    if not candidates:
        return []
    minimum_score = max(2, int(candidates[0]["score"]) // 2)
    return [
        {key: value for key, value in item.items() if key != "score"}
        for item in candidates
        if int(item["score"]) >= minimum_score
    ][:k]


def source_relevant(source: str, query_terms: set[str]) -> bool:
    stem = Path(source).stem.replace("_rules", "").replace("_", " ")
    if Path(source).stem in GENERIC_GUIDANCE_SOURCES:
        return True
    source_terms = tokenize(stem)
    return bool(source_terms.intersection(query_terms))


def split_lines_into_chunks(text: str) -> List[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    chunks = []
    for index in range(0, len(lines), 4):
        chunks.append(" ".join(lines[index:index + 4]))
    return chunks


def tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9+#.]+", text.lower())
        if len(token) > 2 and token not in SEARCH_STOPWORDS
    }


def clean_content(text: str) -> str:
    return " ".join(text.split()).strip()


def deduplicate_results(results: List[Dict[str, str]]) -> List[Dict[str, str]]:
    unique = []
    seen = set()
    for item in results:
        content = item.get("content", "")
        key = content.casefold()
        if not content or key in seen:
            continue
        unique.append(item)
        seen.add(key)
    return unique
