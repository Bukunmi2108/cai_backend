import string
from tempfile import template
from sqlalchemy import TEXT, Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB 
from sqlalchemy.sql import func
import uuid
from .db import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    chats = relationship("ChatHistory", back_populates="user")

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=True)  # Add the title column
    messages = Column(JSONB) 
    created_at = Column(DateTime, server_default=func.now())  # Add the timestamp column
    user = relationship("User", back_populates="chats")

class DocumentTemplate(Base):
    __tablename__="document_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True)
    description = Column(TEXT, nullable=True)
    fields_schema = Column(JSONB)
    template_content = Column(JSONB, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("template_categories.id"))
    created_at = Column(DateTime, server_default=func.now())
    category = relationship("TemplateCategory", back_populates="templates")

class TemplateCategory(Base):
    __tablename__='template_categories'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True)
    templates = relationship("DocumentTemplate", back_populates='category')