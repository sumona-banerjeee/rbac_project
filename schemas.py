from pydantic import BaseModel
from typing import Optional, List
from models import RoleEnum, ProductCategory



class UserCreate(BaseModel):
    name: str
    email: str
    role: RoleEnum


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: RoleEnum

    class Config:
        from_attributes = True


class PermissionAssign(BaseModel):
    permissions: List[str]



class ProductBase(BaseModel):
    name: str
    description: Optional[str] = ""
    price: float
    category: ProductCategory


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int
    is_sold: bool

    class Config:
        orm_mode = True
