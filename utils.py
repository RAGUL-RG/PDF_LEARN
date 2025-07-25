from fastapi import Header, HTTPException, Depends
import jwt, os

def get_user_email(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        decoded = jwt.decode(token, os.getenv("JWT_SECRET", "secret"), algorithms=["HS256"])
        return decoded["email"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")