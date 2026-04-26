from datetime import datetime, timedelta
from typing import Optional
import json
import os

import bcrypt
from jose import JWTError, jwt

SECRET_KEY         = "sap_budget_ia_secret_key_2026_pfe"
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = 24

current_file  = os.path.abspath(__file__)
ia_server_dir = os.path.dirname(current_file)
USERS_FILE    = os.path.join(ia_server_dir, "users.json")
def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def _save_users(users: dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def register_user(email: str, password: str, nom: str, role: str = "comptable") -> dict:
    users = _load_users()
    if email in users:
        return {"error": "Cet email est déjà utilisé."}
    users[email] = {
        "email":      email,
        "nom":        nom,
        "role":       role,
        "password":   hash_password(password),
        "created_at": datetime.utcnow().isoformat()
    }
    _save_users(users)
    return {"success": True, "email": email, "nom": nom, "role": role}

def login_user(email: str, password: str) -> dict:
    users = _load_users()
    if email not in users:
        return {"error": "Email ou mot de passe incorrect."}
    user = users[email]
    if not verify_password(password, user["password"]):
        return {"error": "Email ou mot de passe incorrect."}
    token = create_token({"sub": email, "nom": user["nom"], "role": user["role"]})
    return {
        "success":    True,
        "token":      token,
        "email":      email,
        "nom":        user["nom"],
        "role":       user["role"],
        "expires_in": TOKEN_EXPIRE_HOURS * 3600
    }

def get_current_user(token: str) -> Optional[dict]:
    payload = decode_token(token)
    if not payload:
        return None
    return {
        "email": payload.get("sub"),
        "nom":   payload.get("nom"),
        "role":  payload.get("role")
    }

