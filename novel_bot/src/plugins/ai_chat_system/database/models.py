# novel_bot/src/plugins/ai_chat_system/database/models.py

import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, UniqueConstraint
)
# [核心修复] 从 dialects.postgresql 导入 JSONB 的语句被移除
# [核心修复] 导入通用的、跨数据库的 JSON 类型
from sqlalchemy.types import JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False, unique=True)
    account_number = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # --- 原 user_configs.json 的内容 ---
    security_questions_hash = Column(String, nullable=True)
    active_character_filename = Column(String, nullable=True)
    active_session_id = Column(String, nullable=True)
    user_persona_filename = Column(String, nullable=True)
    preset_filename = Column(String, nullable=True)
    # [核心修复] 将所有 JSONB 替换为通用的 JSON
    active_modules = Column(JSON, default=dict)
    max_tokens = Column(Integer, default=4096)
    session_world_info = Column(JSON, default=list) # world_info
    display_order = Column(JSON, default=dict)
    regex_rules = Column(JSON, default=list)
    generation_profiles = Column(JSON, default=dict)
    deleted_public_items = Column(JSON, default=list)
    tts_voice_assignments = Column(JSON, default=dict)
    tts_service_config = Column(JSON, default=dict)
    api_keys = Column(JSON, default=list)
    llm_service_config = Column(JSON, default=dict)
    has_completed_onboarding = Column(Boolean, default=False)
    
    # Relationships
    content_items = relationship("ContentItem", back_populates="owner")
    sessions = relationship("Session", back_populates="owner")
    
class ContentItem(Base):
    __tablename__ = 'content_items'
    id = Column(Integer, primary_key=True)
    owner_id = Column(String, ForeignKey('users.user_id'), nullable=True, index=True) # NULL for public
    data_type = Column(String, nullable=False, index=True) # 'character', 'preset', 'world_info', etc.
    filename = Column(String, nullable=False, index=True)
    data = Column(JSON, nullable=False) # [核心修复] JSONB -> JSON
    
    owner = relationship("User", back_populates="content_items")
    
    __table_args__ = (UniqueConstraint('owner_id', 'data_type', 'filename', name='_owner_type_filename_uc'),)
    
class Session(Base):
    __tablename__ = 'sessions'
    id = Column(String, primary_key=True) # UUID
    owner_id = Column(String, ForeignKey('users.user_id'), nullable=False, index=True)
    character_filename = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, default="新对话")
    created_at = Column(Float, nullable=False)
    last_updated_at = Column(Float, nullable=False)

    owner = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.timestamp")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True)
    session_id = Column(String, ForeignKey('sessions.id'), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    role = Column(String, nullable=False) # 'user' or 'model'
    content = Column(Text, nullable=False)
    token_usage = Column(JSON, nullable=True) # [核心修复] JSONB -> JSON
    
    session = relationship("Session", back_populates="messages")

class SharedContent(Base):
    __tablename__ = 'shared_content'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(JSON, nullable=True) # [核心修复] JSONB -> JSON
    file_path = Column(String, nullable=False)
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_approved = Column(Boolean, default=True)

    __table_args__ = (UniqueConstraint('data_type', 'name', name='_shared_type_name_uc'),)
    
class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True) # UUID
    user_id = Column(String, nullable=False, index=True)
    task_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    progress = Column(Integer, default=0)
    status_text = Column(String, nullable=True)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    result = Column(JSON, nullable=True) # [核心修复] JSONB -> JSON
    error = Column(JSON, nullable=True) # [核心修复] JSONB -> JSON