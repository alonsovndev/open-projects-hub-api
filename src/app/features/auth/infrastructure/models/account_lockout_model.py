from sqlalchemy import Column, DateTime, Integer, String

from src.app.shared.persistence import Base


class AccountLockoutModel(Base):
    """
    SQLAlchemy model for the 'account_lockouts' table.

    Keyed by the lowercased email under attempt, not user_id, so lockout
    tracking (and its brute-force protection) works even for emails that
    don't correspond to a real account, without disclosing which is which.
    """

    __tablename__ = "account_lockouts"

    # 1. Primary key
    email = Column(String(255), primary_key=True)

    # 2. Data columns
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=False)
