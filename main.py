from fastapi import FastAPI
from database import engine, Base, SessionLocal
from routes import superadmin, admin, user, auth_routes  # ✅ Include auth_routes
from models import User, RoleEnum, PermissionEnum, Permission
import bcrypt
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)


# ✅ Include routers
app.include_router(superadmin.router)
app.include_router(admin.router)
app.include_router(user.router)
app.include_router(auth_routes.router)  # ✅ Include auth routes

# ✅ Function to seed permissions
def seed_permissions(db):
    for perm in PermissionEnum:
        if not db.query(Permission).filter_by(name=perm.value).first():
            db.add(Permission(name=perm.value))
    db.commit()

# ✅ Create default superadmin on startup
@app.on_event("startup")
def create_default_superadmin():
    db = SessionLocal()

    seed_permissions(db)

    existing_superadmin = db.query(User).filter_by(email="sumobanerjee2000@gmail.com").first()
    if not existing_superadmin:
        hashed_pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        superadmin = User(
            name="Sumona Banerjee",
            email="sumobanerjee2000@gmail.com",
            password=hashed_pw,
            role=RoleEnum.superadmin,
            is_approved=True,
            is_active=1
        )
        db.add(superadmin)
        db.commit()
        print("✅ Superadmin created with email: sumobanerjee2000@gmail.com and password: admin123")
    else:
        print("ℹ️ Superadmin already exists")

    db.close()



templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
