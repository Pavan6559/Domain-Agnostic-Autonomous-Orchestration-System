import os
import sys
from collections import Counter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.rag import RAGIngestor, RAGRetriever, RAGQueryEngine, MetadataTagger, get_logger, setup_unicode


setup_unicode()
logger = get_logger("RAGWorkflowEval")


RETRIEVAL_CASES = [
    {
        "name": "student affairs dean lookup",
        "role": "Dean of Student Affairs",
        "query": "Who is listed as Dean of Students Affairs (DOSA)?",
        "expected_terms": ["Dean of Students Affairs", "DOSA"],
    },
    {
        "name": "student affairs associate deans",
        "role": "Dean of Student Affairs",
        "query": "Which associate dean roles are under Dean of Students Affairs?",
        "expected_terms": ["Associate Dean", "Student Affairs"],
    },
    {
        "name": "curriculum credits",
        "role": "Curriculum Designer",
        "query": "What credits or courses are listed for the B.Tech EE curriculum?",
        "expected_terms": ["credit", "course"],
    },
    {
        "name": "grading rules",
        "role": "Academic Officer",
        "query": "What grading rules or grade points are mentioned?",
        "expected_terms": ["Grade", "Grade_Points"],
    },
    {
        "name": "committee governance",
        "role": "Governance Officer",
        "query": "Which committees or statutory bodies are mentioned?",
        "expected_terms": ["Committee"],
    },
    {
        "name": "cross-domain curriculum compliance",
        "role": "Compliance Reviewer",
        "query": "What curriculum and regulation information should be checked for academic compliance?",
        "expected_terms": ["curriculum", "regulation", "credit"],
    },
    {
        "name": "course level eligibility",
        "role": "Academic Officer",
        "query": "What eligibility is mentioned for 400 level B.Tech courses?",
        "expected_terms": ["400", "B.Tech", "Cr"],
    },
    {
        "name": "hostel wardens",
        "role": "Student Affairs Officer",
        "query": "Which hostel wardens or assistant wardens are listed?",
        "expected_terms": ["Warden", "Assistant_Warden", "Hostel"],
    },
    {
        "name": "grade moderation",
        "role": "Academic Officer",
        "query": "What is the process for grade finalization or grade moderation?",
        "expected_terms": ["grade", "moderation", "instructors"],
    },
    {
        "name": "ee curriculum course names",
        "role": "Curriculum Designer",
        "query": "List examples of courses from the B.Tech Electrical Engineering curriculum.",
        "expected_terms": ["Electrical", "Course", "Semester"],
    },
    {
        "name": "student scholarships committee",
        "role": "Student Affairs Officer",
        "query": "Which committee is related to student scholarships and prizes?",
        "expected_terms": ["Scholarships", "Prizes", "Committee"],
    },
    {
        "name": "research and administration deans",
        "role": "Governance Officer",
        "query": "Who are the deans for R&D and Administration?",
        "expected_terms": ["R&D", "Administration", "Dean"],
    },
]


ANSWER_CASES = [
    {
        "name": "known DOSA name extraction",
        "role": "Dean of Student Affairs",
        "query": "Who is listed as Dean of Students Affairs (DOSA)?",
        "expected_answer_terms": ["Ankita", "Sharma"],
    },
    {
        "name": "missing information refusal",
        "role": "Finance Officer",
        "query": "What is the exact hostel fee for VLSI students?",
        "expected_answer_terms": ["don't know", "not in the context", "not mentioned"],
    },
    {
        "name": "course level answer",
        "role": "Academic Officer",
        "query": "What eligibility is mentioned for 400 level B.Tech courses?",
        "expected_answer_terms": ["75", "B.Tech", "Cr"],
    },
    {
        "name": "committee answer",
        "role": "Student Affairs Officer",
        "query": "Which committee is related to student scholarships and prizes?",
        "expected_answer_terms": ["Student Scholarships", "Prizes", "Committee"],
    },
]


def contains_any(text, terms):
    lower_text = text.lower()
    return any(term.lower() in lower_text for term in terms)


def main():
    docs_dir = os.path.join(ROOT_DIR, "docs")
    persist_dir = os.path.join(ROOT_DIR, "chroma_db")

    print("\n=== RAG WORKFLOW EVAL ===")
    print(f"Docs dir: {docs_dir}")
    print(f"DB dir:   {persist_dir}")

    docs = sorted(name for name in os.listdir(docs_dir) if name.lower().endswith(".pdf"))
    print(f"\nPDF count: {len(docs)}")
    for doc in docs:
        print(f"- {doc}")

    ingestor = RAGIngestor(docs_dir=docs_dir, persist_dir=persist_dir)
    vector_db = ingestor.run_ingestion(force_rebuild=False)
    retriever = RAGRetriever(vector_db=vector_db)
    query_engine = RAGQueryEngine(model_name="gemma3:1b")

    collection_count = vector_db._collection.count()
    print(f"\nChroma collection chunks: {collection_count}")

    collection = vector_db._collection.get(include=["metadatas"])
    domain_counts = Counter(meta.get("primary_domain", "missing") for meta in collection.get("metadatas", []))
    print("\nDomain distribution:")
    for domain, count in sorted(domain_counts.items()):
        print(f"- {domain}: {count}")

    print("\n=== RETRIEVAL CASES ===")
    retrieval_passes = 0
    for case in RETRIEVAL_CASES:
        domains = MetadataTagger.classify_query_domains(case["query"])
        results = retriever.retrieve_across_domains(case["query"], domains=domains, k=4)
        context = "\n\n".join(doc.page_content for doc, _ in results)
        passed = bool(results) and contains_any(context, case["expected_terms"])
        retrieval_passes += int(passed)

        print(f"\n[{case['name']}] {'PASS' if passed else 'FAIL'}")
        print(f"Query: {case['query']}")
        print(f"Domains: {domains}")
        print(f"Results: {len(results)}")
        for i, (doc, distance) in enumerate(results[:2], start=1):
            meta = doc.metadata
            snippet = " ".join(doc.page_content.split())[:220]
            print(
                f"  {i}. distance={distance:.4f}, domain={meta.get('primary_domain')}, "
                f"source={meta.get('source_file')}, page={meta.get('page')}"
            )
            print(f"     {snippet}")

    print("\n=== ANSWER CASES ===")
    answer_passes = 0
    for case in ANSWER_CASES:
        context = retriever.retrieve_for_agent(
            agent_role=case["role"],
            task_description=case["query"],
            k=4
        )
        answer = query_engine.generate_answer(case["query"], context)
        passed = contains_any(answer, case["expected_answer_terms"])
        answer_passes += int(passed)

        print(f"\n[{case['name']}] {'PASS' if passed else 'FAIL'}")
        print(f"Query: {case['query']}")
        print(f"Answer: {answer}")

    print("\n=== SUMMARY ===")
    print(f"Retrieval: {retrieval_passes}/{len(RETRIEVAL_CASES)} passed")
    print(f"Answering: {answer_passes}/{len(ANSWER_CASES)} passed")

    if retrieval_passes == len(RETRIEVAL_CASES) and answer_passes == len(ANSWER_CASES):
        print("Overall: PASS")
    else:
        print("Overall: NEEDS ATTENTION")


if __name__ == "__main__":
    main()
