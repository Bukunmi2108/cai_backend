from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import uuid

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