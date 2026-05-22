from langchain_ollama import OllamaLLM
from .utils import get_logger

logger = get_logger("RAGQueryEngine")

class RAGQueryEngine:
    """Manages final answer generation from retrieved RAG context."""

    def __init__(self, model_name: str = "gemma3:1b"):
        self.llm = OllamaLLM(model=model_name)

    def _invoke_or_default(self, prompt: str, default: str, error_message: str) -> str:
        """Invokes the LLM and returns a fallback string if generation fails."""
        try:
            response = self.llm.invoke(prompt).strip()
            return response or default
        except Exception as e:
            logger.error(f"{error_message}: {e}")
            return default

    def generate_answer(self, query: str, context: str) -> str:
        """Generates a grounded answer based ONLY on the provided context."""
        logger.info("Generating final answer using context...")
        prompt = f"""
You are a strict document-based assistant. Your task is to extract information accurately from the provided text.

RULES:
1. Answer ONLY from the provided context.
2. If the answer is not in the context, say "I don't know based on the document".
3. Pay close attention to abbreviations and do NOT confuse them (e.g., DOSA is Dean of Students Affairs, DOAD is Dean of Administration, DOAA is Dean of Academic Affairs, DORD is Dean of R&D, DDIA is Dean of Digital Infrastructure). Align names and roles exactly as written.

CONTEXT:
{context}

QUESTION: {query}

Please provide a precise answer:
"""
        return self._invoke_or_default(
            prompt=prompt,
            default="I don't know based on the document",
            error_message="Failed to generate answer"
        )
