
import time
import jwt

from app.config import JWT_SECRET

token = jwt.encode(
    {
        "sub": "employee-101",
        "role": "admin",
        "exp": int(time.time()) + 3600,
    },
    JWT_SECRET,
    algorithm="HS256",
)

print(token)
