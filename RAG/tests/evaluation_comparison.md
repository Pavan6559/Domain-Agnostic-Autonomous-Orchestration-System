# Evaluation Comparison: 1st Trial vs. 2nd Trial (RAG System)

This document compares the performance of the Retrieval-Augmented Generation (RAG) system between its **1st Trial (Keyword-Based Baseline)** and **2nd Trial (LLM-Enhanced Domain Classification)**.

---

## 📊 Summary of High-Level Metrics

| Metric | 1st Trial (Keyword Baseline) | 2nd Trial (LLM-Enhanced) | Delta / Impact |
| :--- | :--- | :--- | :--- |
| **Query Success Rate** | 100% (13/13 completed) | 100% (13/13 completed) | No change (Stable workflow) |
| **Primary Domain Classification Accuracy** | ~54.0% | 46.2% | **-7.8%** ⚠️ (LLM domain classification struggled more with primary tags than keywords) |
| **Useful Response Rate** | 61.5% (8/13 responses) | 76.9% (10/13 responses) | **+15.4%** 🚀 (Significant improvement in generation quality and context usage) |
| **Factual Hallucinations** | 1 (Query 3: credits) | 0 | **Reduced to 0** 🎉 (Corrected the critical 120 vs. 165 B.Tech credit error) |
| **Incomplete/Truncated Answers** | 3 (Queries 6, 10, 12) | 0 | **Resolved** (LLM answers are now complete and fully detailed) |
| **Correct Refusals** | 100% (3/3) | 100% (3/3) | No change (Kept safe refusals for out-of-scope/unsupported queries) |
| **Processing Time** | Not recorded | ~13 minutes (~60s/query) | Gemma3:1b classification & generation adds latency |

---

## 🔍 Key Architectural Differences

### 1st Trial (Traditional Baseline)
* **Classification:** Matches queries against predefined keyword dictionaries.
* **Retrieval:** Standard ChromaDB query based on the matched domain without secondary reranking.
* **Answer Generation:** Gemma3:1b reads context and generates answers.
* **Result:** Fast and deterministic classification, but prone to hallucinations, incomplete retrieval, and context underutilization.

### 2nd Trial (LLM-Enhanced System)
* **Classification:** Gemma3:1b classifies query into:
  1. *Primary Domain* (single best match)
  2. *Secondary Domains* (supporting domains)
  3. *Secondary Tags* (specific keywords/topics)
* **Retrieval:** ChromaDB query using primary/secondary domains and secondary tags for reranking and metadata-based filtering.
* **Answer Generation:** Gemma3:1b uses structured context to generate answers.
* **Result:** Higher latency and slightly lower primary domain matching accuracy, but **highly resilient retrieval** (recovers from domain classification errors) and **higher quality, hallucination-free generation**.

---

## 📋 Query-by-Query Breakdown

The test suite consists of 13 custom queries. The following table tracks how each query performed under both systems:

