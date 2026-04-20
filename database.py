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
# 3. 定义数据表结构
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
    best_eff = Column(Float)
    best_power = Column(Float)
    best_freq = Column(Float)

class Individual(Base):
    __tablename__ = "individuals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"), index=True)
    gen_index = Column(Integer, index=True)
    ind_index = Column(Integer)
    params_json = Column(JSON)
    score = Column(Float)
    power_val = Column(Float)
    eff_val = Column(Float)
    freq_val = Column(Float)
    side_ratio = Column(Float, nullable=True)
    is_valid = Column(Boolean, default=True)

# ✨ [新增] 第四张表：专门存储庞大的波形数据
class Waveform(Base):
    __tablename__ = "waveforms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    individual_id = Column(Integer, ForeignKey("individuals.id"), index=True) # 绑定到具体的个体
    task_id = Column(String, index=True)
    gen_index = Column(Integer)
    ind_index = Column(Integer)
    power_wave = Column(JSON)    # 功率波形字典
    eff_wave = Column(JSON)      # 效率波形字典
    fft_wave = Column(JSON)      # 频谱波形字典
    main_mode_wave = Column(JSON)# 主模波形字典

def init_db():
    Base.metadata.create_all(bind=engine)