from dotenv import load_dotenv
import os


load_dotenv()


SUPERADMIN_NAME = os.getenv("SUPERADMIN_NAME")
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD")

from fastapi import FastAPI, Request
from database import engine, Base, SessionLocal
from routes import superadmin, admin, user, auth_routes
from models import User, RoleEnum, PermissionEnum, Permission, Resource
import bcrypt
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)

app.include_router(superadmin.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(auth_routes.router)


def seed_permissions(db):
    for perm in PermissionEnum:
        if not db.query(Permission).filter_by(name=perm.value).first():
            db.add(Permission(name=perm.value))
    db.commit()


def seed_resources(db):
    default_resources = [
        "users_management", "product_listings",
        "reports_analytics", "payments_verification",
        "announcements", "Dashboard"
    ]
    for res in default_resources:
        if not db.query(Resource).filter_by(name=res).first():
            db.add(Resource(name=res))
    db.commit()


@app.on_event("startup")
def create_default_superadmin():
    db = SessionLocal()

    seed_permissions(db)
    seed_resources(db)

    existing_superadmin = db.query(User).filter_by(email=SUPERADMIN_EMAIL).first()
    if not existing_superadmin:
        hashed_pw = bcrypt.hashpw(SUPERADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
        superadmin = User(
            name=SUPERADMIN_NAME,
            email=SUPERADMIN_EMAIL,
            password=hashed_pw,
            role=RoleEnum.superadmin,
            is_approved=True,
            is_active=1
        )
        db.add(superadmin)
        db.commit()
        print(f"Superadmin created with email: {SUPERADMIN_EMAIL}")
    else:
        print("Superadmin already exists")

    db.close()


templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
