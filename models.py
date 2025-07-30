from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    Table, Boolean, Float, DateTime
)
from sqlalchemy.orm import relationship
from database import Base
import enum
from sqlalchemy import Enum as SqlEnum  # For general use
from datetime import datetime



class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    user = "user"


class PermissionEnum(str, enum.Enum):
    read = "read"
    write = "write"
    edit = "edit"
    assign_roles = "assign_roles"


class ProductCategory(str, enum.Enum):
    electronics = "electronics"
    fashion = "fashion"
    books = "books"
    other = "other"


user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("permission_name", String, ForeignKey("permissions.name"))
)


class Permission(Base):
    __tablename__ = "permissions"

    name = Column(String, primary_key=True)
    users = relationship("User", secondary=user_permissions, back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(SqlEnum(RoleEnum), default=RoleEnum.user)
    is_approved = Column(Boolean, default=False)
    is_denied = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    
    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")

    
    products = relationship("Product", back_populates="owner")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = Column(SqlEnum(ProductCategory), default=ProductCategory.other)

    created_by = Column(Integer, ForeignKey("users.id"))  # Link to creator
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_sold = Column(Boolean, default=False)

    
    owner = relationship("User", back_populates="products")
