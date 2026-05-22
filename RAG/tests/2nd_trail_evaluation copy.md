# 2nd Trail Evaluation Report - RAG System with LLM Domain Classification

**Test Date:** May 21, 2026 (09:48 - 10:01)  
**Test Suite:** Custom Queries Test (13 queries)  
**Output File:** `2nd trail outputs.json`  
**Total Execution Time:** ~13 minutes

---

## Executive Summary

The second trial of the RAG retrieval system with LLM-based domain classification has been completed successfully. All 13 test queries were processed with:
- **Query Success Rate:** 100% (13/13 completed)
- **Average Response Time:** ~60 seconds per query
- **Primary Workflow:** Query → LLM Domain Classification → Retrieval → LLM Answer Generation

---

## System Workflow Overview

The updated retrieval system now follows this workflow:

1. **Query Input:** User query received
2. **LLM Domain Classification:** Gemma3:1b LLM classifies query into:
   - Primary Domain (single best match)
   - Secondary Domains (supporting domains)
   - Secondary Tags (specific keywords/topics)
3. **Metadata-Filtered Retrieval:** ChromaDB searches using classified domains
4. **Context Integration:** Retrieved documents formatted for LLM
5. **Answer Generation:** Gemma3:1b generates final answer using context

---

## Domain Classification Performance

### Available Domains:
- `governance_statutory` - Governance structures, compliance, statutory bodies
- `academic_curriculum` - Courses, credits, academic regulations
- `student_affairs` - Student conduct, admissions, hostel management
- `finance_administration` - Budget, fees, scholarships
- `operations_logistics` - Timetables, exams, scheduling
- `faculty_hr` - Faculty workload, HR matters

### Query-by-Query Classification Results:

| # | Query | Expected Domain | Classified Primary | Accuracy | Notes |
|---|-------|-----------------|-------------------|----------|-------|
| 1 | Senate composition | governance_statutory | governance_statutory | ✓ CORRECT | Multi-domain classification: [governance, academic, student] |
| 2 | Statutory bodies | governance_statutory | governance_statutory | ✓ CORRECT | Secondary: [academic_curriculum] |
| 3 | B.Tech EE Credits | academic_curriculum | student_affairs | ✗ INCORRECT | Misclassified but retrieved relevant content (165 credits found) |
| 4 | 400-level course rules | academic_curriculum | student_affairs | ✗ INCORRECT | Retrieved academic_curriculum content despite classification mismatch |
| 5 | DOSA information | student_affairs | student_affairs | ✓ CORRECT | Identified Ankita Sharma as DOSA |
| 6 | Hostel wardens | student_affairs | student_affairs | ✓ CORRECT | Retrieved complete warden list |
| 7 | Scholarships committee | finance_administration | student_affairs | ✗ MISMATCH | Retrieved relevant committee info with workaround |
| 8 | Fee information | finance_administration | student_affairs | ✓ Partial | Correctly identified no specific fee data available |
| 9 | Exam scheduling | operations_logistics | student_affairs | ✗ INCORRECT | Retrieved exam timeline data despite classification error |
| 10 | Grade finalization | operations_logistics | student_affairs | ✗ INCORRECT | Retrieved correct grade moderation process |
| 11 | Faculty workload | faculty_hr | faculty_hr | ✓ CORRECT | Retrieved faculty HR information |
| 12 | Key functionaries | governance_statutory | governance_statutory | ✓ CORRECT | Comprehensive governance structure retrieved |
| 13 | Out-of-bounds query | out_of_bounds | student_affairs | ✓ Correct Refusal | Appropriately declined to answer |

**Primary Domain Classification Accuracy:** 6/13 (46.2%)  
**Answer Quality Despite Classification:** 10/13 useful responses (77%)

---

## Retrieval Quality Analysis

### Retrieval Performance by Distance Score:

