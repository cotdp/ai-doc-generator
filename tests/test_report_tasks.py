import os
import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch

from src.tasks.report_tasks import SqlAlchemyTask
from src.database.models import TaskStatus

# Test the SqlAlchemyTask class
def test_sqlalchemy_task_session():
    """Test the session property."""
    with patch('src.tasks.report_tasks.SessionLocal') as mock_session_local:
        # Setup mock session
        mock_db_session = MagicMock()
        mock_session_local.return_value = mock_db_session
        
        # Create task
        task = SqlAlchemyTask()
        
        # Test getting session
        session = task.session
        assert session == mock_db_session
        mock_session_local.assert_called_once()
        
        # Test getting session again (should reuse existing)
        session = task.session
        assert session == mock_db_session
        mock_session_local.assert_called_once()  # Still only called once
        
        # Test after_return cleanup
        task.after_return()
        mock_db_session.close.assert_called_once()
        assert task._session is None