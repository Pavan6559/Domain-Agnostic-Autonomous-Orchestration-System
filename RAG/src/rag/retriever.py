from typing import List, Optional, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from .metadata import MetadataTagger
from .utils import get_logger

logger = get_logger("RAGRetriever")

class RAGRetriever:
    """Core retrieval engine supporting multi-domain classification and ChromaDB top-k search."""

    # Map agent role keywords to primary domains
    ROLE_DOMAIN_MAP = {
        'governance_statutory': ['governance', 'statutory', 'committee', 'senate', 'nba', 'naac', 'accreditation', 'compliance', 'board'],
        'academic_curriculum': ['academic', 'curriculum', 'course', 'syllabus', 'dean', 'education', 'credit', 'ugc'],
        'student_affairs': ['student', 'admission', 'hostel', 'warden', 'discipline', 'conduct', 'welfare', 'grievance'],
        'finance_administration': ['finance', 'fee', 'budget', 'tuition', 'scholarship', 'prize', 'award', 'treasurer'],
        'operations_logistics': ['operations', 'timetable', 'schedule', 'exam', 'venue', 'facility', 'logistics'],
        'faculty_hr': ['faculty', 'workload', 'staff', 'hod', 'professor', 'hr', 'human resources']
    }

    def __init__(self, vector_db: Chroma):
        self.vector_db = vector_db

    def get_domain_for_role(self, agent_role: str) -> Optional[str]:
        """Maps an agent's role (e.g., 'Finance Dean') to a primary domain (e.g., 'finance')."""
        role_lower = agent_role.lower()
        for domain, keywords in self.ROLE_DOMAIN_MAP.items():
            if any(k in role_lower for k in keywords):
                return domain
        return None

    def retrieve(self, query: str, domain: Optional[str] = None, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Retrieves top-k relevant chunks for a query from ChromaDB.
        Supports filtering by primary_domain.
        """
        filter_dict = {"primary_domain": domain} if domain else None
        if domain:
            logger.info(f"Retrieving with domain filter: '{domain}' for query: '{query}'")
        else:
            logger.info(f"Retrieving without domain filter for query: '{query}'")

        try:
            if filter_dict:
                return self.vector_db.similarity_search_with_score(query, k=k, filter=filter_dict)
            return self.vector_db.similarity_search_with_score(query, k=k)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []

    def retrieve_multi_query(self, queries: List[str], domain: Optional[str] = None, k_per_query: int = 4, max_total: int = 5) -> List[Tuple[Document, float]]:
        """
        Performs multi-query retrieval inside one domain. Combines ChromaDB results,
        deduplicates chunks, and keeps the closest-distance top matches.
        """
        logger.info(f"Performing multi-query retrieval for {len(queries)} queries. Domain: {domain}")
        combined_results = [
            result
            for query in queries
            for result in self.retrieve(query, domain=domain, k=k_per_query)
        ]

        # Deduplicate based on chunk page content while keeping the lowest Chroma distance
        unique_results = {}
        for doc, distance in combined_results:
            content = doc.page_content
            if content not in unique_results or distance < unique_results[content][1]:
                unique_results[content] = (doc, distance)

        # Chroma returns distance scores, so lower is better.
        sorted_unique = list(unique_results.values())
        sorted_unique.sort(key=lambda x: x[1])

        return sorted_unique[:max_total]

    def retrieve_across_domains(self, query: str, domains: List[str], k: int = 4) -> List[Tuple[Document, float]]:
        """
        Retrieves chunks from every selected domain and keeps the closest ChromaDB matches.
        Chroma returns distance scores, so lower is better.
        """
        logger.info(f"Retrieving across domains: {domains}")
        combined_results = [
            result
            for domain in domains
            for result in self.retrieve(query, domain=domain, k=k)
        ]

        unique_results = {}
        for doc, distance in combined_results:
            content = doc.page_content
            if content not in unique_results or distance < unique_results[content][1]:
                unique_results[content] = (doc, distance)

        sorted_unique = list(unique_results.values())
        sorted_unique.sort(key=lambda x: x[1])
        return sorted_unique[:k]

    def trace_retrieval(self, results: List[Tuple[Document, float]]):
        """Prints a detailed retrieval trace for debugging and inspection."""
        print("\n" + "="*80)
        print(" RETRIEVAL INSPECTION TRACE ")
        print("="*80)
        if not results:
            print("No documents retrieved.")
        for i, (doc, distance) in enumerate(results):
            meta = doc.metadata
            print(f"\nChunk {i+1} | Distance: {distance:.4f} | Source: {meta.get('source_file')} | Page: {meta.get('page')}")
            print(f"Domain: {meta.get('primary_domain')} | Secondary Tags: [{meta.get('secondary_tags')}]")
            print("-" * 80)
            content_snippet = doc.page_content.replace("\n", " ")[:200]
            print(f"Snippet: {content_snippet}...")
        print("="*80 + "\n")

    def retrieve_for_agent(self, agent_role: str, task_description: str, queries: Optional[List[str]] = None, k: int = 4) -> str:
        """
        High-level agent retrieval interface. The query is classified into one or more
        domains by the LLM, then ChromaDB retrieves top-k matching chunks from those domains.
        """
        domain_query = " ".join(queries) if queries else task_description
        domains = MetadataTagger.classify_query_domains(domain_query)
        logger.info(f"Query for agent role '{agent_role}' classified into domains '{domains}'")

        if queries:
            results = []
            for query in queries:
                results.extend(self.retrieve_across_domains(query, domains=domains, k=k))
            results = self._dedupe_and_sort(results, max_total=k)
        else:
            results = self.retrieve_across_domains(task_description, domains=domains, k=k)

        self.trace_retrieval(results)

        if not results:
            return "No reference documents found for this domain."

        # Format context for prompt
        context_parts = []
        for i, (doc, distance) in enumerate(results):
            meta = doc.metadata
            context_parts.append(
                f"[Reference {i+1} | Source: {meta.get('source_file')} | Page: {meta.get('page')}]\n"
                f"{doc.page_content}"
            )
        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def _dedupe_and_sort(results: List[Tuple[Document, float]], max_total: int) -> List[Tuple[Document, float]]:
        """Deduplicates retrieved chunks and keeps the closest-distance results."""
        unique_results = {}
        for doc, distance in results:
            content = doc.page_content
            if content not in unique_results or distance < unique_results[content][1]:
                unique_results[content] = (doc, distance)

        sorted_unique = list(unique_results.values())
        sorted_unique.sort(key=lambda x: x[1])
        return sorted_unique[:max_total]
