from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

from src.app.shared.persistence.base_model import BaseModel


class UserModel(BaseModel):
    """
    SQLAlchemy model for the 'users' table.
    Inherits common fields from BaseModel.
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(PgEnum("admin", "viewer", name="userrole", create_type=False), nullable=False, default="viewer")
