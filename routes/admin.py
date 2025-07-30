from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from dependencies import require_permission, get_db
from schemas import ProductCreate
from crud import create_product, get_products, update_product, delete_product, get_product_by_id
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from models import RoleEnum, User


router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/data")
def view_data(user=Depends(require_permission("read"))):
    return {"data": "Admin reading data"}

@router.post("/data")
def create_data(user=Depends(require_permission("write"))):
    return {"msg": "Admin writing data"}

@router.get("/dashboard")
def admin_dashboard(request: Request, user=Depends(require_permission("read"))):
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user
    })


@router.get("/products", response_class=HTMLResponse)
def view_products(request: Request, db: Session = Depends(get_db), user=Depends(require_permission("read"))):
    if user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only admins can view their own products")

    products = db.query(User).filter_by(id=user.id).first().products
    return templates.TemplateResponse("admin_products.html", {
        "request": request,
        "products": products,
        "user": user
    })

@router.post("/products/add")
def add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_permission("write"))
):
    product_data = ProductCreate(name=name, description=description, price=price, category=category)
    create_product(db, product_data, user.id)
    return RedirectResponse("/admin/products", status_code=303)



@router.post("/products/delete/{product_id}")
def delete_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission("edit"))
):
    product = get_product_by_id(db, product_id)
    if product.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own products")

    delete_product(db, product_id)
    return RedirectResponse("/admin/products", status_code=303)



@router.get("/products/edit/{product_id}", response_class=HTMLResponse)
def edit_product_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission("edit"))
):
    product = get_product_by_id(db, product_id)
    if product.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own products")

    return templates.TemplateResponse("edit_product.html", {"request": request, "product": product})

@router.post("/products/edit/{product_id}")
def update_product_route(
    request: Request,
    product_id: int,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_permission("edit"))
):
    product = get_product_by_id(db, product_id)
    if product.created_by != user.id:
        raise HTTPException(status_code=403, detail="You can only update your own products")

    updated = ProductCreate(name=name, description=description, price=price, category=category)
    update_product(db, product_id, updated)
    return RedirectResponse("/admin/products", status_code=303)
