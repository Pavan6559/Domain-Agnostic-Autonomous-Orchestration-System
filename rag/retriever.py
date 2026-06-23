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

    def _classify_query_for_retrieval(self, query: str) -> Tuple[str, List[str], List[str]]:
        """Classifies a query into primary domain, secondary domains, and secondary tags."""
        logger.info(f"Classifying query for retrieval: '{query}'")
        query_metadata = MetadataTagger.classify_query_metadata(query)
        primary_domain = query_metadata["primary_domain"]
        secondary_domains = query_metadata["secondary_domains"]
        secondary_tags = query_metadata["secondary_tags"]
        logger.info(
            f"Query classified: primary_domain='{primary_domain}', secondary_domains={secondary_domains}, secondary_tags={secondary_tags}"
        )
        return primary_domain, secondary_domains, secondary_tags

    def retrieve(self, query: str, domain: Optional[str] = None, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Retrieves top-k relevant chunks for a query from ChromaDB.
        If `domain` is omitted, this method first classifies the query with the LLM
        into a primary domain and secondary domains/tags, then performs a domain-aware search.
        """
        if domain:
            filter_dict = {"primary_domain": domain}
            logger.info(f"Retrieving with explicit domain filter: '{domain}' for query: '{query}'")
            try:
                return self.vector_db.similarity_search_with_score(query, k=k, filter=filter_dict)
            except Exception as e:
                logger.error(f"Retrieval failed: {e}")
                return []

        logger.info(f"No explicit domain provided; classifying query before retrieval: '{query}'")
        primary_domain, secondary_domains, secondary_tags = self._classify_query_for_retrieval(query)
        return self.retrieve_with_metadata_filter(query, primary_domain, secondary_domains, secondary_tags, k=k)

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
            print(f"\nChunk {i+1} | Boosted Distance: {distance:.4f} | Source: {meta.get('source_file')} | Page: {meta.get('page')}")
            print(f"Domain: {meta.get('primary_domain')} | Secondary Tags: [{meta.get('secondary_tags')}]")
            print("-" * 80)
            content_snippet = doc.page_content.replace("\n", " ")[:200]
            print(f"Snippet: {content_snippet}...")
        print("="*80 + "\n")

    def retrieve_with_metadata_filter(self, query: str, primary_domain: str, secondary_domains: List[str], secondary_tags: List[str], k: int = 4) -> List[Tuple[Document, float]]:
        """
        Retrieves top-k relevant chunks filtered by primary and secondary domains,
        and then scores/re-ranks them based on match with secondary tags.
        """
        # Fetch more candidates to allow filtering/re-ranking by secondary tags
        candidate_k = max(k * 2, 10)
        
        # Combine primary and secondary domains for the filter
        all_domains = [primary_domain] + [d for d in secondary_domains if d != primary_domain]
        filter_dict = {"primary_domain": {"$in": all_domains}}
        
        logger.info(f"Retrieving from domains {all_domains} with candidate_k={candidate_k} for query: '{query}'")
        try:
            candidates = self.vector_db.similarity_search_with_score(query, k=candidate_k, filter=filter_dict)
        except Exception as e:
            logger.error(f"Retrieval with filter failed: {e}")
            candidates = []

        if not candidates:
            return []

        # Re-rank/prioritize candidates based on domain match, secondary tags overlap, and query keyword/acronym overlap
        scored_candidates = []
        import re
        query_words = set(re.findall(r'\b[A-Za-z0-9&\-\.]{2,}\b', query))
        key_query_terms = set()
        for w in query_words:
            if w.isupper() or any(c.isdigit() for c in w) or w.lower() in ['dean', 'warden', 'committee', 'scholarship', 'vlsi', 'curriculum', 'eligibility']:
                key_query_terms.add(w.lower())

        for doc, distance in candidates:
            doc_tags_str = doc.metadata.get("secondary_tags", "")
            doc_tags = [t.strip().lower() for t in doc_tags_str.split(",") if t.strip()]
            
            # Count matches between query secondary tags and document secondary tags
            matches = sum(1 for tag in secondary_tags if tag in doc_tags) if secondary_tags else 0
            
            # Domain-based boost: Lower distance is better in Chroma
            doc_domain = doc.metadata.get("primary_domain")
            domain_boost = 0.0
            if doc_domain == primary_domain:
                domain_boost = 0.05
            elif doc_domain in secondary_domains:
                domain_boost = 0.02
                
            # Count matches of key query terms in the chunk content
            doc_content_lower = doc.page_content.lower()
            keyword_matches = sum(1 for term in key_query_terms if term in doc_content_lower) if key_query_terms else 0
            keyword_boost = 0.03 * keyword_matches

            boosted_distance = max(0.0, distance - (0.05 * matches) - domain_boost - keyword_boost)
            scored_candidates.append((doc, boosted_distance, matches, doc_domain))

        # Sort by boosted distance (ascending)
        scored_candidates.sort(key=lambda x: x[1])

        # Return the top-k documents (removing extra metadata from the tuple)
        return [(doc, dist) for doc, dist, matches, domain in scored_candidates[:k]]

    def retrieve_with_llm_domain_classification(self, query: str, k: int = 4) -> List[Tuple[Document, float]]:
        """
        Main workflow: Query → LLM Domain Classification → Search
        """
        logger.info(f"Starting LLM-based domain classification for query: '{query}'")
        primary_domain, secondary_domains, secondary_tags = self._classify_query_for_retrieval(query)

        results = self.retrieve_with_metadata_filter(query, primary_domain, secondary_domains, secondary_tags, k=k)
        logger.info(f"Search complete. Retrieved {len(results)} documents for primary_domain='{primary_domain}'")
        return results

    def retrieve_for_agent(self, agent_role: str, task_description: str, queries: Optional[List[str]] = None, k: int = 4) -> str:
        """
        High-level agent retrieval interface.
        Uses query-first LLM classification to determine primary and secondary domains, then performs ChromaDB retrieval.
        """
        if queries:
            query_text = " ".join(queries)
        else:
            query_text = task_description

        logger.info(f"Retrieving for agent role '{agent_role}' with query: '{query_text}'")

        if queries:
            results = []
            for query in queries:
                results.extend(self.retrieve_with_llm_domain_classification(query, k=k))
            results = self._dedupe_and_sort(results, max_total=k)
        else:
            results = self.retrieve_with_llm_domain_classification(task_description, k=k)

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
