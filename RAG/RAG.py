import os
from src.rag import setup_unicode, get_logger, RAGIngestor, RAGRetriever, RAGQueryEngine

# Reconfigure stdout/stderr for Windows terminal unicode support
setup_unicode()
logger = get_logger("RAGMain")

def main():
    try:
        # Step 0: Initialize paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(script_dir, "docs")
        persist_dir = os.path.join(script_dir, "chroma_db")

        # Step 1: Initialize Ingestor & Ingest Documents
        ingestor = RAGIngestor(docs_dir=docs_dir, persist_dir=persist_dir)
        logger.info("Initializing document ingestion...")
        
        vector_db = ingestor.run_ingestion(force_rebuild=False)

        # Step 2: Initialize Retriever & Query Engine
        retriever = RAGRetriever(vector_db=vector_db)
        query_engine = RAGQueryEngine(model_name="gemma3:1b")

        # Step 3: Define query and query details
        query = "Who is listed as Dean of Students Affairs (DOSA)?"
        logger.info(f"Original Query: '{query}'")

        # Step 4: Classify the query domain, retrieve top-k chunks in that domain, and format context
        agent_role = "Dean of Student Affairs"
        context = retriever.retrieve_for_agent(
            agent_role=agent_role,
            task_description=query
        )

        # Step 5: Generate final answer
        logger.info("Sending prompt to LLM...")
        answer = query_engine.generate_answer(query, context)

        print("\n" + "="*80)
        print(" FINAL RAG ANSWER ")
        print("="*80)
        print(answer)
        print("="*80 + "\n")

    except Exception as e:
        logger.error(f"Error in execution pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
