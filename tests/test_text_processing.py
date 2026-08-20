from src.models import DocumentSection
from src.text_processing import chunk_sections, clean_text, split_text


def test_clean_text_normalizes_whitespace_and_blank_lines():
    raw = "Título   com   espaços\r\n\r\n\r\nLinha\tfinal  "

    assert clean_text(raw) == "Título com espaços\n\nLinha final"


def test_split_text_respects_chunk_size_and_overlap():
    text = " ".join(["conteúdo"] * 200)

    chunks = split_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 120 for chunk in chunks)


def test_chunk_sections_keeps_traceable_metadata_and_stable_id():
    section = DocumentSection(
        text="Política corporativa de férias e benefícios.",
        metadata={"source": "politica.md", "source_path": "rh/politica.md", "page": 2},
    )

    first = chunk_sections([section], chunk_size=100, overlap=10)
    second = chunk_sections([section], chunk_size=100, overlap=10)

    assert first[0].id == second[0].id
    assert first[0].metadata["location"] == "página: 2"
    assert first[0].metadata["source"] == "politica.md"
