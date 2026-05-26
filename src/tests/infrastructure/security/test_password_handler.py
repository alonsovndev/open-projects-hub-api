import pytest

from src.app.shared.infrastructure.security.password_handler import PasswordHandler


class TestPasswordHandler:
    @pytest.mark.asyncio
    async def test_hash_password_returns_non_empty_hash(self):
        """Test that hashing returns a non-empty string."""
        password = "MyPassword123"

        hashed = await PasswordHandler.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    @pytest.mark.asyncio
    async def test_hash_password_returns_different_hash_each_time(self):
        """Test that same password produces different hashes due to salt."""
        password = "MyPassword123"

        hash1 = await PasswordHandler.hash_password(password)
        hash2 = await PasswordHandler.hash_password(password)

        assert hash1 != hash2

    @pytest.mark.asyncio
    async def test_verify_password_returns_true_for_correct_password(self):
        """Test password verification with correct password."""
        password = "MyPassword123"
        hashed = await PasswordHandler.hash_password(password)

        result = await PasswordHandler.verify_password(password, hashed)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_password_returns_false_for_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "MyPassword123"
        wrong_password = "WrongPassword"
        hashed = await PasswordHandler.hash_password(password)

        result = await PasswordHandler.verify_password(wrong_password, hashed)
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_password_handles_invalid_hash_gracefully(self):
        """Test that invalid hash returns False without raising."""
        result = await PasswordHandler.verify_password("password", "invalid_hash")
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_password_is_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "MyPassword123"
        hashed = await PasswordHandler.hash_password(password)

        result = await PasswordHandler.verify_password("mypassword123", hashed)
        assert result is False
