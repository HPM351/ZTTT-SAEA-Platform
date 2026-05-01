from pydantic import BaseModel
from typing import List, Optional, Dict, Any

# --- 1. 变量参数模型 ---
class ParamItem(BaseModel):
    id: str
    name: str
    min: float
    max: float
    val: float
    opt: bool

# --- 2. 环境配置模型 ---
class EnvConfig(BaseModel):
    stableTime: float

# --- 3. 目标门控配置模型 ---
class FreqTarget(BaseModel):
    enable: bool
    path: str
    target: float
    blindGap: float
    clutterPenalty: float
    decayK: float
    penaltyBase: float

class PowerTarget(BaseModel):
    enable: bool
    mode: str
    path: str
    target: float
    deadThresh: float
    weight: float
    fluc: float

class EffTarget(BaseModel):
    enable: bool
    mode: str
    path: str
    checkPhys: Optional[bool] = True
    target: float
    deadThresh: float
    weight: float
    fluc: float

class MainModeTarget(BaseModel):
    enable: bool
    path: str

class TargetsConfig(BaseModel):
    freq: FreqTarget
    power: PowerTarget
    eff: EffTarget
    mainMode: Optional[MainModeTarget] = None

# ==========================================
# 4. 各算法独立配置子模型 (完美适配前端嵌套结构)
# ==========================================
class GaConfig(BaseModel):
    recCode: str
    pc: float
    mutCode: str
    pm: float
    useAutoMut: Optional[bool] = False
    autoMutRange: Optional[List[int]] = [30, 70]

class PsoConfig(BaseModel):
    w: float
    c1: float
    c2: float

class BoConfig(BaseModel):
    acqFunc: str
    useAutoAcq: Optional[bool] = True
    kappa: float
    xi: float

class AlgoConfig(BaseModel):
    type: str = "SAEA-GA"  # ✨ 核心修复 1：注册算法类型，确保 BO 和 PSO 能被识别
    nPop: int
    nGen: int
    injectJson: Optional[str] = ""

    # 核心修复 2：以嵌套子模型的方式注册专属参数
    # 使用 Optional 确保在旧数据加载时即使没有某些模块也不会崩溃
    ga: Optional[GaConfig] = None
    pso: Optional[PsoConfig] = None
    bo: Optional[BoConfig] = None

# --- 5. 总体请求配置模型 (对应前端的 config) ---
class OptimizationConfig(BaseModel):
    selectedHistoryPath: Optional[str] = None
    cstPath: str
    selectedHistoryTask: Optional[str] = None
    taskName: str
    env: EnvConfig
    paramsList: List[ParamItem]
    targetsList: Optional[List[Dict[str, Any]]] = []  #允许接收任意结构的动态目标列表
    algo: AlgoConfig

    # 允许额外字段，防止前端传了意外参数导致报错
    model_config = {
        "extra": "ignore"
    }