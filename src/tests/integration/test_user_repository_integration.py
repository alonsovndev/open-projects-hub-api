"""
Integration tests for UserRepositoryImpl.

Tests user repository implementations including password hashing,
email uniqueness constraints, and complex queries.

Run with: pytest -m e2e
"""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.domain.value_objects.entity_id import EntityId


@pytest.mark.e2e
@pytest.mark.asyncio
class TestUserRepositoryIntegration:
    """Integration tests for UserRepository against real database."""

    async def test_save_creates_new_user(self, db_session: AsyncSession):
        """Test saving a new user creates database record."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Integration Test User",
            email=Email("integration@test.com"),
            password_hash="hashed_password_123",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        saved_user = await repository.save(user)
        await db_session.commit()

        # Assert
        assert saved_user is not None
        assert saved_user.id.value == user.id.value
        assert saved_user.display_name == "Integration Test User"
        assert saved_user.email.value == "integration@test.com"

    async def test_find_by_id_returns_saved_user(self, db_session: AsyncSession):
        """Test finding user by ID retrieves correct record."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Findable User",
            email=Email("findable@test.com"),
            password_hash="hashed_password",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()

        # Act
        found_user = await repository.find_by_id(user.id.value)

        # Assert
        assert found_user is not None
        assert found_user.id.value == user.id.value
        assert found_user.display_name == "Findable User"

    async def test_find_by_email_returns_correct_user(self, db_session: AsyncSession):
        """Test finding user by email works correctly."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Email Search User",
            email=Email("unique@email.com"),
            password_hash="hashed_password",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()

        # Act
        found = await repository.find_by_email("unique@email.com")

        # Assert
        assert found is not None
        assert found.email.value == "unique@email.com"
        assert found.display_name == "Email Search User"

    async def test_find_by_email_returns_none_for_nonexistent(self, db_session: AsyncSession):
        """Test finding nonexistent email returns None."""
        # Arrange
        repository = UserRepositoryImpl(db_session)

        # Act
        result = await repository.find_by_email("nonexistent@email.com")

        # Assert
        assert result is None

    async def test_email_uniqueness_constraint(self, clean_db: AsyncSession):
        """Test database enforces email uniqueness."""
        # Arrange
        repository = UserRepositoryImpl(clean_db)
        email = "duplicate@test.com"

        user1 = UserEntity(
            id=EntityId.generate(),
            display_name="First User",
            email=Email(email),
            password_hash="hash1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        user2 = UserEntity(
            id=EntityId.generate(),
            display_name="Second User",
            email=Email(email),
            password_hash="hash2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act & Assert
        await repository.save(user1)
        await clean_db.commit()

        # Attempt to save duplicate email should fail
        with pytest.raises((IntegrityError, Exception)):
            await repository.save(user2)
            await clean_db.commit()

    async def test_update_modifies_existing_user(self, db_session: AsyncSession):
        """Test updating user modifies database record."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Original Name",
            email=Email("original@test.com"),
            password_hash="original_hash",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        saved = await repository.save(user)
        await db_session.commit()

        # Act - Update the user
        saved.display_name = "Updated Name"
        saved.password_hash = "new_hash"
        await repository.save(saved)
        await db_session.commit()

        # Assert
        refetched = await repository.find_by_id(user.id.value)
        assert refetched is not None
        assert refetched.display_name == "Updated Name"
        assert refetched.password_hash == "new_hash"
        assert refetched.email.value == "original@test.com"  # Email unchanged

    async def test_delete_removes_user(self, db_session: AsyncSession):
        """Test deleting user removes database record."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="To Be Deleted",
            email=Email("delete@test.com"),
            password_hash="hash",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()

        # Act
        deleted = await repository.delete(user.id.value)
        await db_session.commit()

        # Assert
        assert deleted is True
        found = await repository.find_by_id(user.id.value)
        assert found is None

    async def test_exists_by_email_returns_true_for_existing(self, db_session: AsyncSession):
        """Test exists_by_email returns True for existing user."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Exists Test",
            email=Email("exists@test.com"),
            password_hash="hash",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()

        # Act
        exists = await repository.exists_by_email("exists@test.com")

        # Assert
        assert exists is True

    async def test_exists_by_email_returns_false_for_nonexistent(self, db_session: AsyncSession):
        """Test exists_by_email returns False for nonexistent email."""
        # Arrange
        repository = UserRepositoryImpl(db_session)

        # Act
        exists = await repository.exists_by_email("nonexistent@test.com")

        # Assert
        assert exists is False

    async def test_password_hash_is_stored_correctly(self, db_session: AsyncSession):
        """Test password hash is stored and retrieved correctly."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        password_hash = "$2b$12$KIXqQJ7b9pN8Y.8tXqQz0e9vZ5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z5Z5"

        user = UserEntity(
            id=EntityId.generate(),
            display_name="Password Test",
            email=Email("password@test.com"),
            password_hash=password_hash,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Act
        await repository.save(user)
        await db_session.commit()

        found = await repository.find_by_email("password@test.com")

        # Assert
        assert found is not None
        assert found.password_hash == password_hash

    async def test_find_all_returns_multiple_users(self, db_session: AsyncSession):
        """Test finding all users returns correct records."""
        # Arrange
        repository = UserRepositoryImpl(db_session)

        user1 = UserEntity(
            id=EntityId.generate(),
            display_name="User One",
            email=Email("one@test.com"),
            password_hash="hash1",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        user2 = UserEntity(
            id=EntityId.generate(),
            display_name="User Two",
            email=Email("two@test.com"),
            password_hash="hash2",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await repository.save(user1)
        await repository.save(user2)
        await db_session.commit()

        # Act
        users = await repository.find_all()

        # Assert
        assert len(users) >= 2
        emails = {u.email.value for u in users}
        assert "one@test.com" in emails
        assert "two@test.com" in emails

    async def test_case_insensitive_email_search(self, db_session: AsyncSession):
        """Test email search is case-insensitive."""
        # Arrange
        repository = UserRepositoryImpl(db_session)
        user = UserEntity(
            id=EntityId.generate(),
            display_name="Case Test",
            email=Email("CaseSensitive@Test.COM"),
            password_hash="hash",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        await repository.save(user)
        await db_session.commit()

        # Act - Try different cases
        found_lower = await repository.find_by_email("casesensitive@test.com")
        found_upper = await repository.find_by_email("CASESENSITIVE@TEST.COM")
        found_mixed = await repository.find_by_email("CaseSensitive@Test.COM")

        # Assert - All should find the same user
        assert found_lower is not None
        assert found_upper is not None
        assert found_mixed is not None
        assert found_lower.id.value == user.id.value
        assert found_upper.id.value == user.id.value
        assert found_mixed.id.value == user.id.value
