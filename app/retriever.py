"""The 'R' in RAG: finds the document paragraphs most relevant to a question.

Uses TF-IDF (classic keyword-based search) so it's free, runs offline and is
easy to explain. It could be swapped for a vector database like ChromaDB later.
"""
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOCS_DIR = Path(__file__).resolve().parent.parent / "data" / "docs"


class Retriever:
    def __init__(self, docs_dir: Path = DOCS_DIR):
        # Split every document into paragraphs ("chunks").
        self.chunks = []
        for path in sorted(docs_dir.glob("*.txt")):
            for paragraph in path.read_text(encoding="utf-8").split("\n\n"):
                if paragraph.strip():
                    self.chunks.append({"document": path.name, "text": paragraph.strip()})

                # Character n-grams match parts of words, so "password" also matches "passwords".
        self.vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self.matrix = self.vectorizer.fit_transform(c["text"] for c in self.chunks)

    def search(self, query: str, k: int = 3) -> list[dict]:
        """Return the top-k chunks that share meaningful words with the query."""
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        best = scores.argsort()[::-1][:k]
        return [self.chunks[i] for i in best if scores[i] > 0]
