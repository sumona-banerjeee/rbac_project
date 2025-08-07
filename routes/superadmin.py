from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
import os

from models import (
    User, RoleEnum, Permission, Product, Purchase,
    Resource, ResourcePermission, PermissionEnum
)
from dependencies import get_current_user, require_permission, require_superadmin
from database import get_db
from utils.email_utils import send_email

router = APIRouter(prefix="/superadmin")
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("assign_roles"))
):
    pending_users = db.query(User).filter_by(is_approved=False).all()
    permissions = db.query(Permission).all()
    raw_resources = db.query(Resource).all()

    
    seen = set()
    resources = []
    for r in raw_resources:
        if r.name not in seen:
            resources.append(r)
            seen.add(r.name)

    return templates.TemplateResponse("superadmin_dashboard.html", {
        "request": request,
        "users": pending_users,
        "permissions": permissions,
        "roles": list(RoleEnum),
        "resources": resources
    })


@router.post("/approve/{user_id}")
async def approve_user(
    request: Request,
    user_id: int,
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assign_roles"))
):
    
    form_data = await request.form()

    
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    
    user.role = RoleEnum(role)
    user.is_approved = True
    user.is_active = True

    
    global_permissions = form_data.getlist("permissions")
    if global_permissions:
        assigned_perms = db.query(Permission).filter(Permission.name.in_(global_permissions)).all()
        user.permissions = assigned_perms
    else:
        user.permissions = []

    
    db.query(ResourcePermission).filter_by(user_id=user.id).delete()

    
    raw_resources = db.query(Resource).all()
    seen = set()
    unique_resources = []
    for r in raw_resources:
        if r.name not in seen:
            unique_resources.append(r)
            seen.add(r.name)

    for resource in unique_resources:
        can_create = form_data.get(f"resource_{resource.id}_create") == "on"
        can_read   = form_data.get(f"resource_{resource.id}_read") == "on"
        can_update = form_data.get(f"resource_{resource.id}_update") == "on"
        can_delete = form_data.get(f"resource_{resource.id}_delete") == "on"

        
        if can_create or can_read or can_update or can_delete:
            rp = ResourcePermission(
                user_id=user.id,
                resource_id=resource.id,
                can_create=can_create,
                can_read=can_read,
                can_update=can_update,
                can_delete=can_delete
            )
            db.add(rp)

    
    db.commit()

    
    subject = "Your Account Has Been Approved"
    body = f"""
    Hello {user.name},

    Your account has been approved by the Superadmin.
    You can now log in and access your assigned role and resources.

    Regards,
    RBAC System
    """
    send_email(subject, user.email, body)

    return RedirectResponse("/superadmin/dashboard", status_code=303)





@router.post("/deny/{user_id}")
def deny_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission("assign_roles"))
):
    user_to_deny = db.query(User).get(user_id)
    if not user_to_deny:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user_to_deny)
    db.commit()
    return RedirectResponse("/superadmin/dashboard", status_code=303)



@router.get("/manage-users", response_class=HTMLResponse)
def manage_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assign_roles"))
):
    approved_users = db.query(User).filter(
        User.is_approved == True,
        User.is_active == True,
        User.role != RoleEnum.superadmin
    ).all()
    return templates.TemplateResponse("manage_users.html", {
        "request": request,
        "users": approved_users
    })



@router.post("/delete-user/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assign_roles"))
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return RedirectResponse("/superadmin/manage-users", status_code=303)


# 🔹 View pending users
@router.get("/approvals", response_class=HTMLResponse)
def view_pending_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_superadmin)
):
    pending_users = db.query(User).filter(User.is_approved == False).all()
    return templates.TemplateResponse("superadmin_approvals.html", {
        "request": request,
        "users": pending_users
    })



@router.get("/analytics-ui", response_class=HTMLResponse)
def render_analytics_ui(
    request: Request,
    current_user: User = Depends(require_permission("assign_roles"))
):
    return templates.TemplateResponse("analytics_dashboard.html", {"request": request})



@router.get("/analytics-data")
def get_analytics_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("assign_roles"))
):
    top_products = db.query(
        Product.name,
        func.count(Purchase.id).label("purchase_count")
    ).join(Purchase).group_by(Product.id).order_by(func.count(Purchase.id).desc()).limit(5).all()

    sales_trend = db.query(
        func.date(Purchase.created_at),
        func.count(Purchase.id)
    ).group_by(func.date(Purchase.created_at)).all()

    active_buyers = db.query(
        User.name,
        func.count(Purchase.id)
    ).join(Purchase).filter(User.role == RoleEnum.user).group_by(User.id).all()

    active_sellers = db.query(
        User.name,
        func.count(Product.id)
    ).join(Product).filter(User.role == RoleEnum.admin).group_by(User.id).all()

    payment_split = db.query(
        Product.payment_method,
        func.count(Product.id)
    ).group_by(Product.payment_method).all()

    return {
        "top_products": [{"name": name, "count": count} for name, count in top_products],
        "sales_trend": [{"date": str(date), "count": count} for date, count in sales_trend],
        "active_buyers": [{"name": name, "count": count} for name, count in active_buyers],
        "active_sellers": [{"name": name, "count": count} for name, count in active_sellers],
        "payment_split": [{"method": method, "count": count} for method, count in payment_split],
    }



@router.get("/resource/{resource_name}", response_class=HTMLResponse)
def access_resource(
    resource_name: str,
    request: Request,
    current_user: User = Depends(require_permission("read", resource_name=True))
):
    file_path = f"resource_pages/{resource_name}.html"
    full_path = f"templates/{file_path}"

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Page Not Found")

    return templates.TemplateResponse(file_path, {"request": request})