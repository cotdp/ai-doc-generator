from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportStatus(BaseModel):
    """Status of a report generation task."""

    id: str
    status: str
    topic: str
    error: Optional[str] = None
    progress: Optional[float] = 0.0


class ReportSection(BaseModel):
    """A section in the report."""

    title: str
    content: str
    subsections: Optional[List["ReportSection"]] = None
    images: Optional[List[Dict[str, str]]] = None
    tables: Optional[List[Dict[str, Any]]] = None


class ReportStructure(BaseModel):
    """The structure of a report."""

    title: str
    sections: List[ReportSection]
    metadata: Dict[str, Any]


class ReportRequest(BaseModel):
    """Request model for report generation."""

    topic: str
    template_type: str = Field(
        default="standard", description="Type of report template to use"
    )
    max_pages: int = Field(
        default=10, ge=1, le=50, description="Maximum number of pages"
    )
    include_images: bool = Field(
        default=True, description="Whether to include images in the report"
    )


class ResearchResult(BaseModel):
    """Result of research for a specific topic or question."""

    source: str
    content: str
    credibility_score: float = Field(ge=0.0, le=1.0)
    timestamp: str
    metadata: Dict[str, Any]
