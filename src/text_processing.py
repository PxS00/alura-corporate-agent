from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from src.models import DocumentSection, TextChunk


def clean_text(text: str) -> str:
    """Normalize extraction noise while preserving paragraph boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

    cleaned_lines: list[str] = []
    previous_blank = False
    for line in lines:
        is_blank = not line
        if is_blank and previous_blank:
            continue
        cleaned_lines.append(line)
        previous_blank = is_blank

    return "\n".join(cleaned_lines).strip()


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks, preferring natural boundaries."""
    if chunk_size <= 0:
        raise ValueError("chunk_size deve ser maior que zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap deve ser >= 0 e menor que chunk_size")

    normalized = clean_text(text)
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0

    while start < len(normalized):
        hard_end = min(start + chunk_size, len(normalized))
        end = hard_end

        if hard_end < len(normalized):
            search_from = start + int(chunk_size * 0.6)
            candidate = max(
                normalized.rfind("\n\n", search_from, hard_end),
                normalized.rfind(". ", search_from, hard_end),
                normalized.rfind("\n", search_from, hard_end),
            )
            if candidate > start:
                end = candidate + (2 if normalized[candidate:candidate + 2] == ". " else 0)

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)

    return chunks


def chunk_sections(
    sections: Iterable[DocumentSection],
    chunk_size: int,
    overlap: int,
) -> list[TextChunk]:
    """Convert extracted sections into stable, traceable text chunks."""
    chunks: list[TextChunk] = []

    for section in sections:
        for index, text in enumerate(split_text(section.text, chunk_size, overlap)):
            location = _location_from_metadata(section.metadata)
            identity = "|".join(
                [
                    str(section.metadata.get("source_path", section.metadata.get("source", "unknown"))),
                    location,
                    str(index),
                    text,
                ]
            )
            chunk_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()
            metadata = {**section.metadata, "chunk_index": index, "location": location}
            chunks.append(TextChunk(id=chunk_id, text=text, metadata=metadata))

    return chunks


def _location_from_metadata(metadata: dict) -> str:
    for key, label in (("page", "página"), ("slide", "slide"), ("sheet", "planilha"), ("section", "seção")):
        value = metadata.get(key)
        if value is not None:
            return f"{label}: {value}"
    return "documento"
