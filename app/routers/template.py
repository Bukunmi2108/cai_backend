from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
import json
from .. import models, schemas, auth
from ..db import get_db
# from ..auth import auth

router = APIRouter(prefix="/template", tags=['Templates'])

# --- Dependency for Protected Routes ---
# async def get_current_active_user(current_user: models.User = Depends(auth.get_current_user)):
#     return current_user
async def get_current_active_user():
    return True


# --- SFDT Validation Helper ---
def validate_sfdt(sfdt_content: dict) -> bool:
    """Basic SFDT structure validation"""
    if not isinstance(sfdt_content, dict):
        return False
    if 'sections' not in sfdt_content:
        return False
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
    
    if template_content_file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Template content must be SFDT JSON")

    try:
        # Parse and validate fields schema
        fields_schema_content = await fields_schema_file.read()
        fields_schema = json.loads(fields_schema_content.decode("utf-8"))
        
        # Parse and validate SFDT
        sfdt_content = json.loads((await template_content_file.read()).decode("utf-8"))
        if not validate_sfdt(sfdt_content):
            raise HTTPException(status_code=400, detail="Invalid SFDT structure")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    db_template = models.DocumentTemplate(
        name=name,
        description=description,
        fields_schema=fields_schema,
        template_content=sfdt_content,  # Store as JSON
        category_id=category_id,
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.get("/get/all", response_model=List[schemas.DocumentTemplateRead])
def read_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    return db.query(models.DocumentTemplate).offset(skip).limit(limit).all()

@router.get("/get/{template_id}", response_model=schemas.DocumentTemplateRead)
def read_template(template_id: UUID, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not db_template:
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
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    if fields_schema_file:
        if fields_schema_file.content_type != "application/json":
            raise HTTPException(status_code=400, detail="Fields schema file must be JSON")
        try:
            fields_schema_content = await fields_schema_file.read()
            db_template.fields_schema = json.loads(fields_schema_content.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in fields schema")

    if template_content_file:
        if template_content_file.content_type != "application/json":
            raise HTTPException(status_code=400, detail="Template content must be SFDT JSON")
        try:
            sfdt_content = json.loads((await template_content_file.read()).decode("utf-8"))
            if not validate_sfdt(sfdt_content):
                raise HTTPException(status_code=400, detail="Invalid SFDT structure")
            db_template.template_content = sfdt_content
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid SFDT JSON")

    if name:
        db_template.name = name
    if description:
        db_template.description = description
    if category_id:
        db_template.category_id = category_id

    db.commit()
    db.refresh(db_template)
    return db_template

# @router.delete("/delete/all", dependencies=[Depends(get_current_active_user)])
# def delete_template(db: Session = Depends(get_db)):
#     db_templates = db.query(models.DocumentTemplate).all()
#     if not db_templates:
#         raise HTTPException(status_code=404, detail="Templates not found")
#     for template in db_templates:
#         db.delete(template)
#     db.commit()
#     return 


@router.delete("/delete/{template_id}", response_model=schemas.DocumentTemplateRead, dependencies=[Depends(get_current_active_user)])
def delete_template(template_id: UUID, db: Session = Depends(get_db), current_user: bool = Depends(get_current_active_user)):
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(db_template)
    db.commit()
    return db_template

# --- SFDT Processing Endpoint ---
@router.post("/{template_id}/process", response_model=schemas.ProcessedSfdtResponse)
async def process_sfdt_template(
    template_id: UUID,
    field_data: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: bool = Depends(get_current_active_user),
):
    """
    Populates SFDT template with field data and returns modified SFDT
    """
    db_template = db.query(models.DocumentTemplate).filter(models.DocumentTemplate.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Deep copy the SFDT content
    processed_sfdt = json.loads(json.dumps(db_template.template_content))
    
    # Recursive placeholder replacement
    def replace_placeholders(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    for field, value in field_data.items():
                        obj[k] = v.replace(f"{{{{{field}}}}}", value)
                else:
                    replace_placeholders(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_placeholders(item)
    
    replace_placeholders(processed_sfdt)
    
    return {"processed_sfdt": processed_sfdt}


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
