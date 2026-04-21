import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "saea_data.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 2. 创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==========================================
# 3. 定义数据表结构 (🌟 终极去物理化版本)
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
    best_metrics_json = Column(JSON)  # ✨ 动态收纳当代最优个体的所有标量指标

class Individual(Base):
    __tablename__ = "individuals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    gen_index = Column(Integer, index=True)
    ind_index = Column(Integer)
    params_json = Column(JSON)
    score = Column(Float)
    metrics_json = Column(JSON)       # ✨ 动态收纳该个体的所有标量指标 (替代原 power_val, eff_val 等)
    is_valid = Column(Boolean, default=True)

class Waveform(Base):
    __tablename__ = "waveforms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    individual_id = Column(Integer, ForeignKey("individuals.id"), index=True)
    task_id = Column(String, index=True)
    gen_index = Column(Integer)
    ind_index = Column(Integer)
    waves_json = Column(JSON)         # ✨ 动态收纳所有的波形字典，前端按 Key 解析即可

def init_db():
    Base.metadata.create_all(bind=engine)