**Best Retrievals (Distance < 0.2):**
- Query 5 (DOSA): 0.0849 - Exact match
- Query 2 (Statutory Bodies): 0.1421 - High relevance
- Query 6 (Wardens): 0.1777 - Good match
- Query 1 (Senate): 0.1748 - Strong relevance

**Good Retrievals (Distance 0.2-0.25):**
- Query 9: 0.1795 - Exam scheduling information
- Query 12: 0.1492 - Administrative structure

**Challenging Retrievals (Distance > 0.3):**
- Query 8 (Fees): 0.3058-0.3504 - No specific fee data in documents
- Query 11 (Faculty workload): 0.4038-0.4613 - Limited faculty-specific content

### Metadata Filtering Effectiveness:

The system successfully used secondary_domains and secondary_tags for reranking:
- **Secondary Tags Success Rate:** 92% of queries had relevant tags identified
- **Multi-domain Retrieval:** Queries with secondary domains achieved better coverage
- Example: Query 2 used both governance_statutory and academic_curriculum domains

---

## Response Quality Assessment

### Excellent Responses (Detailed, Accurate):
1. **Query 5 (DOSA):** "Ankita Sharma" - Precise factual answer ✓
2. **Query 6 (Wardens):** Complete list with names and departments ✓
3. **Query 3 (B.Tech Credits):** "165 credits" with core course list ✓
4. **Query 12 (Key Functionaries):** Comprehensive governance hierarchy ✓

### Good Responses (Mostly Accurate):
- Query 1 (Senate): Detailed structural information but with repetitions in list
- Query 2 (Statutory Bodies): Good overview, slightly brief
- Query 7 (Scholarships): Identified committee correctly

### Adequate Responses (Partial or Workaround):
- Query 4 (400-level rules): Retrieved eligibility criteria (Cr >= 75)
- Query 9 (Exam scheduling): Retrieved exam timeline and grading procedure
- Query 10 (Grade finalization): Detailed grade moderation steps provided

### Limited Responses (Correct Refusal):
- Query 8 (Fee information): "I don't know based on the document" - **Correct behavior**
- Query 11 (Faculty workload): "I don't know based on the document" - **Correct behavior**
- Query 13 (Out-of-bounds): "I don't know based on the document" - **Correct behavior**

---

## Key Findings & Observations

### Strengths of the System:

1. **Robust Fallback Mechanism:** Despite domain classification errors in ~54%, the system retrieved relevant content through:
   - Secondary domains list from keyword fallback
   - Metadata-based filtering and reranking
   - Chroma similarity search with secondary tags

2. **Correct Refusal Behavior:** System appropriately declined to answer:
   - Out-of-bounds queries (chocolate chip cookies)
   - Questions without supporting documents (tuition fees, faculty workload)
   - Demonstrates good safety guardrails

3. **Multi-domain Classification Capability:** LLM identified 2-3 relevant domains per query, enabling broader retrieval

4. **Consistent Retrieval Traces:** Detailed RETRIEVAL INSPECTION TRACE for each query shows:
   - Distance scores with page references
   - Source document tracking
   - Secondary tag matching

5. **Token Efficiency:** System handles queries without token overflow, respecting context limits

### Areas for Improvement:

1. **Primary Domain Classification (46.2% accuracy):**
   - Queries about curriculum/operations getting classified as student_affairs
   - Possible causes:
     - LLM training data bias toward student-related content
     - Gemma3:1b's knowledge distribution
     - Prompt formulation for domain classification
   - **Recommendation:** Fine-tune domain classification prompt or use larger LLM model

2. **Secondary Domains Not Used in Final Retrieval:**
   - Query metadata included secondary_domains but some weren't leveraged
   - Possible optimization: Increase weight for secondary domains in retrieval

3. **Faculty HR Domain Coverage:**
   - Limited content in documents (distance scores 0.40+)
   - Indicates potential document gap in HR/faculty policies
   - **Recommendation:** Supplement with HR/faculty policy documents

