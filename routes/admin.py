from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from dependencies import get_current_user
from models import Product, User, Purchase, Resource, ResourcePermission, RoleEnum 
from database import get_db
import os
import bcrypt
from models import Product 
from fastapi import Form


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



@router.get("/resource/users_management", response_class=HTMLResponse)
def view_users_management(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "users_management", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    if current_user.role == RoleEnum.superadmin:
        users = db.query(User).filter(User.role != RoleEnum.superadmin).all()
    else:
        users = db.query(User).filter(
            User.created_by != None,
            User.created_by != 1,
            User.id != current_user.id
        ).all()

    permissions = current_user.get_resource_permissions(db, "users_management")
    return templates.TemplateResponse("users_management.html", {
        "request": request,
        "users": users,
        "permissions": permissions
    })

# ✅ Create user
@router.post("/resource/users_management/create")
async def create_user_by_admin(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user.has_permission(db, "users_management", "create"):
        raise HTTPException(status_code=403, detail="Permission denied.")

    form = await request.form()
    name = form["name"]
    email = form["email"]
    password = form["password"]
    role = form["role"]

    if db.query(User).filter_by(email=email).first():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    new_user = User(
        name=name,
        email=email,
        password=hashed_pw,
        role=RoleEnum(role),
        is_approved=True,
        is_active=True,
        created_by=current_user.id  # ✅ track creator
    )

    db.add(new_user)
    db.commit()
    return RedirectResponse("/admin/resource/users_management", status_code=303)

# ✅ Update user role
@router.post("/resource/users_management/update/{user_id}")
def update_user_role(
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user.has_permission(db, "users_management", "update"):
        raise HTTPException(status_code=403, detail="Permission denied.")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = RoleEnum(role)
    db.commit()
    return RedirectResponse("/admin/resource/users_management", status_code=303)

# ✅ Delete user
@router.post("/resource/users_management/delete/{user_id}")
def delete_user_by_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not current_user.has_permission(db, "users_management", "delete"):
        raise HTTPException(status_code=403, detail="Permission denied.")

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return RedirectResponse("/admin/resource/users_management", status_code=303)





@router.get("/resource/product_listings", response_class=HTMLResponse)
def view_product_listings(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "product_listings", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    products = db.query(Product).all()

    return templates.TemplateResponse("resource_pages/product_listings.html", {
        "request": request,
        "products": products,
        "permissions": current_user.get_resource_permissions(db, "product_listings")
    })




@router.post("/resource/product_listings/create")
async def create_product_listing(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "product_listings", "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    new_product = Product(
        name=form["name"],
        description=form["description"],
        price=float(form["price"]),
        category=form["category"],
        created_by=current_user.id
    )
    db.add(new_product)
    db.commit()
    return RedirectResponse("/admin/resource/product_listings", status_code=303)



@router.post("/resource/product_listings/update/{product_id}")
async def update_product_listing(
    product_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "product_listings", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name
    db.commit()
    return RedirectResponse("/admin/resource/product_listings", status_code=303)




@router.post("/resource/product_listings/delete/{product_id}")
def delete_product_listing(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "product_listings", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return RedirectResponse("/admin/resource/product_listings", status_code=303)






@router.get("/resource/products", response_class=HTMLResponse)
def view_products(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "products", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    products = db.query(Product).all()
    return templates.TemplateResponse("resource_pages/products.html", {
        "request": request,
        "products": products,
        "permissions": current_user.get_resource_permissions(db, "products")
    })


@router.post("/resource/products/create")
async def create_product(
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


@router.post("/resource/products/update/{product_id}")
async def update_product(
    product_id: int,
    name: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "products", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = name  # You can extend this to update more fields
    db.commit()
    return RedirectResponse("/admin/resource/products", status_code=303)


@router.post("/resource/products/delete/{product_id}")
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



@router.get("/resource/orders", response_class=HTMLResponse)
def view_orders(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "orders", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    orders = db.query(Purchase).all()
    return templates.TemplateResponse("resource_pages/orders.html", {
        "request": request,
        "orders": orders,
        "permissions": current_user.get_resource_permissions(db, "orders")
    })


@router.post("/resource/orders/create")
async def create_order(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "orders", "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    product_id = int(form["product_id"])
    quantity = int(form["quantity"])

    new_order = Purchase(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity
    )
    db.add(new_order)
    db.commit()
    return RedirectResponse("/admin/resource/orders", status_code=303)


@router.post("/resource/orders/update/{order_id}")
async def update_order(
    order_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "orders", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    order = db.query(Purchase).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.quantity = quantity
    db.commit()
    return RedirectResponse("/admin/resource/orders", status_code=303)


@router.post("/resource/orders/delete/{order_id}")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "orders", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    order = db.query(Purchase).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return RedirectResponse("/admin/resource/orders", status_code=303)





@router.get("/resource/order_management", response_class=HTMLResponse)
def view_order_management(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "order_management", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    orders = db.query(Purchase).all()
    return templates.TemplateResponse("resource_pages/order_management.html", {
        "request": request,
        "orders": orders,
        "permissions": current_user.get_resource_permissions(db, "order_management")
    })


@router.post("/resource/order_management/create")
async def create_order_management(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "order_management", "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    product_id = int(form["product_id"])
    quantity = int(form["quantity"])

    new_order = Purchase(
        user_id=current_user.id,
        product_id=product_id,
        quantity=quantity
    )
    db.add(new_order)
    db.commit()
    return RedirectResponse("/admin/resource/order_management", status_code=303)


@router.post("/resource/order_management/update/{order_id}")
async def update_order_management(
    order_id: int,
    quantity: int = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "order_management", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    order = db.query(Purchase).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.quantity = quantity
    db.commit()
    return RedirectResponse("/admin/resource/order_management", status_code=303)


@router.post("/resource/order_management/delete/{order_id}")
def delete_order_management(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "order_management", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    order = db.query(Purchase).filter_by(id=order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    db.delete(order)
    db.commit()
    return RedirectResponse("/admin/resource/order_management", status_code=303)





@router.get("/resource/dashboard", response_class=HTMLResponse)
def view_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "dashboard", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    
    total_users = db.query(User).count()
    total_products = db.query(Product).count()

   
    total_sales = db.query(Purchase).join(Product).with_entities(
        func.sum(Product.price)
    ).scalar() or 0.0

    
    from sqlalchemy import func
    sales_by_date = (
        db.query(func.date(Purchase.created_at), func.sum(Product.price))
        .join(Product, Product.id == Purchase.product_id)
        .group_by(func.date(Purchase.created_at))
        .all()
    )

    sales_dates = [str(date) for date, _ in sales_by_date]
    sales_values = [float(value) for _, value in sales_by_date]

    return templates.TemplateResponse("resource_pages/dashboard.html", {
        "request": request,
        "permissions": current_user.get_resource_permissions(db, "dashboard"),
        "stats": {
            "total_users": total_users,
            "total_products": total_products,
            "total_sales": total_sales,
            "sales_dates": sales_dates,
            "sales_values": sales_values
        }
    })




@router.get("/resource/payments_verification", response_class=HTMLResponse)
def view_payments_verification(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "payments_verification", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    payments = db.query(Product).filter(Product.payment_method != None).all()

    return templates.TemplateResponse("resource_pages/payments_verification.html", {
        "request": request,
        "payments": payments,
        "permissions": current_user.get_resource_permissions(db, "payments_verification")
    })


@router.post("/resource/payments_verification/update/{product_id}")
async def update_payment_status(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "payments_verification", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    new_status = form["payment_status"]

    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.payment_status = new_status
    db.commit()

    return RedirectResponse("/admin/resource/payments_verification", status_code=303)



@router.get("/resource/announcements", response_class=HTMLResponse)
def view_announcements(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "announcements", "read"):
        raise HTTPException(status_code=403, detail="Access Denied")

    from models import Announcement
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()

    return templates.TemplateResponse("resource_pages/announcements.html", {
        "request": request,
        "announcements": announcements,
        "permissions": current_user.get_resource_permissions(db, "announcements")
    })



@router.post("/resource/announcements/create")
async def create_announcement(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "announcements", "create"):
        raise HTTPException(status_code=403, detail="Access Denied")

    form = await request.form()
    title = form["title"]
    content = form["content"]

    from models import Announcement
    new_announcement = Announcement(title=title, content=content)
    db.add(new_announcement)
    db.commit()
    return RedirectResponse("/admin/resource/announcements", status_code=303)


@router.post("/resource/announcements/update/{id}")
async def update_announcement(
    id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "announcements", "update"):
        raise HTTPException(status_code=403, detail="Access Denied")

    from models import Announcement
    form = await request.form()
    announcement = db.query(Announcement).filter_by(id=id).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    announcement.title = form["title"]
    announcement.content = form["content"]
    db.commit()
    return RedirectResponse("/admin/resource/announcements", status_code=303)




@router.post("/resource/announcements/delete/{id}")
def delete_announcement(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.has_permission(db, "announcements", "delete"):
        raise HTTPException(status_code=403, detail="Access Denied")

    from models import Announcement
    announcement = db.query(Announcement).filter_by(id=id).first()

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    db.delete(announcement)
    db.commit()
    return RedirectResponse("/admin/resource/announcements", status_code=303)
