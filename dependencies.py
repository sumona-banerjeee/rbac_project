from fastapi import Depends, HTTPException, Cookie, Request
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from database import get_db
from models import User, RoleEnum, PermissionEnum, Resource, ResourcePermission


SECRET_KEY = "54baa32cf3b3cd8a83179b9e4e3f483c244498fcc6c2183cc746e926f6b47e30"
ALGORITHM = "HS256"


def get_current_user(
    access_token: str = Cookie(default=None),
    db: Session = Depends(get_db)
) -> User:
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


def require_superadmin(user: User = Depends(get_current_user)):
    if user.role != RoleEnum.superadmin:
        raise HTTPException(status_code=403, detail="Only Superadmin can access this route")
    return user


def require_permission(permission: str, resource_name: bool = False):
    def checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        
        if current_user.role == RoleEnum.superadmin:
            return current_user

        
        if permission in [p.name for p in current_user.permissions]:
            return current_user

        
        if resource_name:
            resource_key = request.path_params.get("name")
            resource = db.query(Resource).filter_by(name=resource_key).first()
            if not resource:
                raise HTTPException(status_code=404, detail="Resource not found")

            rp = db.query(ResourcePermission).filter_by(
                user_id=current_user.id,
                resource_id=resource.id
            ).first()

            if not rp:
                raise HTTPException(status_code=403, detail="No permission for this resource")

            if (
                (permission == "read" and rp.can_read) or
                (permission == "create" and rp.can_create) or
                (permission == "update" and rp.can_update) or
                (permission == "delete" and rp.can_delete)
            ):
                return current_user

        raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")

    return checker

