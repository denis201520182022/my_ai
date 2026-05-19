# app/database/models.py
import datetime
from typing import Any
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, Text, Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector  # Расширение для работы с векторами

from app.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Связи
    messages = relationship("ChatMessage", back_populates="user")
    reminders = relationship("Reminder", back_populates="user")
    knowledge = relationship("VectorKnowledge", back_populates="user")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=False, index=True)  # Для группировки диалогов
    role = Column(String, nullable=False)  # 'user' или 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="messages")

class VectorKnowledge(Base):
    __tablename__ = "vector_knowledge"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Сам текст куска данных
    # Векторное представление текста (для rubert-tiny2 размерность 312)
    embedding = Column(Vector(312)) 
    metadata_ = Column(JSONB, default={}) # Доп. данные (источник, дата и т.д.)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="knowledge")

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    remind_at = Column(DateTime, nullable=False)  # Когда напомнить
    is_triggered = Column(Boolean, default=False)  # Выполнено ли
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="reminders")