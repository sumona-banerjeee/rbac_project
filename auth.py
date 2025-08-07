from datetime import datetime, timedelta
from jose import jwt



SECRET_KEY = "54baa32cf3b3cd8a83179b9e4e3f483c244498fcc6c2183cc746e926f6b47e30"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