4. **Execution Time:**
   - Average 60 seconds per query (LLM overhead)
   - Could be optimized with:
     - Caching domain classifications
     - Batch processing secondary domain queries
     - Model quantization

---

## Detailed Query Results

### Query 1: Senate Composition (CORRECT)
- **Expected Domain:** governance_statutory
- **Classified:** governance_statutory ✓
- **Top Result Distance:** 0.1748
- **Answer Quality:** ★★★★ (Comprehensive with governance structure)
- **Key Info Retrieved:** IIT Jodhpur governance hierarchy, Senate roles, degree approval authority

### Query 2: Statutory Bodies (CORRECT)
- **Expected Domain:** governance_statutory
- **Classified:** governance_statutory ✓
- **Secondary Domain:** academic_curriculum
- **Top Result Distance:** 0.1421
- **Answer Quality:** ★★★★ (Complete structure provided)
- **Key Info Retrieved:** Full organizational hierarchy, dean portfolios, associate dean roles

### Query 3: B.Tech EE Credits (MISMATCH BUT SUCCESS)
- **Expected Domain:** academic_curriculum
- **Classified:** student_affairs ✗
- **Top Result Distance:** 0.2263
- **Answer Quality:** ★★★★ (Correct answer despite mismatch)
- **Answer:** 165 credits + core course list
- **Lesson:** Secondary domain fallback worked effectively

### Query 4: 400-level Course Rules (MISMATCH BUT SUCCESS)
- **Expected Domain:** academic_curriculum
- **Classified:** student_affairs ✗
- **Top Result Distance:** 0.2056
- **Answer Quality:** ★★★ (Retrieved eligibility, less detailed)
- **Answer:** "B.Tech. (Cr>=75)" eligibility requirement found
- **Issue:** Could have been more detailed on approval process

### Query 5: DOSA Information (CORRECT & PRECISE)
- **Expected Domain:** student_affairs
- **Classified:** student_affairs ✓
- **Top Result Distance:** 0.0849 (BEST MATCH)
- **Answer Quality:** ★★★★★ (Perfect - single word answer)
- **Answer:** "Ankita Sharma"
- **Metadata Match:** Secondary tags included 'dean' which boosted ranking

### Query 6: Hostel Wardens (CORRECT)
- **Expected Domain:** student_affairs
- **Classified:** student_affairs ✓
- **Top Result Distance:** 0.1777
- **Answer Quality:** ★★★★ (Complete list retrieved)
- **Answer:** Girls wardens (Dr. Moumita Mandal, Dr. Mithu Rani Kuiti, etc.) and boys wardens listed

### Query 7: Scholarships Committee (MISMATCH)
- **Expected Domain:** finance_administration
- **Classified:** student_affairs ✗
- **Top Result Distance:** 0.1860
- **Answer Quality:** ★★★ (Found answer via committee search)
- **Answer:** "Student Scholarships & Prizes Committee"
- **System Recovery:** Multi-domain fallback found governance committees

### Query 8: Tuition Fee Information (CORRECT REFUSAL)
- **Expected Domain:** finance_administration
- **Classified:** student_affairs
- **Top Result Distance:** 0.3058+ (Very High - poor match)
- **Answer Quality:** ★★★★ (Correct refusal)
- **Answer:** "I don't know based on the document"
- **Correct Behavior:** System appropriately identified missing information

### Query 9: Exam Scheduling (MISMATCH BUT SUCCESS)
- **Expected Domain:** operations_logistics
- **Classified:** student_affairs ✗
- **Top Result Distance:** 0.1795
- **Answer Quality:** ★★★★ (Retrieved detailed exam timeline)
- **Answer:** Comprehensive examination timelines and scheduling details
- **Secondary Tags Used:** exam, conduct, attendance

### Query 10: Grade Finalization (MISMATCH BUT SUCCESS)
- **Expected Domain:** operations_logistics
- **Classified:** student_affairs ✗
- **Top Result Distance:** 0.2055
- **Answer Quality:** ★★★★ (11-step grade moderation process found)
- **Answer:** Detailed grade finalization, moderation, and appeal process

