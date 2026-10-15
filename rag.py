import os
import chromadb
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL = MODEL = "openai/gpt-oss-120b" # update if Groq rejects this name
MAX_DISTANCE = 0.85  # lower = stricter. Tune this with your own PDF.
NO_ANSWER = "I don't know based on this document."

embedder = SentenceTransformer("all-MiniLM-L6-v2")
llm = Groq(api_key=os.getenv("GROQ_API_KEY"))
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def reset_collection():
    """Clear old documents before indexing a new one."""
    global collection
    try:
        chroma.get_collection("docs")
    except Exception:
        collection = chroma.get_or_create_collection(
            "docs", metadata={"hnsw:space": "cosine"}
        )
        return

    chroma.delete_collection("docs")
    collection = chroma.get_or_create_collection("docs", metadata={"hnsw:space": "cosine"})


def load_pdf(path):
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]


def chunk_text(text, size=800, overlap=150):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def index_pdf(path, name=None):
    name = name or os.path.basename(path)
    ids, docs, metas = [], [], []
    for page_num, text in load_pdf(path):
        for j, chunk in enumerate(chunk_text(text)):
            if not chunk.strip():
                continue
            ids.append(f"{name}-{page_num}-{j}")
            docs.append(chunk)
            metas.append({"page": page_num, "source": name})
    if not docs:
        return 0
    embeddings = embedder.encode(docs).tolist()
    collection.add(ids=ids, documents=docs, embeddings=embeddings, metadatas=metas)
    return len(docs)


def retrieve(question, k=4):
    """Return only chunks that are close enough to the question."""
    total = collection.count()
    if total == 0:
        return []
    q_emb = embedder.encode([question]).tolist()
    res = collection.query(query_embeddings=q_emb, n_results=min(k, total))
    documents = res.get("documents", [])
    metadatas = res.get("metadatas", [])
    distances = res.get("distances", [])
    if not documents or not documents[0]:
        return []
    hits = zip(documents[0], metadatas[0], distances[0])
    return [(d, m, dist) for d, m, dist in hits if dist <= MAX_DISTANCE]


def answer(question):
    hits = retrieve(question)
    if not hits:
        return NO_ANSWER, []

    context = "\n\n".join(f"[Page {m['page']}] {d}" for d, m, _ in hits)
    system = (
        "You answer questions using ONLY the provided context. "
        "Cite page numbers like [Page 3]. "
        f"If the answer is not in the context, say exactly: {NO_ANSWER}"
    )
    resp = llm.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    sources = [{"page": m["page"], "text": d} for d, m, _ in hits]
    return resp.choices[0].message.content, sources