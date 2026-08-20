from __future__ import annotations

from google import genai
from google.genai import types


class GeminiClient:
    """Thin adapter around Gemini generation and embedding APIs."""

    def __init__(
        self,
        api_key: str,
        llm_model: str,
        embedding_model: str,
        embedding_dimensions: int,
    ) -> None:
        if not api_key:
            raise ValueError("A chave da API Gemini é obrigatória.")
        self._client = genai.Client(api_key=api_key)
        self._llm_model = llm_model
        self._embedding_model = embedding_model
        self._embedding_dimensions = embedding_dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = self._client.models.embed_content(
            model=self._embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_DOCUMENT",
                output_dimensionality=self._embedding_dimensions,
            ),
        )
        return [embedding.values for embedding in response.embeddings or []]

    def embed_query(self, text: str) -> list[float]:
        response = self._client.models.embed_content(
            model=self._embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="QUESTION_ANSWERING",
                output_dimensionality=self._embedding_dimensions,
            ),
        )
        if not response.embeddings:
            raise RuntimeError("A API Gemini não retornou embedding para a consulta.")
        return response.embeddings[0].values

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._llm_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=700),
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError("A API Gemini retornou uma resposta vazia.")
        return text
