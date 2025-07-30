from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, RoleEnum, Permission
from dependencies import get_current_user, require_permission
from database import get_db
from dependencies import require_superadmin


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
