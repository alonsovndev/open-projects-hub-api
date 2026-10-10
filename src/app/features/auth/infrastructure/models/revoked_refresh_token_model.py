from sqlalchemy import Column, DateTime, String

from src.app.shared.persistence import Base


class RevokedRefreshTokenModel(Base):
    """
    SQLAlchemy model for the 'revoked_refresh_tokens' table.

    Records a single-use refresh token as spent once it's been rotated or a
    session logged out, so a replay is rejected. Keyed by a SHA-256 hash of
    the token — raw bearer tokens are never stored at rest.
    """

    __tablename__ = "revoked_refresh_tokens"

    # 1. Primary key
    token_hash = Column(String(64), primary_key=True)

    # 2. Data columns
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
