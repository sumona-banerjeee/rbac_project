from sqlalchemy import (
    Column, Integer, String, Enum, ForeignKey, Table, Boolean, Float, DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from sqlalchemy import Enum as SqlEnum
from database import Base

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
    Column("permission_name", SqlEnum(PermissionEnum), ForeignKey("permissions.name"))
)

# --- Models ---
class Permission(Base):
    __tablename__ = "permissions"
    name = Column(SqlEnum(PermissionEnum), primary_key=True)
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

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator = relationship("User", remote_side=[id], backref="created_users")

    permissions = relationship("Permission", secondary=user_permissions, back_populates="users")

    products = relationship("Product", back_populates="owner")
    purchases = relationship("Purchase", back_populates="buyer")
    resource_permissions = relationship("ResourcePermission", back_populates="user")

    def has_permission(self, db, resource_name: str, action: str) -> bool:
        resource = db.query(Resource).filter_by(name=resource_name).first()
        if not resource:
            return False
        rp = db.query(ResourcePermission).filter_by(user_id=self.id, resource_id=resource.id).first()
        if not rp:
            return False
        return {
            "create": rp.can_create,
            "read": rp.can_read,
            "update": rp.can_update,
            "delete": rp.can_delete,
        }.get(action, False)

    def get_resource_permissions(self, db, resource_name):
        resource = db.query(Resource).filter_by(name=resource_name).first()
        if not resource:
            return []
        rp = db.query(ResourcePermission).filter_by(
            user_id=self.id, resource_id=resource.id
        ).first()
        if not rp:
            return []
        perms = []
        if rp.can_create: perms.append("create")
        if rp.can_read: perms.append("read")
        if rp.can_update: perms.append("update")
        if rp.can_delete: perms.append("delete")
        return perms


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

    owner = relationship("User", back_populates="products", foreign_keys=[created_by])
    purchases = relationship("Purchase", back_populates="product")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    buyer_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="purchases")
    buyer = relationship("User", back_populates="purchases")


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)


class ResourcePermission(Base):
    __tablename__ = "resource_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resource_id = Column(Integer, ForeignKey("resources.id"))

    can_create = Column(Boolean, default=False)
    can_read = Column(Boolean, default=False)
    can_update = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)

    user = relationship("User", back_populates="resource_permissions")
    resource = relationship("Resource")


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
