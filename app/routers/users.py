from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas, auth
from ..db import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.User)
async def update_user_me(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_user = db.query(models.User).filter((models.User.username == user.username) & (models.User.id != current_user.id)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already in use")

    db_user = db.query(models.User).filter((models.User.email == user.email) & (models.User.id != current_user.id)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    current_user.username = user.username
    current_user.email = user.email
    current_user.hashed_password = auth.get_password_hash(user.password)

    db.commit()
    db.refresh(current_user)
    return current_user
