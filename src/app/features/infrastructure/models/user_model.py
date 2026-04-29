from sqlalchemy import Column, String, Enum as SQLEnum

from src.app.features.domain.value_objects.user_role import UserRole
from src.app.shared.infrastructure.models.base_model import BaseModel


class UserModel(BaseModel):
    """
    SQLAlchemy model for the 'users' table.
    Inherits common fields from BaseModel.
    """

    __tablename__ = 'users'

    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    country_code = Column(String(10), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)