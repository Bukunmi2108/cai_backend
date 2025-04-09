from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from .. import models, schemas
from ..db import get_db
# from ..auth import auth  

router = APIRouter(prefix="/template", tags=['Templates'])

# --- Dependency for Protected Routes ---
# async def get_current_active_user(current_user: models.User = Depends(auth.get_current_user)):
#     return current_user
async def get_current_active_user():
    return True

# --- TemplateCategory Routes ---

@router.post("/categories/", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
def create_category(category: schemas.TemplateCategoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    db_category = models.TemplateCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.TemplateCategory])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    categories = db.query(models.TemplateCategory).offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.TemplateCategory)
def read_category(category_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
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

@router.delete("/categories/{category_id}", response_model=schemas.TemplateCategory, dependencies=[Depends(get_current_active_user)])
def delete_category(category_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_category = db.query(models.TemplateCategory).filter(models.TemplateCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return db_category

# --- DocumentTemplate Routes ---

@router.post("/templates/", response_model=schemas.DocumentTemplate, dependencies=[Depends(get_current_active_user)])
def create_template(template: schemas.DocumentTemplateCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = models.DocumentTemplate(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/templates/", response_model=List[schemas.DocumentTemplate])
def read_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    templates = db.query(models.DocumentTemplate).offset(skip).limit(limit).all()
    return templates

@router.get("/templates/{template_id}", response_model=schemas.DocumentTemplate)
def read_template(template_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.put("/templates/{template_id}", response_model=schemas.DocumentTemplate, dependencies=[Depends(get_current_active_user)])
def update_template(template_id: UUID, template: schemas.DocumentTemplateUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, value in template.model_dump(exclude_unset=True).items():
        setattr(db_template, key, value)
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/templates/{template_id}", response_model=schemas.DocumentTemplate, dependencies=[Depends(get_current_active_user)])
def delete_template(template_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(db_template)
    db.commit()
    return db_template

# --- Additional Template Routes (Potentially Useful) ---

@router.get("/categories/{category_id}/templates/", response_model=List[schemas.DocumentTemplate])
def read_templates_by_category(category_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    templates = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.category_id == category_id).offset(skip).limit(limit).all()
    return templates

@router.get("/templates/by_name/{template_name}", response_model=schemas.DocumentTemplate)
def read_template_by_name(template_name: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.name == template_name).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

# --- Example of a route to get the schema for a specific template ---
@router.get("/templates/{template_id}/schema", response_model=schemas.TemplateSchemaResponse)
def read_template_schema(template_id: UUID, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"schema": db_template.schema}