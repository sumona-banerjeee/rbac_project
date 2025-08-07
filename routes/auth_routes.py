from fastapi import APIRouter, Request, Form, Depends, Response, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User, RoleEnum
from auth import create_access_token
from utils.email_utils import send_email  # ✅ Import email utility
import bcrypt
from routes import superadmin, admin, user, auth_routes


router = APIRouter()
templates = Jinja2Templates(directory="templates")



@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@router.post("/login")
def login_user(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(email=email).first()
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "User not found"
        })

    if not user.is_approved:
        return RedirectResponse("/waiting-approval", status_code=303)

    if user.is_denied:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Access denied by admin"
        })

    if not bcrypt.checkpw(password.encode(), user.password.encode()):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid password"
        })

    
    access_token = create_access_token(data={"sub": user.email})

    
    response = RedirectResponse(
        url=(
            "/superadmin/dashboard" if user.role == RoleEnum.superadmin else
            "/admin/dashboard" if user.role == RoleEnum.admin else
            "/user/dashboard"
        ),
        status_code=303
    )
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        path="/"
    )

    return response



@router.get("/logout")
def logout():
    response = RedirectResponse("/login")
    response.delete_cookie("access_token")
    return response



@router.get("/waiting-approval", response_class=HTMLResponse)
def waiting_approval(request: Request):
    return templates.TemplateResponse("waiting_approval.html", {"request": request})



@router.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})



@router.post("/signup")
def signup_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    
    existing_user = db.query(User).filter_by(email=email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    
    new_user = User(
        name=name,
        email=email,
        password=hashed_pw,
        is_approved=False,  
        is_active=1,
        role=None  
    )
    db.add(new_user)
    db.commit()

    
    superadmin = db.query(User).filter(User.role == RoleEnum.superadmin).first()
    if superadmin:
        subject = "New User Signup Notification"
        body = f"""
        Hello Superadmin,

        A new user has signed up with the email: {new_user.email}
        Please login and assign a role.

        Regards,
        RBAC System
        """
        send_email(subject, superadmin.email, body)

    return RedirectResponse("/waiting-approval", status_code=303)