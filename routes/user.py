from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from dependencies import require_permission
from sqlalchemy.orm import Session
from dependencies import get_db
from crud import get_products



router = APIRouter(prefix="/user", tags=["User"])
templates = Jinja2Templates(directory="templates")

@router.get("/read")
def read_content(user=Depends(require_permission("read"))):
    return {"msg": "User has read access"}

@router.get("/dashboard")
def user_dashboard(request: Request, user=Depends(require_permission("read"))):
    return templates.TemplateResponse("user_dashboard.html", {
        "request": request,
        "user": user
    })


@router.get("/products")
def browse_products(request: Request, db: Session = Depends(get_db), user=Depends(require_permission("read"))):
    products = get_products(db)
    return templates.TemplateResponse("user_products.html", {"request": request, "products": products, "user": user})
