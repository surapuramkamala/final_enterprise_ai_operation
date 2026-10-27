
import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash

router = APIRouter(tags=["Authentication"])

DB_PATH = Path(__file__).resolve().parent.parent / "users.db"
password_hash = PasswordHash.recommended()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        """)


init_db()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


@router.post("/register", status_code=201)
def register(data: RegisterRequest):
    username = data.username.strip()
    email = str(data.email).lower()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required"
        )

    hashed_password = password_hash.hash(data.password)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username, email, hashed_password)
            )
            user_id = cursor.lastrowid

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

    return {
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "username": username,
            "email": email
        }
    }
