import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# 1. 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "saea_data.db")
# 优先读取环境变量，默认回退到当前目录下的 db 文件
SQLALCHEMY_DATABASE_URL = os.getenv("DB_PATH", f"sqlite:///{DB_PATH}")

# 2. 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 3. 定义数据表结构 (去物理化版本)
# ==========================================
class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    cst_path = Column(String)
    status = Column(String, default="running")
    config_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)

class Generation(Base):
    __tablename__ = "generations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    gen_index = Column(Integer, index=True)
    best_score = Column(Float)
    best_metrics_json = Column(JSON)  # 动态收纳当代最优个体的所有标量指标

class Individual(Base):
    __tablename__ = "individuals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    gen_index = Column(Integer, index=True)
    ind_index = Column(Integer)
    params_json = Column(JSON)
    score = Column(Float)
    metrics_json = Column(JSON)       # 动态收纳该个体的所有标量指标 (替代原 power_val, eff_val 等)
    is_valid = Column(Boolean, default=True)

class Waveform(Base):
    __tablename__ = "waveforms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    individual_id = Column(Integer, ForeignKey("individuals.id"), index=True)
    task_id = Column(String, index=True)
    gen_index = Column(Integer)
    ind_index = Column(Integer)
    waves_json = Column(JSON)         # 动态收纳所有的波形字典，前端按 Key 解析即可


class NnOnlineLog(Base):
    __tablename__ = "nn_online_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    gen_index = Column(Integer, index=True)
    loss = Column(Float)
    error = Column(Float)
    details_json = Column(JSON, nullable=True)  # 预留字段：记录学习率等其他微调超参


# ==========================================
# 4. 身份认证与文献助手相关数据表
# ==========================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    # 一个用户可以有多个研讨会话
    sessions = relationship("ChatSession", back_populates="owner", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(50), primary_key=True, index=True)  # 采用前端传来的时间戳字符串作为 ID
    title = Column(String(100), default="新文献研讨")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' 或 'ai'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ChatSession", back_populates="messages")


def init_db():
    Base.metadata.create_all(bind=engine)