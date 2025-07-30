from sqlalchemy.orm import Session
from models import User, RoleEnum, Permission, PermissionEnum, Product
from schemas import ProductCreate
from datetime import datetime



def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, name: str, email: str, role: RoleEnum):
    user = User(name=name, email=email, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def assign_role(db: Session, user_id: int, role: RoleEnum):
    user = db.query(User).get(user_id)
    if user:
        user.role = role
        db.commit()
        return user


def assign_permissions(db: Session, user_id: int, permissions: list[str]):
    user = db.query(User).get(user_id)
    if user:
        perms = db.query(Permission).filter(Permission.name.in_(permissions)).all()
        user.permissions = perms
        db.commit()
        return user



def create_product(db: Session, product: ProductCreate, user_id: int):
    db_product = Product(**product.dict(), created_by=user_id)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_products(db: Session):
    return db.query(Product).all()


def get_product_by_id(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()


def update_product(db: Session, product_id: int, updated_data: ProductCreate):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        for key, value in updated_data.dict().items():
            setattr(product, key, value)
        product.updated_at = datetime.utcnow()
        db.commit()
    return product


def delete_product(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        db.delete(product)
        db.commit()
        return True
    return False
