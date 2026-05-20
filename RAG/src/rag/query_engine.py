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
3. For lists or tables, be extremely careful to match the correct person with the correct title.
4. The context may contain PDF symbols or broken spacing. Ignore visual symbols and extract the relevant text labels exactly.
5. If the context contains partial but relevant labels, answer with those labels rather than saying you do not know.

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
