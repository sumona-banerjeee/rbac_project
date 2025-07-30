from fastapi import Depends, HTTPException, Cookie
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from models import User, RoleEnum
from database import get_db
from fastapi import Depends, HTTPException
from models import RoleEnum

SECRET_KEY = "54baa32cf3b3cd8a83179b9e4e3f483c244498fcc6c2183cc746e926f6b47e30"
ALGORITHM = "HS256"

# ✅ Authenticated user from cookie
def get_current_user(
    access_token: str = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = access_token.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_approved:
        raise HTTPException(status_code=403, detail="User not approved by admin")

    return user




# ✅ Add this below get_current_user
def require_superadmin(user=Depends(get_current_user)):
    if user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403, detail="Only Superadmin can access this route")
    return user




# ✅ Permission-checking dependency
def require_permission(permission: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role == RoleEnum.superadmin:
            return user  # Superadmin bypasses permission checks

        # Check if user has the required permission
        if permission not in [p.name for p in user.permissions]:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")

        return user
    return checker



