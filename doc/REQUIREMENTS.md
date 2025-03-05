Here's a product requirements document for an Agentic AI-driven report generation system using FastAPI:

## Objective
Develop an AI-powered report generation system that autonomously researches complex topics, structures findings, and produces polished Microsoft Word documents with minimal human intervention.

## Key Features

**1. Agentic AI Orchestration**
- Main Planner Agent that:
  - Interprets user queries using NLP (e.g., "build report on sustainable finance in Indonesia")
  - Creates execution plan with 3 phases: Research → Structuring → Content Generation
  - Delegates tasks to specialized sub-agents
  - Manages inter-agent communication and data flow

**2. Research Module**
- Web Research Agent:
  - Performs multi-source research from:
    - Government databases (Indonesia Financial Services Authority)
    - Academic repositories (Google Scholar)
    - Industry reports (MSCI ESG Ratings)
    - News sources
  - Verifies source credibility using domain-specific criteria
  - Maintains citation trail for all data points

**3. Document Structuring Engine**
- Template Agent that:
  - Generates logical document frameworks based on:
    ```python
    def create_template(topic):
        return {
            "sections": ["Executive Summary", "Methodology", "Market Analysis", 
                       "Regulatory Landscape", "Case Studies", "Recommendations"],
            "elements": ["headers", "charts", "comparative tables", 
                       "infographics", "references"]
        }
    ```
  - Adapts structure based on content type (e.g., add "Climate Risk Assessment" for ESG topics)

**4. Content Generation System**
- Team of specialized writing agents:
  - Data Visualization Agent: Creates charts/tables from research data
  - Narrative Agent: Writes explanatory text with proper academic tone
  - Compliance Agent: Ensures financial disclosure requirements
  - Formatting Agent: Applies APA/MLA styles as needed

**5. DOCX Compilation Module**
- Word Document Builder with:
  - Automatic table of contents generation
  - Dynamic pagination and section breaks
  - Embedded charts (PNG/SVG) with captions
  - Style-consistent headers (H1-H4)
  - Cross-referencing system for figures/tables
  - Reference section auto-generation

## Technical Requirements

**Core Architecture**
| Component          | Technology Stack         |
|--------------------|--------------------------|
| API Layer          | FastAPI + WebSockets     |
| AI Framework       | LangChain + LlamaIndex   |
| Document Processing| python-docx + Pandoc     |
| Data Storage       | PostgreSQL + Redis Cache |
| Task Queue         | Celery/RQ                |

**Performance Metrics**
1. Research Phase: = 5
    assert doc.tables.count >= 3
    assert similarity_score(doc) 85)
- <3% error rate in final documents
- Average report generation time <25 minutes
- 99.9% API uptime

This system requires careful implementation of concurrent agent orchestration while maintaining auditability in financial content generation. The technical stack prioritizes Python ecosystem compatibility while allowing for horizontal scaling through containerized microservices.

---
Answer from Perplexity: pplx.ai/share
