from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_current_user
from models import Product, User, Purchase, Resource, ResourcePermission, RoleEnum 
from database import get_db
import os
import bcrypt 
from utils.email_utils import send_email
from models import Announcement
from sqlalchemy import func 
from database import engine


router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")



@router.get("/dashboard", response_class=HTMLResponse)
def admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resource_data = []
    all_resources = db.query(Resource).all()

    for resource in all_resources:
        rp = db.query(ResourcePermission).filter_by(
            user_id=current_user.id, resource_id=resource.id
        ).first()

        if rp:
            permissions = []
            if rp.can_create: permissions.append("create")
            if rp.can_read: permissions.append("read")
            if rp.can_update: permissions.append("update")
            if rp.can_delete: permissions.append("delete")

            if permissions:
                resource_data.append({
                    "name": resource.name,
                    "permissions": permissions
                })

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "resources": resource_data
    })


@router.get("/resource/{resource_name}", response_class=HTMLResponse)
def access_resource(
    resource_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, resource_name, "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    file_path = f"resource_pages/{resource_name}.html"
    if not os.path.exists(f"templates/{file_path}"):
        raise HTTPException(status_code=404, detail="Page Not Found")

    resource_obj = db.query(Resource).filter_by(name=resource_name).first()
    rp = db.query(ResourcePermission).filter_by(
        user_id=current_user.id, resource_id=resource_obj.id
    ).first()

    permissions = []
    if rp:
        if rp.can_create: permissions.append("create")
        if rp.can_read: permissions.append("read")
        if rp.can_update: permissions.append("update")
        if rp.can_delete: permissions.append("delete")

    return templates.TemplateResponse(file_path, {
        "request": request,
        "resource_name": resource_name,
        "permissions": permissions
    })


@router.post("/resource/{resource_name}/update/{item_id}")
async def update_resource_item(
    resource_name: str,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, resource_name, "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()

    model_map = {
        "products": Product,
        "users": User,
    }

    model = model_map.get(resource_name)
    if not model:
        raise HTTPException(status_code=404, detail="Unknown resource")

    item = db.query(model).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for key, value in form.items():
        if hasattr(item, key):
            setattr(item, key, value)
            

    db.commit()
    return RedirectResponse(f"/admin/resource/{resource_name}", status_code=303)


@router.post("/products/add")
async def add_product(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "products", "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    name = form["name"]
    description = form["description"]
    price = float(form["price"])
    category = form["category"]

    new_product = Product(
        name=name,
        description=description,
        price=price,
        category=category,
        created_by=current_user.id
    )
    db.add(new_product)
    db.commit()
    return RedirectResponse("/admin/resource/products", status_code=303)


@router.post("/products/delete/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "products", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return RedirectResponse("/admin/resource/products", status_code=303)


@router.get("/users", response_class=HTMLResponse)
def view_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "users", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    users = db.query(User).filter(
    User.role != "superadmin",
    User.is_approved == True,
    User.is_active == True
    ).all()

    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "users": users
    })




@router.post("/users/delete/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "users", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)


@router.get("/orders", response_class=HTMLResponse)
def view_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "orders", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    orders = db.query(Purchase).all()
    return templates.TemplateResponse("admin_orders.html", {
        "request": request,
        "orders": orders
    })



model_map = {
    "users_management": (User, "resource_pages/users_management.html"),
    "product_listings": (Product, "resource_pages/product_listings.html"),
    "reports_analytics": (None, "resource_pages/reports_analytics.html"),
    "payments_verification": (None, "resource_pages/payments_verification.html"),
    "announcements": (Announcement, "resource_pages/announcements.html"),
    "dashboard": (None, "resource_pages/dashboard.html")
}


@router.get("/resource/{resource_name}", response_class=HTMLResponse)
def view_resource_list(
    resource_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if resource_name not in model_map:
        raise HTTPException(status_code=404, detail="Resource not found")

    model, template_name = model_map[resource_name]

    if not current_user.has_permission(db, resource_name, "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    items = db.query(model).all()
    permissions = current_user.get_resource_permissions(db, resource_name)

    return templates.TemplateResponse(template_name, {
        "request": request,
        "items": items,
        "permissions": permissions
    })





@router.post("/resource/{resource_name}/create")
async def create_resource_item(
    resource_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if resource_name not in model_map:
        raise HTTPException(status_code=404, detail="Resource not found")

    model, _ = model_map[resource_name]

    if not current_user.has_permission(db, resource_name, "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    new_item = model(**form)  # Fill columns dynamically
    db.add(new_item)
    db.commit()

    return RedirectResponse(f"/admin/resource/{resource_name}", status_code=303)



@router.post("/resource/{resource_name}/update/{item_id}")
async def update_resource_item(
    resource_name: str,
    item_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if resource_name not in model_map:
        raise HTTPException(status_code=404, detail="Resource not found")

    model, _ = model_map[resource_name]

    if not current_user.has_permission(db, resource_name, "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    item = db.query(model).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    form = await request.form()
    for key, value in form.items():
        if hasattr(item, key):
            setattr(item, key, value)

    db.commit()
    return RedirectResponse(f"/admin/resource/{resource_name}", status_code=303)



@router.post("/resource/{resource_name}/delete/{item_id}")
def delete_resource_item(
    resource_name: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if resource_name not in model_map:
        raise HTTPException(status_code=404, detail="Resource not found")

    model, _ = model_map[resource_name]

    if not current_user.has_permission(db, resource_name, "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    item = db.query(model).filter_by(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()
    return RedirectResponse(f"/admin/resource/{resource_name}", status_code=303)
