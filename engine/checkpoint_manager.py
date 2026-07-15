"""
Checkpoint Manager — 优化断点续跑核心模块

设计原则：
  - 所有运行时状态序列化为 JSON，存入 saea_data.db 的 checkpoints 表
  - SQLite WAL 模式保证原子写入，崩溃不丢数据
  - 统一接口：save / load / delete，三个算法引擎和在线学习共用
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import numpy as np
from database import SessionLocal, Checkpoint

logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """扩展 JSON 编码器，处理 numpy 标量与数组"""

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def _serialize_cache(cache: dict) -> list:
    """
    将 global_simulation_cache 转为可 JSON 序列化的列表。
    cache 的 key 是 tuple (通通是 float)，JSON 不支持 tuple key，
    因此转为 [[key_list, value_dict], ...] 格式。
    """
    result = []
    for key, val in cache.items():
        if isinstance(key, tuple):
            result.append([list(key), val])
        else:
            result.append([key, val])
    return result


def _deserialize_cache(serialized: list) -> dict:
    """反向还原 cache：list → dict with tuple keys"""
    result = {}
    for item in serialized:
        key, val = item[0], item[1]
        if isinstance(key, list):
            result[tuple(key)] = val
        else:
            result[key] = val
    return result


# ---------------------------------------------------------------
# 公共接口
# ---------------------------------------------------------------

def save_checkpoint(
    task_id: str,
    algo_type: str,
    gen: int,
    chrom: np.ndarray,
    fitnv: Optional[np.ndarray],
    opt_names: list,
    cache: dict,
    extra: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    保存优化运行时状态快照。

    Args:
        task_id:    任务唯一 ID
        algo_type:  算法类型 (SAEA-GA / PSO / BO)
        gen:        当前代数
        chrom:      种群矩阵 (n_pop × n_params)
        fitnv:      适应度排名 (n_pop × 1)，可为 None
        opt_names:  优化变量名列表
        cache:      全局仿真缓存字典 {param_tuple: result_dict}
        extra:      预留字段，用于 PSO/BO 额外状态 (如 pso_V, bo_X_history)

    Returns:
        True 保存成功，False 失败
    """
    try:
        state = {
            "algo_type": algo_type,
            "gen": gen,
            "Chrom": chrom.tolist() if isinstance(chrom, np.ndarray) else chrom,
            "FitnV": fitnv.tolist() if fitnv is not None else [],
            "opt_names": opt_names,
            "cache": _serialize_cache(cache),
        }
        if extra:
            state.update(extra)

        db = SessionLocal()
        try:
            existing = db.query(Checkpoint).filter(Checkpoint.task_id == task_id).first()
            if existing:
                existing.algo_type = algo_type
                existing.gen = gen
                existing.state_json = state
                existing.updated_at = datetime.now()
            else:
                db.add(Checkpoint(
                    task_id=task_id,
                    algo_type=algo_type,
                    gen=gen,
                    state_json=state,
                ))
            db.commit()
            logger.debug(f"[{task_id}] ✓ Checkpoint 已保存: gen={gen}, algo={algo_type}")
            return True
        except Exception as db_e:
            db.rollback()
            logger.error(f"[{task_id}] Checkpoint 写入 DB 失败: {db_e}")
            return False
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[{task_id}] Checkpoint 序列化失败: {e}")
        return False


def load_checkpoint(task_id: str) -> Optional[Dict[str, Any]]:
    """
    加载已保存的运行时状态快照。

    Returns:
        state_dict 或 None（无 checkpoint）
        state_dict 内 numpy 数组已还原为 np.ndarray
    """
    try:
        db = SessionLocal()
        try:
            row = db.query(Checkpoint).filter(Checkpoint.task_id == task_id).first()
            if not row:
                return None

            state = row.state_json

            # 还原 numpy 数组
            state["Chrom"] = np.array(state["Chrom"], dtype=np.float64)
            fitnv_raw = state.get("FitnV", [])
            state["FitnV"] = np.array(fitnv_raw, dtype=np.float64) if fitnv_raw else None

            # 还原仿真缓存
            state["cache"] = _deserialize_cache(state.get("cache", []))

            logger.info(f"[{task_id}] ✓ Checkpoint 已加载: gen={state['gen']}, algo={state['algo_type']}")
            return state
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[{task_id}] Checkpoint 读取失败: {e}")
        return None


def delete_checkpoint(task_id: str):
    """优化完成或主动终止后清理 checkpoint"""
    try:
        db = SessionLocal()
        try:
            db.query(Checkpoint).filter(Checkpoint.task_id == task_id).delete()
            db.commit()
            logger.debug(f"[{task_id}] Checkpoint 已清理")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"[{task_id}] Checkpoint 清理失败: {e}")
