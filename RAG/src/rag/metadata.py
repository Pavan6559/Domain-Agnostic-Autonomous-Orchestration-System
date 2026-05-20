import re
from typing import Dict, Any, List
from langchain_ollama import OllamaLLM
from .utils import get_logger

logger = get_logger("MetadataTagger")

class MetadataTagger:
    """Helper class to tag text chunks with metadata using LLM for domain-aware retrieval."""

    # Primary domains based on institutional structure (from Statutory_bodies_and_key_functionaries.pdf)
    PRIMARY_DOMAINS = [
        'governance_statutory',      # Statutory bodies, governance structure, compliance
        'academic_curriculum',       # Curriculum, courses, credits, syllabus, academic regulations
        'student_affairs',           # Student conduct, discipline, admissions, hostel
        'finance_administration',    # Budget, fees, scholarships, financial matters
        'operations_logistics',      # Timetable, exam schedule, venues, facilities
        'faculty_hr',               # Faculty workload, staff, HR matters, faculty responsibilities
    ]

    # Fallback keyword mappings for domain classification (used when LLM is unavailable)
    DOMAIN_KEYWORDS = {
        'governance_statutory': ['statutory', 'governance', 'committee', 'nba', 'naac', 'accreditation', 'senate', 'council', 'board'],
        'academic_curriculum': ['curriculum', 'credit', 'ugc', 'syllabus', 'course', 'degree', 'academic', 'b.tech', 'module'],
        'student_affairs': ['student', 'conduct', 'discipline', 'hostel', 'admission', 'warden', 'grievance', 'welfare'],
        'finance_administration': ['fee', 'finance', 'budget', 'tuition', 'scholarship', 'prize', 'award', 'funding', 'payment'],
        'operations_logistics': ['timetable', 'schedule', 'exam', 'venue', 'calendar', 'date', 'timing', 'slot', 'class'],
        'faculty_hr': ['faculty', 'workload', 'staff', 'hod', 'professor', 'salary', 'liaison', 'duty']
    }

    SECONDARY_TAG_LIST = [
        'vlsi', 'credits', 'curriculum', 'hostel', 'warden', 'dean', 'scholarship', 
        'tuition', 'syllabus', 'accreditation', 'exam', 'governance', 'ugc', 'naac',
        'admissions', 'conduct', 'discipline', 'grading', 'attendance', 'fees', 'senate',
        'committee', 'statutory', 'compliance', 'grievance', 'appeal'
    ]

    # Batch cache to avoid redundant LLM calls
    _domain_cache = {}
    _llm_instance = None
    _use_llm = True

    @classmethod
    def get_llm(cls) -> OllamaLLM:
        """Lazy-load LLM instance."""
        if cls._llm_instance is None:
            try:
                cls._llm_instance = OllamaLLM(model="gemma3:1b")
                logger.info("LLM initialized successfully for metadata tagging")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}. Falling back to keyword matching.")
                cls._use_llm = False
        return cls._llm_instance

    @classmethod
    def normalize_domain(cls, raw_domain: str, fallback_text: str, filename: str = "query") -> str:
        """Validates one LLM domain response and falls back to keyword scoring when needed."""
        domain = raw_domain.strip().lower()
        if domain in cls.PRIMARY_DOMAINS:
            return domain

        for valid_domain in cls.PRIMARY_DOMAINS:
            if valid_domain in domain:
                return valid_domain

        return cls.determine_domain_keyword_fallback(filename, fallback_text)

    @classmethod
    def normalize_domains(cls, raw_domains: str, fallback_text: str, max_domains: int = 3) -> List[str]:
        """Validates a comma/newline-separated LLM domain response for multi-domain retrieval."""
        response = raw_domains.strip().lower()
        selected = []

        for domain in cls.PRIMARY_DOMAINS:
            if domain in response:
                selected.append(domain)

        if not selected:
            selected = cls.determine_domains_keyword_fallback(fallback_text, max_domains=max_domains)

        return selected[:max_domains]

    @classmethod
    def determine_domain_with_llm(cls, filename: str, chunk_text: str) -> str:
        """
        Uses LLM to intelligently classify text chunk into one of the primary domains.
        Falls back to keyword matching if LLM fails.
        """
        # Check cache first
        cache_key = hash((filename, chunk_text[:100]))
        if cache_key in cls._domain_cache:
            return cls._domain_cache[cache_key]

        if not cls._use_llm:
            return cls.determine_domain_keyword_fallback(filename, chunk_text)

        try:
            domains_str = ", ".join(cls.PRIMARY_DOMAINS)
            prompt = f"""Classify this text chunk into ONE primary domain. Choose the BEST fit from: {domains_str}

File: {filename}
Text: {chunk_text[:500]}

Respond with ONLY the domain name, nothing else."""
            
            domain = cls.normalize_domain(
                raw_domain=cls.get_llm().invoke(prompt),
                fallback_text=chunk_text,
                filename=filename
            )
            
            cls._domain_cache[cache_key] = domain
            logger.debug(f"LLM classified '{filename}' -> {domain}")
            return domain
            
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}. Using keyword fallback.")
            cls._use_llm = False
            return cls.determine_domain_keyword_fallback(filename, chunk_text)

    @classmethod
    def determine_domain_keyword_fallback(cls, filename: str, chunk_text: str) -> str:
        """
        Fallback keyword-based domain classification when LLM is unavailable.
        """
        fn_lower = filename.lower()
        text_lower = chunk_text.lower()

        # Phase 1: Filename keyword matching (highest priority)
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            if any(k in fn_lower for k in keywords):
                return domain

        # Phase 2: Content keyword frequency matching
        domain_scores = {d: 0 for d in cls.DOMAIN_KEYWORDS.keys()}
        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            for kw in keywords:
                count = len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower))
                domain_scores[domain] += count

        max_score = 0
        best_domain = 'governance_statutory'  # Default primary domain
        for domain, score in domain_scores.items():
            if score > max_score:
                max_score = score
                best_domain = domain

        return best_domain

    @classmethod
    def determine_domains_keyword_fallback(cls, text: str, max_domains: int = 3) -> List[str]:
        """Fallback query classifier that can return multiple relevant domains."""
        text_lower = text.lower()
        domain_scores = {}

        for domain, keywords in cls.DOMAIN_KEYWORDS.items():
            score = 0
            for kw in keywords:
                score += len(re.findall(r'\b' + re.escape(kw) + r'\b', text_lower))
            if score > 0:
                domain_scores[domain] = score

        if not domain_scores:
            return ['governance_statutory']

        ranked_domains = sorted(domain_scores.items(), key=lambda item: item[1], reverse=True)
        return [domain for domain, _ in ranked_domains[:max_domains]]

    @classmethod
    def classify_query_domains(cls, query: str, max_domains: int = 3) -> List[str]:
        """
        Classifies a user/agent query into one or more primary domains before retrieval.
        Cross-domain questions can search multiple scoped groups of chunks.
        """
        cache_key = hash(("query_domains", query[:200], max_domains))
        if cache_key in cls._domain_cache:
            return cls._domain_cache[cache_key]

        if not cls._use_llm:
            return cls.determine_domains_keyword_fallback(query, max_domains=max_domains)

        try:
            domains_str = ", ".join(cls.PRIMARY_DOMAINS)
            prompt = f"""Classify this search query into up to {max_domains} relevant primary domains.
Choose ONLY from: {domains_str}

Query: {query[:500]}

Respond with ONLY comma-separated domain names. If one domain is enough, return one domain."""

            domains = cls.normalize_domains(
                raw_domains=cls.get_llm().invoke(prompt),
                fallback_text=query,
                max_domains=max_domains
            )

            cls._domain_cache[cache_key] = domains
            logger.info(f"Query classified into domains: {domains}")
            return domains

        except Exception as e:
            logger.warning(f"Query domain classification failed: {e}. Using keyword fallback.")
            cls._use_llm = False
            return cls.determine_domains_keyword_fallback(query, max_domains=max_domains)

    @classmethod
    def classify_query_domain(cls, query: str) -> str:
        """Backward-compatible single-domain query classifier."""
        return cls.classify_query_domains(query, max_domains=1)[0]

    @classmethod
    def extract_secondary_tags_with_llm(cls, chunk_text: str) -> List[str]:
        """
        Uses LLM to extract relevant secondary tags and entities from the chunk.
        """
        if not cls._use_llm:
            return cls.extract_secondary_tags_keyword_fallback(chunk_text)

        try:
            tags_str = ", ".join(cls.SECONDARY_TAG_LIST)
            prompt = f"""Extract relevant tags from this text. Choose from: {tags_str}

Text: {chunk_text[:500]}

Respond with ONLY comma-separated tag names, nothing else. If no tags match, respond with: none"""
            
            response = cls.get_llm().invoke(prompt).strip().lower()
            
            if response == 'none':
                return []
            
            # Parse comma-separated tags
            tags = [tag.strip() for tag in response.split(',')]
            # Filter to only valid tags
            tags = [tag for tag in tags if tag in cls.SECONDARY_TAG_LIST]
            
            logger.debug(f"Extracted secondary tags: {tags}")
            return tags
            
        except Exception as e:
            logger.warning(f"LLM tag extraction failed: {e}. Using keyword fallback.")
            cls._use_llm = False
            return cls.extract_secondary_tags_keyword_fallback(chunk_text)

    @classmethod
    def extract_secondary_tags_keyword_fallback(cls, chunk_text: str) -> List[str]:
        """Fallback keyword-based tag extraction."""
        text_lower = chunk_text.lower()
        tags = []
        for tag in cls.SECONDARY_TAG_LIST:
            if re.search(r'\b' + re.escape(tag), text_lower):
                tags.append(tag)
        return tags

    @classmethod
    def generate_metadata(
        cls,
        filename: str,
        page_number: int,
        chunk_text: str,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        Generates the standard metadata dictionary for ChromaDB.
        Ingestion defaults to keyword tagging because calling an LLM for every chunk is slow.
        Serializes secondary tags as a comma-separated string due to ChromaDB limitations.
        """
        if use_llm:
            primary_domain = cls.determine_domain_with_llm(filename, chunk_text)
            secondary_tags_list = cls.extract_secondary_tags_with_llm(chunk_text)
        else:
            primary_domain = cls.determine_domain_keyword_fallback(filename, chunk_text)
            secondary_tags_list = cls.extract_secondary_tags_keyword_fallback(chunk_text)
        
        # Serialize list to comma-separated string to comply with ChromaDB specifications
        secondary_tags_str = ",".join(secondary_tags_list) if secondary_tags_list else ""

        return {
            "primary_domain": primary_domain,
            "secondary_tags": secondary_tags_str,
            "source_file": filename,
            "page": page_number
        }
