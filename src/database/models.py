import datetime
import enum
from typing import Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class UserRole(enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    reports = relationship("Report", back_populates="user")


class TemplateType(enum.Enum):
    """Report template type enumeration."""
    STANDARD = "standard"
    ACADEMIC = "academic"
    BUSINESS = "business"


class ReportTemplate(Base):
    """Report template model."""
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    template_type = Column(Enum(TemplateType), default=TemplateType.STANDARD)
    description = Column(Text, nullable=True)
    structure = Column(JSON)  # JSON structure for the template
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    reports = relationship("Report", back_populates="template")


class TaskStatus(enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Report model."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)  # UUID for the task
    user_id = Column(Integer, ForeignKey("users.id"))
    template_id = Column(Integer, ForeignKey("report_templates.id"))
    topic = Column(String)
    max_pages = Column(Integer, default=10)
    include_images = Column(Boolean, default=True)
    file_path = Column(String, nullable=True)  # Path to the generated file
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    error = Column(Text, nullable=True)  # Error message if failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="reports")
    template = relationship("ReportTemplate", back_populates="reports")
    tasks = relationship("Task", back_populates="report")


class TaskType(enum.Enum):
    """Task type enumeration."""
    RESEARCH = "research"
    STRUCTURE = "structure"
    CONTENT = "content"
    IMAGE = "image"


class Task(Base):
    """Task model for tracking sub-tasks in report generation."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    task_type = Column(Enum(TaskType))
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    result_data = Column(JSON, nullable=True)  # JSON result data
    error = Column(Text, nullable=True)  # Error message if failed
    started_at = Column(DateTime, nullable=True)  # When the task started
    completed_at = Column(DateTime, nullable=True)  # When the task completed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    report = relationship("Report", back_populates="tasks")
