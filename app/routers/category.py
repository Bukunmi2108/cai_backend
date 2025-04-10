from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from .. import models, schemas
from ..db import get_db
# from ..auth import auth  

router = APIRouter(prefix="/category", tags=['Categories'])

# --- Dependency for Protected Routes ---
# async def get_current_active_user(current_user: models.User = Depends(auth.get_current_user)):
#     return current_user
async def get_current_active_user():
    return True

# --- TemplateCategory Routes ---

@router.post("/create", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
def create_category(category: schemas.TemplateCategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    db_category = models.TemplateCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/all", response_model=List[schemas.TemplateCategoryRead])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    categories = db.query(models.TemplateCategory).offset(skip).limit(limit).all()
    return categories

@router.get("/info", response_model=List[schemas.TemplateCategoryReadWithoutTemplates])
def read_categories_names_and_id(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    categories = db.query(models.TemplateCategory).all()
    return categories

@router.get("/{category_id}", response_model=schemas.TemplateCategoryRead)
def read_category(category_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/{category_id}", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
def update_category(category_id: UUID, category: schemas.TemplateCategoryUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.model_dump(exclude_unset=True).items():
        setattr(db_category, key, value)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
def delete_category(category_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return db_category