from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, RoleEnum, Permission, Product, Purchase
from dependencies import get_current_user, require_permission
from database import get_db
from dependencies import require_superadmin
from sqlalchemy import func



router = APIRouter(prefix="/superadmin")
templates = Jinja2Templates(directory="templates")


# 🟢 Render Superadmin Dashboard with Pending Users
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(require_permission("assign_roles"))
):
    pending_users = db.query(User).filter_by(is_approved=False).all()
    permissions = db.query(Permission).all()
    return templates.TemplateResponse("superadmin_dashboard.html", {
        "request": request,
        "users": pending_users,
        "permissions": permissions,
        "roles": list(RoleEnum)
    })


# 🟢 Approve a User and Assign Role + Permissions
@router.post("/approve/{user_id}")
def approve_user(
    user_id: int,
    role: str = Form(...),
    permissions: list[str] = Form(...),
    db: Session = Depends(get_db),
    user=Depends(require_permission("assign_roles"))
):
    target_user = db.query(User).get(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Assign role and permissions
    target_user.role = RoleEnum(role)
    target_user.is_approved = True
    assigned_perms = db.query(Permission).filter(Permission.name.in_(permissions)).all()
    target_user.permissions = assigned_perms

    db.commit()
    return RedirectResponse("/superadmin/dashboard", status_code=303)


@router.post("/deny/{user_id}")
def deny_user(user_id: int, db: Session = Depends(get_db), user=Depends(require_superadmin)):
    user_to_deny = db.query(User).filter_by(id=user_id).first()
    if not user_to_deny:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user_to_deny)  # ❌ Permanently delete
    db.commit()

    return RedirectResponse(url="/superadmin/dashboard", status_code=303)


@router.get("/analytics-data")
def get_analytics_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403, detail="Access denied")

    # 🔹 Top selling products (by count of buyers)
    top_products = db.query(
        Product.name,
        func.count(Purchase.id).label("purchase_count")
    ).join(Purchase).group_by(Product.id).order_by(func.count(Purchase.id).desc()).limit(5).all()

    # 🔹 Sales Trends Over Time
    sales_trend = db.query(
        func.date(Purchase.created_at),
        func.count(Purchase.id)
    ).group_by(func.date(Purchase.created_at)).all()

    # 🔹 Active Buyers
    active_buyers = db.query(
        User.name,
        func.count(Purchase.id)
    ).join(Purchase).filter(User.role == RoleEnum.user).group_by(User.id).all()

    # 🔹 Active Sellers
    active_sellers = db.query(
        User.name,
        func.count(Product.id)
    ).join(Product).filter(User.role == RoleEnum.admin).group_by(User.id).all()

    # 🔹 Payment Split
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



@router.get("/manage-users", response_class=HTMLResponse)
def manage_users(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403)

    approved_users = db.query(User).filter(User.is_approved == True, User.role != RoleEnum.superadmin).all()
    return templates.TemplateResponse("manage_users.html", {"request": request, "users": approved_users})

@router.post("/delete-user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403)

    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return RedirectResponse("/superadmin/manage-users", status_code=303)


@router.get("/analytics-ui", response_class=HTMLResponse)
def render_analytics_ui(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403)
    
    return templates.TemplateResponse("analytics_dashboard.html", {"request": request})
