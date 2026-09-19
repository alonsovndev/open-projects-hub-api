"""Unit tests for ClientEntity."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.domain.value_objects.phone_number import PhoneNumber


class TestClientEntityCreation:
    """Test client entity creation."""

    def test_create_client_with_required_fields(self):
        """Test creating client with only required fields."""
        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            client = ClientEntity.create(name="Test Client")

        assert client.name == "Test Client"
        assert client.email is None
        assert client.phone is None
        assert client.company is None
        assert client.address is None
        assert client.notes is None
        assert client.created_at == mock_now
        assert client.updated_at == mock_now
        assert isinstance(client.id, EntityId)

    def test_create_client_with_all_fields(self):
        """Test creating client with all fields."""
        client = ClientEntity.create(
            name="Full Client",
            email="test@example.com",
            phone="+1234567890",
            company="Test Company",
            address="123 Test St",
            notes="Important client",
        )

        assert client.name == "Full Client"
        assert client.email is not None
        assert client.email.value == "test@example.com"
        assert client.phone is not None
        assert client.phone.value == "+1234567890"
        assert client.company == "Test Company"
        assert client.address == "123 Test St"
        assert client.notes == "Important client"

    def test_create_client_with_email_value_object(self):
        """Test that email is converted to Email value object."""
        client = ClientEntity.create(name="Test Client", email="user@domain.com")

        assert isinstance(client.email, Email)
        assert client.email.value == "user@domain.com"

    def test_create_client_with_phone_value_object(self):
        """Test that phone is converted to PhoneNumber value object."""
        client = ClientEntity.create(name="Test Client", phone="+9876543210")

        assert isinstance(client.phone, PhoneNumber)
        assert client.phone.value == "+9876543210"

    def test_create_client_empty_name_raises_error(self):
        """Test creating client with empty name raises ValueError."""
        with pytest.raises(ValueError, match="Client name cannot be empty"):
            ClientEntity.create(name="")

    def test_create_client_whitespace_name_raises_error(self):
        """Test creating client with whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Client name cannot be empty"):
            ClientEntity.create(name="   ")

    def test_create_client_name_too_long_raises_error(self):
        """Test creating client with name > 200 chars raises ValueError."""
        long_name = "a" * 201

        with pytest.raises(ValueError, match="Client name cannot exceed 200 characters"):
            ClientEntity.create(name=long_name)

    def test_create_client_company_too_long_raises_error(self):
        """Test creating client with company > 200 chars raises ValueError."""
        long_company = "a" * 201

        with pytest.raises(ValueError, match="Company name cannot exceed 200 characters"):
            ClientEntity.create(name="Test Client", company=long_company)

    def test_create_client_invalid_email_raises_error(self):
        """Test creating client with invalid email raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email format"):
            ClientEntity.create(name="Test Client", email="not-an-email")

    def test_create_client_invalid_phone_raises_error(self):
        """Test creating client with invalid phone raises ValueError."""
        with pytest.raises(ValueError, match="Invalid phone number format"):
            ClientEntity.create(name="Test Client", phone="abc")


class TestClientEntityUpdate:
    """Test client entity update operations."""

    def test_update_client_name(self):
        """Test updating client name."""
        client = ClientEntity.create(name="Old Name")

        with patch("src.app.shared.domain.entities.base_entity.datetime") as mock_datetime:
            mock_now = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
            mock_datetime.now.return_value = mock_now

            client.update_details(name="New Name")

        assert client.name == "New Name"
        assert client.updated_at == mock_now

    def test_update_client_email(self):
        """Test updating client email."""
        client = ClientEntity.create(name="Test Client")

        new_email = Email("new@example.com")
        client.update_details(email=new_email)

        assert client.email == new_email
        assert client.email.value == "new@example.com"

    def test_update_client_phone(self):
        """Test updating client phone."""
        client = ClientEntity.create(name="Test Client")

        new_phone = PhoneNumber("+1111111111")
        client.update_details(phone=new_phone)

        assert client.phone == new_phone
        assert client.phone.value == "+1111111111"

    def test_update_client_company(self):
        """Test updating client company."""
        client = ClientEntity.create(name="Test Client")

        client.update_details(company="New Company")

        assert client.company == "New Company"

    def test_update_client_address(self):
        """Test updating client address."""
        client = ClientEntity.create(name="Test Client")

        client.update_details(address="New Address")

        assert client.address == "New Address"

    def test_update_client_notes(self):
        """Test updating client notes."""
        client = ClientEntity.create(name="Test Client")

        client.update_details(notes="New notes")

        assert client.notes == "New notes"

    def test_update_client_all_fields(self):
        """Test updating all client fields at once."""
        client = ClientEntity.create(name="Old Name")

        new_email = Email("updated@example.com")
        new_phone = PhoneNumber("+2222222222")

        client.update_details(
            name="Updated Name",
            email=new_email,
            phone=new_phone,
            company="Updated Company",
            address="Updated Address",
            notes="Updated notes",
        )

        assert client.name == "Updated Name"
        assert client.email == new_email
        assert client.phone == new_phone
        assert client.company == "Updated Company"
        assert client.address == "Updated Address"
        assert client.notes == "Updated notes"

    def test_update_client_empty_name_raises_error(self):
        """Test updating with empty name raises ValueError."""
        client = ClientEntity.create(name="Test Client")

        with pytest.raises(ValueError, match="Client name cannot be empty"):
            client.update_details(name="")

    def test_update_client_name_too_long_raises_error(self):
        """Test updating with name > 200 chars raises ValueError."""
        client = ClientEntity.create(name="Test Client")
        long_name = "a" * 201

        with pytest.raises(ValueError, match="Client name cannot exceed 200 characters"):
            client.update_details(name=long_name)

    def test_update_client_company_too_long_raises_error(self):
        """Test updating with company > 200 chars raises ValueError."""
        client = ClientEntity.create(name="Test Client")
        long_company = "a" * 201

        with pytest.raises(ValueError, match="Company name cannot exceed 200 characters"):
            client.update_details(company=long_company)

    def test_update_client_partial_update_preserves_other_fields(self):
        """Test that partial update preserves unchanged fields."""
        client = ClientEntity.create(
            name="Test Client",
            email="test@example.com",
            company="Test Company",
        )

        client.update_details(name="Updated Name")

        assert client.name == "Updated Name"
        assert client.email is not None
        assert client.email.value == "test@example.com"
        assert client.company == "Test Company"


class TestClientEntityProperties:
    """Test client entity property access."""

    def test_all_properties_accessible(self):
        """Test all properties are accessible."""
        client_id = EntityId.generate()
        email = Email("test@example.com")
        phone = PhoneNumber("+1234567890")
        now = datetime.now()

        client = ClientEntity(
            id=client_id,
            name="Test Client",
            email=email,
            phone=phone,
            company="Test Company",
            address="123 Test St",
            notes="Test notes",
            created_at=now,
            updated_at=now,
        )

        assert client.id == client_id
        assert client.name == "Test Client"
        assert client.email == email
        assert client.phone == phone
        assert client.company == "Test Company"
        assert client.address == "123 Test St"
        assert client.notes == "Test notes"
        assert client.created_at == now
        assert client.updated_at == now

    def test_repr(self):
        """Test string representation."""
        client = ClientEntity.create(name="Test Client", company="Test Company")

        repr_str = repr(client)

        assert "ClientEntity" in repr_str
        assert "Test Client" in repr_str
        assert "Test Company" in repr_str
