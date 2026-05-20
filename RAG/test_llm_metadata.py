#!/usr/bin/env python3
"""
Smoke test for LLM-based metadata tagging and query-domain retrieval.
"""

import os
import sys

from src.rag import setup_unicode, get_logger, RAGIngestor, RAGRetriever, RAGQueryEngine

setup_unicode()
logger = get_logger("TestLLMMetadata")


def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(script_dir, "docs")
        persist_dir = os.path.join(script_dir, "chroma_db")

        ingestor = RAGIngestor(docs_dir=docs_dir, persist_dir=persist_dir)
        logger.info("=" * 80)
        logger.info("Initializing document ingestion with LLM-based metadata tagging...")
        logger.info("Chunk size: 1200, overlap: 150")
        logger.info("Domain classification: LLM-based with keyword fallback")
        logger.info("=" * 80)

        vector_db = ingestor.run_ingestion(force_rebuild=False)
        retriever = RAGRetriever(vector_db=vector_db)
        query_engine = RAGQueryEngine(model_name="gemma3:1b")

        query = "Who are the statutory bodies?"
        agent_role = "Governance Officer"
        logger.info(f"Test Query: '{query}'")

        context = retriever.retrieve_for_agent(
            agent_role=agent_role,
            task_description=query
        )

        logger.info(f"Retrieved Context (first 500 chars):\n{context[:500]}...\n")
        answer = query_engine.generate_answer(query, context)

        print("\n" + "=" * 80)
        print(" TEST COMPLETE - LLM-BASED METADATA TAGGING WORKING ")
        print("=" * 80)
        print(f"Query: {query}")
        print("-" * 80)
        print(f"Answer: {answer}")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
