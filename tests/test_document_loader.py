from pathlib import Path

from src.document_loader import DocumentLoader


def test_load_directory_extracts_supported_text_formats(tmp_path: Path):
    rh = tmp_path / "rh"
    financeiro = tmp_path / "financeiro"
    legal = tmp_path / "legal"
    operacional = tmp_path / "operacional"
    for directory in (rh, financeiro, legal, operacional):
        directory.mkdir()

    (rh / "politica.md").write_text("Política de férias vigente.", encoding="utf-8")
    (financeiro / "reembolso.csv").write_text(
        "tipo,limite\nAlimentação,R$ 100\n",
        encoding="utf-8",
    )
    (legal / "conduta.json").write_text(
        '{"regra": "Proteger dados pessoais"}',
        encoding="utf-8",
    )
    (operacional / "guia.html").write_text(
        "<html><body><main>Ative o MFA no primeiro dia.</main></body></html>",
        encoding="utf-8",
    )

    sections = DocumentLoader(tmp_path).load_directory()

    assert len(sections) == 4
    assert {section.metadata["category"] for section in sections} == {
        "rh",
        "financeiro",
        "legal",
        "operacional",
    }
    assert all(section.metadata["owner"] for section in sections)
    assert all(section.metadata["source_path"] for section in sections)


def test_load_directory_removes_duplicate_content(tmp_path: Path):
    category = tmp_path / "rh"
    category.mkdir()
    content = "Mesmo documento corporativo."
    (category / "a.md").write_text(content, encoding="utf-8")
    (category / "b.md").write_text(content, encoding="utf-8")

    sections = DocumentLoader(tmp_path).load_directory()

    assert len(sections) == 1
