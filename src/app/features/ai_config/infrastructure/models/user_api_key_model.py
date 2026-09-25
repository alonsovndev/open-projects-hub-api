import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM as pg_enum, UUID  # noqa: N811

from src.app.shared.persistence import Base


class UserApiKeyModel(Base):
    """
    SQLAlchemy model for the 'user_api_keys' table.

    Holds only ciphertext: there is no plaintext column and no plaintext read path
    (F-010 NFR-010-01/NFR-010-02). `masked_key` is the sole display form.
    """

    __tablename__ = "user_api_keys"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(
        pg_enum("gemini", "openai", "deepseek", name="aiprovider", create_type=False),
        nullable=False,
    )
    encrypted_key = Column(LargeBinary, nullable=False)
    encryption_nonce = Column(LargeBinary, nullable=False)
    # Which master key produced `encrypted_key`, so a rotation can find rows to re-encrypt.
    key_version = Column(Integer, nullable=False, server_default="1", default=1)
    masked_key = Column(String(64), nullable=False)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)

    # One active key per provider per user (FR-010-04): a replacement overwrites this row
    # rather than adding a second, which is what makes a rotated key unusable at once.
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_api_keys_user_provider"),)

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )


class ApiKeyValidationAttemptModel(Base):
    """
    SQLAlchemy model for the 'api_key_validation_attempts' table.

    One row per user, holding the fixed-window counter behind NFR-010-03's 5-per-hour
    validation budget. SQL-backed so the budget holds across restarts and instances.
    """

    __tablename__ = "api_key_validation_attempts"

    # 1. Primary key — the user, since the budget is per user and there is one window each
    id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # 2. Data columns
    attempt_count = Column(Integer, nullable=False, server_default="0", default=0)
    window_started_at = Column(DateTime(timezone=True), nullable=False)

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
