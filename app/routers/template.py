from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from .. import models, schemas
from ..db import get_db
# from ..auth import auth

router = APIRouter(prefix="/template", tags=['Templates'])

# --- Dependency for Protected Routes ---
# async def get_current_active_user(current_user: models.User = Depends(auth.get_current_user)):
#     return current_user
async def get_current_active_user():
    return True

# --- DocumentTemplate Routes ---

@router.post("/create", response_model=schemas.DocumentTemplateRead, dependencies=[Depends(get_current_active_user)])
async def create_template(
    name: str = File(...),
    description: Optional[str] = File(None),
    fields_schema_file: UploadFile = File(...),
    template_content_file: UploadFile = File(...),
    category_id: UUID = File(...),
    db: Session = Depends(get_db),
    current_user: bool = Depends(get_current_active_user),
):
    existing_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.name == name).first()
    if existing_template:
        raise HTTPException(status_code=400, detail=f"Template with name '{name}' already exists")

    if fields_schema_file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Fields schema file must be JSON")
    
    if template_content_file.content_type not in ["text/markdown", "text/plain"]:
        raise HTTPException(status_code=400, detail="Template content file must be Markdown or plain text")

    try:
        fields_schema_content = await fields_schema_file.read()
        fields_schema = json.loads(fields_schema_content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in fields schema file")

    template_content = (await template_content_file.read()).decode("utf-8")

    db_template = models.DocumentTemplate(
        name=name,
        description=description,
        fields_schema=fields_schema,
        template_content=template_content,
        category_id=category_id,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/get/all", response_model=List[schemas.DocumentTemplateRead])
def read_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    templates = db.query(models.DocumentTemplate).offset(skip).limit(limit).all()
    return templates

@router.get("/get/{template_id}", response_model=schemas.DocumentTemplateRead)
def read_template(template_id: UUID, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

@router.put("/update/{template_id}", response_model=schemas.DocumentTemplateRead, dependencies=[Depends(get_current_active_user)])
async def update_template(
    template_id: UUID,
    name: Optional[str] = File(None),
    description: Optional[str] = File(None),
    fields_schema_file: Optional[UploadFile] = File(None),
    template_content_file: Optional[UploadFile] = File(None),
    category_id: Optional[UUID] = File(None),
    db: Session = Depends(get_db),
    current_user: bool = Depends(get_current_active_user),
):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    if fields_schema_file:
        if fields_schema_file.content_type != "application/json":
            raise HTTPException(status_code=400, detail="Fields schema file must be JSON")
        try:
            fields_schema_content = await fields_schema_file.read()
            fields_schema = json.loads(fields_schema_content.decode("utf-8"))
            db_template.fields_schema = fields_schema
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in fields schema file")

    if template_content_file:
        if template_content_file.content_type not in ["text/markdown", "text/plain"]:
            raise HTTPException(status_code=400, detail="Template content file must be Markdown or plain text")
        template_content = (await template_content_file.read()).decode("utf-8")
        db_template.template_content = template_content

    if name:
        db_template.name = name
    if description:
        db_template.description = description
    if category_id:
        db_template.category_id = category_id

    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.delete("/delete/{template_id}", response_model=schemas.DocumentTemplateRead, dependencies=[Depends(get_current_active_user)])
def delete_template(template_id: UUID, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(db_template)
    db.commit()
    return db_template

# --- Additional Template Routes (Potentially Useful) ---

@router.get("/{category_id}/templates/", response_model=List[schemas.DocumentTemplateRead])
def read_templates_by_category(category_id: UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    templates = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.category_id == category_id).offset(skip).limit(limit).all()
    return templates

@router.get("/by_name/{template_name}", response_model=schemas.DocumentTemplateRead)
def read_template_by_name(template_name: str, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.name == template_name).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template

# --- Route to get the schema for a specific template ---
@router.get("/{template_id}/schema", response_model=schemas.TemplateSchemaResponse)
def read_template_schema(template_id: UUID, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"fields_schema": db_template.fields_schema}

# --- Route to get the markdown for a specific template ---
@router.post("/{template_id}/markdown", response_model=schemas.TemplateMarkdownResponse)
def read_template_markdown(
    template_id: UUID,
    field_data: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    """
    Retrieves the markdown content for a specific document template,
    populated with the provided field data.
    """
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    markdown_content = db_template.template_content

    for field, value in field_data.items():
        placeholder = f"{{{{{field}}}}}"
        markdown_content = markdown_content.replace(placeholder, value)

    return schemas.TemplateMarkdownResponse(template_content=markdown_content)