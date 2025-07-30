from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey,
    Table, Boolean, Float, DateTime
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum
from sqlalchemy import Enum as SqlEnum


# --- Enums ---

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

class PaymentMethod(str, enum.Enum):
    cash = "cash"
    upi = "upi"
    card = "card"


# --- Association Table ---

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("permission_name", String, ForeignKey("permissions.name"))
)


# --- Models ---

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
    purchases = relationship("Purchase", back_populates="buyer")  # 👈 user as buyer


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    category = Column(SqlEnum(ProductCategory), default=ProductCategory.other)

    payment_method = Column(SqlEnum(PaymentMethod), default=PaymentMethod.cash)
    payment_status = Column(String, default="pending")  # pending, verified

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_sold = Column(Boolean, default=False)

    owner = relationship("User", back_populates="products")
    purchases = relationship("Purchase", back_populates="product")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="purchases")
    buyer = relationship("User", back_populates="purchases")
