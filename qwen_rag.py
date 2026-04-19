"""
Qwen RAG System — Semantic search over any codebase.
Uses ChromaDB + sentence-transformers for local, offline vector search.
"""

import os, json, hashlib, time
import glob as glob_lib
from pathlib import Path
from typing import Optional

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".cpp", ".c",
    ".h", ".cs", ".rb", ".php", ".swift", ".kt", ".md", ".txt", ".json",
    ".yaml", ".yml", ".toml", ".env", ".sh", ".bash", ".sql", ".html", ".css",
    ".vue", ".svelte", ".dart", ".ex", ".exs", ".hs", ".r", ".m", ".scala",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", ".nuxt", "target", "vendor", ".cache", "qwen_rag", ".mypy_cache",
}

CHUNK_LINES = 60   # lines per chunk
MAX_FILE_SIZE = 500_000  # 500KB max


class RAGSystem:
    """Local vector search over codebase files."""

    def __init__(self, persist_dir: str = "qwen_rag"):
        self.persist_dir  = persist_dir
        self._client      = None
        self._collection  = None
        self._model       = None
        self._initialized = False

    def _init(self):
        if self._initialized:
            return
        try:
            import chromadb
            from sentence_transformers import SentenceTransformer
            self._client     = chromadb.PersistentClient(path=self.persist_dir)
            self._collection = self._client.get_or_create_collection(
                "codebase",
                metadata={"hnsw:space": "cosine"}
            )
            print("Loading embedding model (all-MiniLM-L6-v2)...")
            self._model  = SentenceTransformer("all-MiniLM-L6-v2")
            self._initialized = True
            print(f"RAG ready. {self._collection.count()} chunks indexed.")
        except ImportError as e:
            raise RuntimeError(f"RAG deps missing: pip install chromadb sentence-transformers | {e}")

    # ── INDEXING ──────────────────────────────────────────────────────────────
    def index_directory(self, path: str = ".", force: bool = False) -> str:
        self._init()
        p = Path(path).resolve()
        if not p.exists():
            return f"Path not found: {path}"

        all_files = self._collect_files(p)
        indexed   = 0
        skipped   = 0

        for fp in all_files:
            try:
                result = self._index_file(str(fp), force=force)
                if result > 0:
                    indexed += result
                else:
                    skipped += 1
            except Exception:
                skipped += 1

        return (f"✅ RAG Index complete: {indexed} chunks from {len(all_files)} files "
                f"({skipped} skipped) | Total in DB: {self._collection.count()}")

    def _collect_files(self, root: Path) -> list:
        files = []
        for fp in root.rglob("*"):
            if any(part in SKIP_DIRS for part in fp.parts):
                continue
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if fp.stat().st_size > MAX_FILE_SIZE:
                continue
            files.append(fp)
        return files

    def _index_file(self, filepath: str, force: bool = False) -> int:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            content = f.read()
        if not content.strip():
            return 0

        # Check if already indexed (by file hash)
        file_hash = hashlib.md5(content.encode()).hexdigest()
        meta_id   = f"__meta__{filepath}"

        if not force:
            existing = self._collection.get(ids=[meta_id])
            if existing["ids"] and existing["metadatas"]:
                if existing["metadatas"][0].get("hash") == file_hash:
                    return 0  # unchanged

        # Build chunks
        lines  = content.splitlines()
        chunks = []
        for i in range(0, max(1, len(lines)), CHUNK_LINES):
            chunk_lines = lines[i : i + CHUNK_LINES]
            chunk_text  = "\n".join(chunk_lines)
            if chunk_text.strip():
                chunks.append((f"{filepath}::L{i+1}", chunk_text, i + 1))

        if not chunks:
            return 0

        # Embed all chunks
        texts      = [c[1] for c in chunks]
        embeddings = self._model.encode(texts, show_progress_bar=False).tolist()

        # Upsert chunks
        self._collection.upsert(
            ids        = [c[0] for c in chunks],
            documents  = [c[1] for c in chunks],
            metadatas  = [{"file": filepath, "start_line": c[2], "hash": file_hash} for c in chunks],
            embeddings = embeddings,
        )

        # Store meta
        self._collection.upsert(
            ids        = [meta_id],
            documents  = [f"meta:{filepath}"],
            metadatas  = [{"file": filepath, "hash": file_hash, "chunks": len(chunks)}],
            embeddings = [self._model.encode([f"meta {filepath}"], show_progress_bar=False)[0].tolist()],
        )

        return len(chunks)

    # ── SEARCH ────────────────────────────────────────────────────────────────
    def search(self, query: str, n: int = 6, file_filter: str = "") -> str:
        self._init()
        if self._collection.count() == 0:
            return "RAG index is empty. Run rag_index first."

        embedding = self._model.encode([query], show_progress_bar=False)[0].tolist()

        where = None
        if file_filter:
            where = {"file": {"$contains": file_filter}}

        results = self._collection.query(
            query_embeddings = [embedding],
            n_results        = min(n, self._collection.count()),
            where            = where,
            include          = ["documents", "metadatas", "distances"],
        )

        if not results["ids"][0]:
            return f"No results for: {query}"

        output = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if meta.get("file", "").startswith("__meta__"):
                continue
            score    = round((1 - dist) * 100, 1)
            filepath = meta.get("file", "?")
            line     = meta.get("start_line", 1)
            output.append(
                f"**{filepath}** (line {line}, relevance {score}%)\n"
                f"```\n{doc[:600]}\n```"
            )

        return "\n\n---\n\n".join(output) if output else "No relevant results."

    def stats(self) -> str:
        self._init()
        count = self._collection.count()
        return f"RAG: {count} chunks indexed in '{self.persist_dir}'"

    def clear(self) -> str:
        self._init()
        self._client.delete_collection("codebase")
        self._collection = self._client.get_or_create_collection("codebase")
        return "✅ RAG index cleared."


# ── STANDALONE TEST ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    rag = RAGSystem()
    print(rag.index_directory("."))
    print(rag.search("how does the tool executor work"))
