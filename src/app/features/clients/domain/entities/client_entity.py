"""Client domain entity."""
from datetime import datetime
from typing import Optional

from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.features.clients.domain.value_objects.email import Email
from src.app.features.clients.domain.value_objects.phone_number import PhoneNumber
from src.app.features.clients.domain.validators.client_validators import ClientValidators


class ClientEntity(BaseEntity):
    """Domain entity representing a client/company."""
    
    def __init__(
        self,
        id: EntityId,
        name: str,
        email: Optional[Email] = None,
        phone: Optional[PhoneNumber] = None,
        company: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        # Initialize base entity (id, created_at, updated_at)
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        
        # Client-specific fields
        self._name = name
        self._email = email
        self._phone = phone
        self._company = company
        self._address = address
        self._notes = notes
        
        self._validate()
    
    def _validate(self):
        """Validate client invariants using centralized validators."""
        ClientValidators.validate_name(self._name)
        
        if self._company:
            ClientValidators.validate_company(self._company)
    
    @property
    def name(self) -> str:
        """Get client name."""
        return self._name
    
    @property
    def email(self) -> Optional[Email]:
        """Get client email."""
        return self._email
    
    @property
    def phone(self) -> Optional[PhoneNumber]:
        """Get client phone number."""
        return self._phone
    
    @property
    def company(self) -> Optional[str]:
        """Get client company name."""
        return self._company
    
    @property
    def address(self) -> Optional[str]:
        """Get client address."""
        return self._address
    
    @property
    def notes(self) -> Optional[str]:
        """Get client notes."""
        return self._notes
    
    def update_details(
        self,
        name: Optional[str] = None,
        email: Optional[Email] = None,
        phone: Optional[PhoneNumber] = None,
        company: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
    ):
        """Update client details."""
        if name is not None:
            self._name = name
        if email is not None:
            self._email = email
        if phone is not None:
            self._phone = phone
        if company is not None:
            self._company = company
        if address is not None:
            self._address = address
        if notes is not None:
            self._notes = notes
        
        self.mark_as_updated()
        self._validate()
    
    @classmethod
    def create(
        cls,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> "ClientEntity":
        """Factory method to create a new client."""
        client_id = EntityId.generate()
        
        email_vo = Email(email) if email else None
        phone_vo = PhoneNumber(phone) if phone else None
        
        return cls(
            id=client_id,
            name=name,
            email=email_vo,
            phone=phone_vo,
            company=company,
            address=address,
            notes=notes,
        )
    
    def __repr__(self) -> str:
        return f"ClientEntity(id={self.id}, name={self.name}, company={self.company})"
