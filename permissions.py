from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from models import User
from dependencies import get_current_user
from database import get_db

def check_permission(resource: str, action: str):
    def permission_dependency(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
    ):
        if not current_user.has_permission(db, resource, action):
            raise HTTPException(status_code=403, detail="Access Denied")
        return current_user
    return permission_dependency
