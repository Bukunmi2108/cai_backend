import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Any, List, Dict, Optional
import uuid

from fastapi import UploadFile
from sqlalchemy import JSON

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: uuid.UUID
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    chat_id: Optional[uuid.UUID] = None
    message: str

class ChatResponse(BaseModel):
    response: str
    history: List[Message]
    chat_id: uuid.UUID
    title: Optional[str] = None

class ChatHistoryResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    messages: List[Message]
    user_id: uuid.UUID

    class Config:
        from_attributes = True


class TemplateCategoryBase(BaseModel):
    name: str

class TemplateCategoryCreate(TemplateCategoryBase):
    pass

class TemplateCategoryUpdate(TemplateCategoryBase):
    pass

class DocumentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: uuid.UUID

class DocumentTemplateCreate(DocumentTemplateBase):
    fields_schema_file: UploadFile
    template_content_file: UploadFile

class DocumentTemplateUpdate(DocumentTemplateBase):
    name: Optional[str] = None
    description: Optional[str] = None
    fields_schema_file: Optional[UploadFile] = None
    template_content_file: Optional[UploadFile] = None
    category_id: Optional[uuid.UUID] = None

# --- Schemas for Read Operations (Handling Circular Dependency) ---

class DocumentTemplateRead(DocumentTemplateBase):
    id: uuid.UUID
    created_at: datetime.datetime
    fields_schema: Dict[str, Any]
    template_content: str
    category: Optional["TemplateCategoryReadWithoutTemplates"] = None  # Exclude templates here

    class Config:
        from_attributes = True

class TemplateCategoryReadWithoutTemplates(TemplateCategoryBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class TemplateCategoryRead(TemplateCategoryBase):
    id: uuid.UUID
    templates: Optional[List["DocumentTemplateReadWithoutCategory"]] = None

    class Config:
        from_attributes = True

class DocumentTemplateReadWithoutCategory(DocumentTemplateBase):
    id: uuid.UUID
    created_at: datetime.datetime
    fields_schema: Dict[str, Any]
    template_content: str

    class Config:
        from_attributes = True

class TemplateCategory(TemplateCategoryBase):
    id: uuid.UUID
    templates: Optional[List["DocumentTemplateRead"]] = None

    class Config:
        from_attributes = True

class DocumentTemplate(DocumentTemplateBase):
    id: uuid.UUID
    created_at: datetime.datetime
    fields_schema: Dict[str, Any]
    template_content: str
    category: Optional["TemplateCategory"] = None

    class Config:
        from_attributes = True

# --- Response Schema for Template Schema ---

class TemplateSchemaResponse(BaseModel):
    fields_schema: Dict[str, Any]