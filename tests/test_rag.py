from pathlib import Path

from src.config import Settings
from src.models import SearchResult
from src.rag import FALLBACK_ANSWER, RagAgent


class FakeAiClient:
    def __init__(self) -> None:
        self.generated_prompt: str | None = None

    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2]

    def generate(self, prompt: str) -> str:
        self.generated_prompt = prompt
        return "O pedido de férias deve ser enviado com 30 dias de antecedência."


class FakeVectorStore:
    def __init__(self, results: list[SearchResult]) -> None:
        self.results = results

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        return self.results[:top_k]


def make_settings() -> Settings:
    return Settings(
        gemini_api_key="test",
        llm_model="test-model",
        embedding_model="test-embedding",
        embedding_dimensions=2,
        chroma_path=Path(".chroma-test"),
        chroma_collection="test",
        documents_path=Path("documents"),
        chunk_size=1000,
        chunk_overlap=150,
        top_k=4,
        max_cosine_distance=0.65,
    )


def test_agent_answers_with_relevant_context_and_sources():
    ai_client = FakeAiClient()
    store = FakeVectorStore(
        [
            SearchResult(
                text="O pedido de férias deve ser enviado ao RH com 30 dias de antecedência.",
                metadata={
                    "source": "politica_ferias.md",
                    "category": "rh",
                    "location": "seção: document",
                },
                distance=0.2,
            )
        ]
    )
    agent = RagAgent(make_settings(), ai_client, store)

    response = agent.ask("Quando devo pedir férias?")

    assert "30 dias" in response.answer
    assert response.sources[0].source == "politica_ferias.md"
    assert "REGRAS OBRIGATÓRIAS" in (ai_client.generated_prompt or "")


def test_agent_falls_back_when_search_is_not_relevant():
    ai_client = FakeAiClient()
    store = FakeVectorStore(
        [
            SearchResult(
                text="Conteúdo fora do assunto.",
                metadata={"source": "outro.md", "category": "geral", "location": "documento"},
                distance=0.9,
            )
        ]
    )
    agent = RagAgent(make_settings(), ai_client, store)

    response = agent.ask("Qual é o vale estacionamento?")

    assert response.answer == FALLBACK_ANSWER
    assert response.sources == ()
    assert ai_client.generated_prompt is None


def test_agent_uses_only_best_semantic_match():
    ai_client = FakeAiClient()
    store = FakeVectorStore(
        [
            SearchResult(
                text="A NexaCorp concede 30 dias corridos de férias.",
                metadata={
                    "source": "politica_ferias.md",
                    "category": "rh",
                    "location": "seção: document",
                },
                distance=0.20,
            ),
            SearchResult(
                text="Cada colaborador possui benefício anual para cursos e certificações.",
                metadata={
                    "source": "faq.md",
                    "category": "comunicacao",
                    "location": "seção: document",
                },
                distance=0.24,
            ),
        ]
    )
    agent = RagAgent(make_settings(), ai_client, store)

    response = agent.ask("Quantos dias de férias os colaboradores possuem?")

    assert [source.source for source in response.sources] == ["politica_ferias.md"]
    assert "faq.md" not in (ai_client.generated_prompt or "")
