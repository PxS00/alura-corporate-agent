from __future__ import annotations

from dataclasses import dataclass

from src.ai_client import GeminiClient
from src.config import Settings
from src.document_loader import DocumentLoader
from src.text_processing import chunk_sections
from src.vector_store import VectorStore


@dataclass(frozen=True, slots=True)
class IndexingResult:
    documents: int
    chunks: int


def rebuild_index(
    settings: Settings,
    ai_client: GeminiClient,
    vector_store: VectorStore,
) -> IndexingResult:
    """Rebuild the vector index from the curated document directory."""
    loader = DocumentLoader(settings.documents_path)
    sections = loader.load_directory()
    chunks = chunk_sections(sections, settings.chunk_size, settings.chunk_overlap)

    if not chunks:
        raise RuntimeError("Nenhum conteúdo válido foi encontrado para indexação.")

    embeddings: list[list[float]] = []
    batch_size = 50
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        embeddings.extend(ai_client.embed_documents([chunk.text for chunk in batch]))

    if len(embeddings) != len(chunks):
        raise RuntimeError("A quantidade de embeddings retornada não corresponde aos chunks gerados.")

    vector_store.replace_all(chunks, embeddings)
    source_paths = {str(section.metadata.get("source_path", "")) for section in sections}
    return IndexingResult(documents=len(source_paths), chunks=len(chunks))
