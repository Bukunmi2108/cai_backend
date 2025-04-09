import datetime
from pydantic import BaseModel, EmailStr
from typing import Any, List, Dict, Optional
import uuid

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
    title: Optional[str] = None  # Add the title field
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

class TemplateCategory(TemplateCategoryBase):
    id: uuid.UUID
    templates: Optional[List["DocumentTemplate"]] = None  # Forward reference to avoid circular dependency

    class Config:
        from_attributes = True

# --- DocumentTemplate Schemas ---

class DocumentTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    fields_schema: Dict[str, Any]
    template_content: str
    category_id: uuid.UUID

class DocumentTemplateCreate(DocumentTemplateBase):
    pass

class DocumentTemplateUpdate(DocumentTemplateBase):
    name: Optional[str] = None
    fields_schema: Optional[Dict[str, Any]] = None
    template_content: Optional[str] = None
    category_id: Optional[uuid.UUID] = None

class DocumentTemplate(DocumentTemplateBase):
    id: uuid.UUID
    created_at: datetime.datetime
    category: Optional[TemplateCategory] = None

    class Config:
        from_attributes = True

# --- Response Schema for Template Schema ---

class TemplateSchemaResponse(BaseModel):
    fields_schema: Dict[str, Any]

# Update forward reference
TemplateCategory.model_rebuild()