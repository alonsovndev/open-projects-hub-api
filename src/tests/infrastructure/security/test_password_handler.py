from src.app.shared.infrastructure.security.password_handler import PasswordHandler


class TestPasswordHandler:

    def test_hash_password_returns_non_empty_hash(self):
        """Test that hashing returns a non-empty string."""
        password = "MyPassword123"

        hashed = PasswordHandler.hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_returns_different_hash_each_time(self):
        """Test that same password produces different hashes due to salt."""
        password = "MyPassword123"

        hash1 = PasswordHandler.hash_password(password)
        hash2 = PasswordHandler.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_returns_true_for_correct_password(self):
        """Test password verification with correct password."""
        password = "MyPassword123"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "MyPassword123"
        wrong_password = "WrongPassword"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(wrong_password, hashed) is False

    def test_verify_password_handles_invalid_hash_gracefully(self):
        """Test that invalid hash returns False without raising."""
        assert PasswordHandler.verify_password("password", "invalid_hash") is False

    def test_verify_password_is_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "MyPassword123"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password("mypassword123", hashed) is False