| Query ID & Prompt | Expected Domain | 1st Trial Performance | 2nd Trial Performance | Comparison / Key Improvement |
| :--- | :--- | :--- | :--- | :--- |
| **Q1: Senate Composition** | `governance_statutory` | **✓ Partial** classification. Good context retrieved. Verbose/redundant answer. | **✓ Correct** classification. Good context. Detailed and structured answer. | Better answer structure and less redundancy in the 2nd trial. |
| **Q2: Statutory Bodies** | `governance_statutory` | **✓ Partial** classification. Great context, but LLM only outputted "IIT Jodhpur". | **✓ Correct** classification. Detailed overview including deans & associate deans. | **Major Improvement.** 2nd trial successfully synthesized the retrieved context. |
| **Q3: B.Tech EE Credits** | `academic_curriculum` | **✓ Correct** classification. **Critical Hallucination:** Claimed 120 credits (context stated 165). | **✗ Incorrect** classification (student_affairs). **Recovery:** Fallback found 165 credits. | **Factual Accuracy.** Hallucination resolved in the 2nd trial due to better prompting/reranking. |
| **Q4: 400-level Course Rules** | `academic_curriculum` | **✗ Incorrect** classification. Retrieved PhD rules instead of B.Tech. Refused to answer. | **✗ Incorrect** classification (student_affairs). **Recovery:** Retrieved eligibility (Cr>=75). | **Resilience.** Fallback mechanisms rescued the retrieval process in the 2nd trial. |
| **Q5: DOSA Information** | `student_affairs` | **✓ Correct** classification. Perfect answer: "Ankita Sharma". | **✓ Correct** classification. Perfect answer: "Ankita Sharma". | Equally excellent performance in both trials. |
| **Q6: Hostel Wardens** | `student_affairs` | **✓ Correct** classification. Only outputted 5 of 18+ wardens (truncated list). | **✓ Correct** classification. Outputted complete list of wardens by boys/girls hostels. | **Answer Completeness.** Resolved the truncation issue in the 1st trial. |
| **Q7: Scholarships Committee** | `finance_administration` | **✗ Incorrect** classification. But keyword matching retrieved "Student Scholarships & Prizes". | **✗ Incorrect** classification (student_affairs). **Recovery:** Found committee via fallback. | Successful answers in both, but 2nd trial tracked retrieval trace with distance metrics. |
| **Q8: Tuition/Hostel Fees** | `finance_administration` | **✓ Partial** classification. Correctly refused (no fee data exists in documents). | **✓ Partial** classification. Correctly refused (no fee data exists in documents). | System appropriately refused speculative answers in both trials (safe behavior). |
| **Q9: Exam Scheduling** | `operations_logistics` | **✓ Partial** classification. Retrieved exam timelines, but answer was truncated. | **✗ Incorrect** classification (student_affairs). **Recovery:** Retrieved timeline using tags. | **Answer Completeness.** 2nd trial produced comprehensive scheduling details. |
| **Q10: Grade Finalization** | `operations_logistics` | **✓ Partial** classification. Retrieved 11-step process, but answer was truncated to 1-2 steps. | **✗ Incorrect** classification (student_affairs). **Recovery:** Retrieved full 11-step process. | **Answer Completeness.** 2nd trial successfully listed all 11 moderation steps. |
| **Q11: Faculty Workload** | `faculty_hr` | **✓ Partial** classification. Correctly refused (no policy data exists in documents). | **✓ Correct** classification. Correctly refused (no policy data exists in documents). | Correct refusal behavior maintained under both systems. |
| **Q12: Key Functionaries** | `governance_statutory` | **✓ Correct** classification. Comprehensive info but truncated in JSON output. | **✓ Correct** classification. Detailed and complete administrative structure output. | Resolved JSON serialization/truncation limits. |
| **Q13: Out-of-Bounds** | `out_of_bounds` | **N/A** classification. Correctly refused. | **✗ Incorrect** classification (student_affairs). Correctly refused due to distance threshold. | Correct safety and refusal preserved in both trials. |

---

## 📈 Detailed Comparison of Outcomes

### 1. Hallucination Prevention
* **Baseline Issue:** In the 1st trial, the system retrieved the correct text but generated an incorrect answer for Query 3 (claiming 120 credits instead of the documented 165 credits).
* **2nd Trial Resolution:** The LLM-driven domain classification and revised prompting completely eliminated hallucinations. The B.Tech EE program query successfully outputted the correct value (165 credits) along with the core course list.

### 2. Answer Completeness & Truncation
* **Baseline Issue:** Multiple queries (Q2 statutory bodies, Q6 wardens, Q10 grade finalization, Q12 key functionaries) had excellent context retrieved, but the generated answers were either empty, single-sentence, or truncated.
* **2nd Trial Resolution:** The 2nd trial resolved all truncation issues. For instance:
  * **Q6 (Wardens):** Listed all girls and boys wardens with departments rather than just 5.
  * **Q10 (Grade Finalization):** Outlined the entire 11-step moderation process.
  * **Q12 (Key Functionaries):** Returned the full administrative hierarchy.

### 3. Domain Classification vs. Fallback Resilience
* **Baseline Performance:** Pure keyword matching achieved ~54% classification accuracy. When classification failed, the system occasionally found the right files through overlap, but struggled on complex queries (like Q4).
* **2nd Trial Performance:** LLM primary domain classification was slightly lower (46.2%). Gemma3:1b tended to classify academic, operations, and finance queries as `student_affairs`.
* **The RAG Savior:** Even though domain classification was inaccurate, the **secondary domains** and **secondary tags** extracted by Gemma3:1b acted as highly effective fallback search criteria in ChromaDB. This enabled a **76.9% useful response rate**, meaning the system successfully retrieved the correct context despite classifying the query into the wrong domain.

---

## 🚀 Recommendations for Trial 3

To build on the strengths of Trial 2, the following improvements are recommended:

1. **Enhance Domain Classification (High Priority):**
   * Introduce *few-shot examples* in the domain classification LLM prompt to help Gemma3:1b distinguish between `academic_curriculum`, `operations_logistics`, and `student_affairs`.
   * Implement domain classification confidence scoring.
2. **Increase ChromaDB Weight for Secondary Domains:**
   * Optimize retrieval weights so that both primary and secondary domains contribute to context generation.
3. **Supplement Documentation Gaps:**
   * Add policy documents for Faculty HR (workload guidelines) and Finance (official fee schedules) to resolve correct refusals on valid queries.
4. **Reduce Latency:**
   * Implement caching for domain classification of common query patterns to reduce the average 60s response time.
