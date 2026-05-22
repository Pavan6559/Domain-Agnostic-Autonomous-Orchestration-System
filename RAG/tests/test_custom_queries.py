import os
import sys
import json

# Setup root path so we can import src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.rag import RAGIngestor, RAGRetriever, RAGQueryEngine, MetadataTagger, setup_unicode, get_logger

setup_unicode()
logger = get_logger("CustomQueriesTest")

# Define diverse test queries across all 6 domains plus a refusal case
TEST_QUERIES = [
    # 1. governance_statutory
    {
        "domain": "governance_statutory",
        "role": "Governance Officer",
        "query": "What is the composition and role of the Senate as per statutory guidelines?"
    },
    {
        "domain": "governance_statutory",
        "role": "Compliance Reviewer",
        "query": "What statutory bodies exist for governing the academic and administrative decisions?"
    },
    # 2. academic_curriculum
    {
        "domain": "academic_curriculum",
        "role": "Curriculum Designer",
        "query": "How many total credits are required for the B.Tech Electrical Engineering program, and what are some core courses?"
    },
    {
        "domain": "academic_curriculum",
        "role": "Academic Officer",
        "query": "What are the rules regarding registration for 400-level B.Tech courses?"
    },
    # 3. student_affairs
    {
        "domain": "student_affairs",
        "role": "Dean of Student Affairs",
        "query": "Who is listed as the Dean of Students Affairs (DOSA) and what associate deans assist them?"
    },
    {
        "domain": "student_affairs",
        "role": "Hostel Warden",
        "query": "Who are the wardens or assistant wardens listed for the hostels?"
    },
    # 4. finance_administration
    {
        "domain": "finance_administration",
        "role": "Finance Officer",
        "query": "Which committee is responsible for coordinating student scholarships, assistantships, and prizes?"
    },
    {
        "domain": "finance_administration",
        "role": "Student Advisor",
        "query": "Is there a specific fee mentioned for tuition or hostel admission for undergraduate students?"
    },
    # 5. operations_logistics
    {
        "domain": "operations_logistics",
        "role": "Operations Coordinator",
        "query": "What details are provided about examination scheduling and timetabling?"
    },
    {
        "domain": "operations_logistics",
        "role": "Academic Officer",
        "query": "How are grades finalized and moderated before publication?"
    },
    # 6. faculty_hr
    {
        "domain": "faculty_hr",
        "role": "HR Specialist",
        "query": "What is the policy or workload expectations for faculty members like HODs?"
    },
    {
        "domain": "faculty_hr",
        "role": "Dean of Faculty",
        "query": "What are the key functionaries and statutory bodies mentioned under administration?"
    },
    # 7. Refusal / Out-of-bounds Case
    {
        "domain": "out_of_bounds",
        "role": "General Agent",
        "query": "What is the recipe for chocolate chip cookies or the names of the security guard's pets?"
    }
]

def main():
    try:
        docs_dir = os.path.join(ROOT_DIR, "docs")
        persist_dir = os.path.join(ROOT_DIR, "chroma_db")
        output_file = os.path.join(ROOT_DIR, "tests", "custom_queries_output.json")

        logger.info("Initializing RAG Ingestor...")
        ingestor = RAGIngestor(docs_dir=docs_dir, persist_dir=persist_dir)
        
        logger.info("Running Ingestion...")
        vector_db = ingestor.run_ingestion(force_rebuild=False)
        
        logger.info("Initializing Retriever and Query Engine...")
        retriever = RAGRetriever(vector_db=vector_db)
        query_engine = RAGQueryEngine(model_name="gemma3:1b")

        results = []

        logger.info(f"Starting evaluation of {len(TEST_QUERIES)} queries...")
        for i, item in enumerate(TEST_QUERIES, 1):
            query = item["query"]
            role = item["role"]
            expected_domain = item["domain"]
            
            logger.info(f"[{i}/{len(TEST_QUERIES)}] Query: '{query}' | Role: '{role}'")
            
            # Classify domains
            classified_domains = MetadataTagger.classify_query_domains(query)
            
            # Retrieve context
            context = retriever.retrieve_for_agent(
                agent_role=role,
                task_description=query
            )
            
            # Generate answer
            answer = query_engine.generate_answer(query, context)
            
            logger.info(f"Answer: {answer[:100]}...")
            
            results.append({
                "index": i,
                "query": query,
                "role": role,
                "expected_domain": expected_domain,
                "classified_domains": classified_domains,
                "retrieved_context": context,
                "answer": answer
            })
            
        # Save results to JSON file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Evaluation complete. Results saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error executing custom queries test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