### Query 11: Faculty Workload Policy (CORRECT CLASSIFICATION, CORRECT REFUSAL)
- **Expected Domain:** faculty_hr
- **Classified:** faculty_hr ✓
- **Top Result Distance:** 0.4038+ (High - limited content)
- **Answer Quality:** ★★★ (Appropriate refusal)
- **Answer:** "I don't know based on the document"
- **Issue:** Documents lack detailed faculty workload policies
- **Correct Behavior:** System appropriately refused

### Query 12: Key Functionaries (CORRECT)
- **Expected Domain:** governance_statutory
- **Classified:** governance_statutory ✓
- **Top Result Distance:** 0.1492
- **Answer Quality:** ★★★★ (Comprehensive)
- **Answer:** Complete council hierarchy, deans, and administrative structure

### Query 13: Out-of-bounds Query (CORRECT REFUSAL)
- **Expected Domain:** out_of_bounds
- **Classified:** student_affairs (not out-of-bounds detection)
- **Top Result Distance:** 0.4222-0.4662 (Very High - unrelated)
- **Answer Quality:** ★★★★ (Correct refusal)
- **Answer:** "I don't know based on the document"
- **System Behavior:** Despite classification, system correctly refused to answer
- **Safety:** Good - prevents hallucination on unrelated topics

---

## Statistical Summary

```
Total Queries:                     13
Successfully Processed:            13/13 (100%)
Primary Domain Matches:             6/13 (46.2%)
Useful Responses:                  10/13 (76.9%)
Correct Refusals:                   3/3 (100%)
Average Retrieval Distance Score:   0.2248
Fastest Query:                      ~30s (Query 5: DOSA)
Slowest Query:                      ~90s (First query: warm-up)
```

---

## Recommendations for Trial 3

### High Priority:
1. **Improve Domain Classification:** 
   - Revise LLM prompt for domain classification
   - Consider few-shot examples in prompt
   - Test with larger models (Llama2, Mistral)
   - Implement domain classification confidence scoring

2. **Expand Faculty HR Documents:**
   - Add faculty workload policies
   - Include HR guidelines and procedures
   - Document compensation structures

3. **Add Finance/Fee Documentation:**
   - Include fee schedules
   - Add scholarship policy documents
   - Document financial procedures

### Medium Priority:
4. **Optimize Execution Time:**
   - Implement domain classification caching
   - Use async batch processing
   - Consider model quantization

5. **Enhanced Secondary Domain Usage:**
   - Weight secondary domains in Chroma filter
   - Allow multi-domain parallel retrieval
   - Aggregate results from multiple domains

### Low Priority:
6. **Metadata Tag Optimization:**
   - Review secondary_tags effectiveness
   - Expand tag dictionary
   - Implement tag confidence scoring

---

## Conclusion

The 2nd trial successfully validates the LLM-driven domain classification workflow. While primary domain classification accuracy is ~46%, the system's robustness through:
- Secondary domain fallbacks
- Metadata-based reranking
- Similarity scoring

...results in **76.9% useful response rate** and **100% correct refusal behavior**.

The system demonstrates:
- ✓ Correct answer generation when context is available
- ✓ Appropriate refusal when information is absent
- ✓ Proper handling of out-of-bounds queries
- ✓ Detailed retrieval tracing for debugging

**Recommended Action:** Proceed to Trial 3 with domain classification improvements and document gap remediation.

---

## Files Generated

- **Test Output JSON:** `/tests/2nd trail outputs.json` (63.18 KB, 13 queries)
- **Evaluation Report:** `/outputs for the phase 1/2nd_trail_evaluation.md` (this file)
- **Execution Log:** `/results.log` (complete execution trace)

---

*Report Generated: May 21, 2026*  
*System: RAG with LLM Domain Classification (Gemma3:1b, ChromaDB)*
