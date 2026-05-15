"""
Unit tests for SQLAlchemy Unit of Work implementation.

Tests transaction management, repository coordination, and error handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.shared.infrastructure.unit_of_work_impl import SqlAlchemyUnitOfWork


class TestSqlAlchemyUnitOfWork:
    """Test suite for SqlAlchemyUnitOfWork."""
    
    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def uow(self, mock_session):
        """Create UnitOfWork instance with mock session."""
        return SqlAlchemyUnitOfWork(mock_session)
    
    # === Repository Access Tests ===
    
    @pytest.mark.asyncio
    async def test_projects_repository_lazy_initialization(self, uow):
        """Test that projects repository is lazily initialized."""
        # Repository should not exist initially
        assert uow._projects is None
        
        # Access should create it
        repo = uow.projects
        assert repo is not None
        
        # Second access should return same instance
        assert uow.projects is repo
    
    @pytest.mark.asyncio
    async def test_stories_repository_lazy_initialization(self, uow):
        """Test that stories repository is lazily initialized."""
        assert uow._stories is None
        
        repo = uow.stories
        assert repo is not None
        assert uow.stories is repo
    
    @pytest.mark.asyncio
    async def test_users_repository_lazy_initialization(self, uow):
        """Test that users repository is lazily initialized."""
        assert uow._users is None
        
        repo = uow.users
        assert repo is not None
        assert uow.users is repo
    
    @pytest.mark.asyncio
    async def test_user_preferences_repository_lazy_initialization(self, uow):
        """Test that user preferences repository is lazily initialized."""
        assert uow._user_preferences is None
        
        repo = uow.user_preferences
        assert repo is not None
        assert uow.user_preferences is repo
    
    @pytest.mark.asyncio
    async def test_repositories_share_same_session(self, uow, mock_session):
        """Test that all repositories share the same session."""
        # Access multiple repositories
        projects_repo = uow.projects
        stories_repo = uow.stories
        users_repo = uow.users
        
        # All should use the same session (repositories use db_session attribute)
        assert projects_repo._session is mock_session
        assert stories_repo._session is mock_session
        assert users_repo.db_session is mock_session
    
    # === Context Manager Tests ===
    
    @pytest.mark.asyncio
    async def test_context_manager_enter(self, uow):
        """Test entering context manager."""
        async with uow as context_uow:
            assert context_uow is uow
    
    @pytest.mark.asyncio
    async def test_context_manager_successful_commit(self, uow, mock_session):
        """Test context manager with successful commit."""
        async with uow:
            await uow.commit()
        
        # Should have committed
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_context_manager_auto_rollback_on_exception(self, uow, mock_session):
        """Test context manager automatically rolls back on exception."""
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test exception")
        
        # Should have rolled back
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_context_manager_rollback_if_no_commit(self, uow, mock_session):
        """Test context manager rolls back if commit not called."""
        async with uow:
            # Do some work but don't commit
            _ = uow.projects
        
        # Should have rolled back
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
    
    # === Commit Tests ===
    
    @pytest.mark.asyncio
    async def test_commit_success(self, uow, mock_session):
        """Test successful commit."""
        async with uow:
            await uow.commit()
        
        assert uow._committed is True
        assert uow._rolled_back is False
        mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_commit_fails_if_already_committed(self, uow, mock_session):
        """Test that committing twice raises exception."""
        async with uow:
            await uow.commit()
            
            with pytest.raises(Exception, match="already committed"):
                await uow.commit()
    
    @pytest.mark.asyncio
    async def test_commit_fails_if_already_rolled_back(self, uow, mock_session):
        """Test that committing after rollback raises exception."""
        async with uow:
            await uow.rollback()
            
            with pytest.raises(Exception, match="already rolled back"):
                await uow.commit()
    
    @pytest.mark.asyncio
    async def test_commit_rolls_back_on_failure(self, uow, mock_session):
        """Test that failed commit triggers rollback."""
        # Make commit raise exception
        mock_session.commit.side_effect = Exception("Commit failed")
        
        with pytest.raises(Exception, match="Commit failed"):
            async with uow:
                await uow.commit()
        
        # Should have attempted rollback
        mock_session.rollback.assert_called_once()
        assert uow._rolled_back is True
    
    # === Rollback Tests ===
    
    @pytest.mark.asyncio
    async def test_rollback_success(self, uow, mock_session):
        """Test successful rollback."""
        async with uow:
            await uow.rollback()
        
        assert uow._rolled_back is True
        assert uow._committed is False
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_idempotent(self, uow, mock_session):
        """Test that multiple rollbacks are safe."""
        async with uow:
            await uow.rollback()
            await uow.rollback()  # Should not raise
        
        # Should only rollback once
        mock_session.rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rollback_raises_on_failure(self, uow, mock_session):
        """Test that rollback failure raises exception."""
        mock_session.rollback.side_effect = Exception("Rollback failed")
        
        with pytest.raises(Exception, match="Rollback failed"):
            async with uow:
                await uow.rollback()
    
    # === Integration Scenario Tests ===
    
    @pytest.mark.asyncio
    async def test_multi_repository_transaction_success(self, uow, mock_session):
        """Test successful transaction across multiple repositories."""
        async with uow:
            # Access multiple repositories
            projects_repo = uow.projects
            stories_repo = uow.stories
            
            # Verify they share session
            assert projects_repo._session is stories_repo._session
            
            # Commit transaction
            await uow.commit()
        
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_multi_repository_transaction_failure(self, uow, mock_session):
        """Test failed transaction rolls back all repositories."""
        with pytest.raises(ValueError):
            async with uow:
                # Access repositories
                _ = uow.projects
                _ = uow.stories
                
                # Simulate error during operation
                raise ValueError("Operation failed")
        
        # Should rollback, not commit
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_partial_commit_rolls_back_on_error(self, uow, mock_session):
        """Test that commit failure rolls back partial changes."""
        # Make commit fail
        mock_session.commit.side_effect = Exception("Constraint violation")
        
        with pytest.raises(Exception, match="Constraint violation"):
            async with uow:
                # Do some work
                _ = uow.projects
                _ = uow.stories
                
                # Attempt commit (will fail)
                await uow.commit()
        
        # Should have rolled back
        assert uow._rolled_back is True
        mock_session.rollback.assert_called_once()
    
    # === State Management Tests ===
    
    @pytest.mark.asyncio
    async def test_initial_state(self, uow):
        """Test initial UnitOfWork state."""
        assert uow._committed is False
        assert uow._rolled_back is False
        assert uow._projects is None
        assert uow._stories is None
        assert uow._users is None
        assert uow._user_preferences is None
    
    @pytest.mark.asyncio
    async def test_state_after_commit(self, uow, mock_session):
        """Test state flags after successful commit."""
        async with uow:
            await uow.commit()
        
        assert uow._committed is True
        assert uow._rolled_back is False
    
    @pytest.mark.asyncio
    async def test_state_after_rollback(self, uow, mock_session):
        """Test state flags after rollback."""
        async with uow:
            await uow.rollback()
        
        assert uow._committed is False
        assert uow._rolled_back is True
    
    @pytest.mark.asyncio
    async def test_state_after_exception(self, uow, mock_session):
        """Test state flags after exception."""
        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test")
        
        assert uow._committed is False
        assert uow._rolled_back is True
