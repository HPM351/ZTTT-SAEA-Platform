import os
import json
import torch
import numpy as np
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, List
import geatpy as ea
import asyncio
import shap # [新增] SHAP 可解释性库
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import traceback

# ==========================================
# 1. 全局状态与 Pydantic 数据模型
# ==========================================
nn_router = APIRouter(prefix="/api/nn", tags=["Neural Network"])

NN_STATE = {
    "model": None, "scaler_X": None, "scaler_y": None,
    "model_type": "single_head", "input_dim": 4,
    "outputs_config": []  # ✨ 新增：用于在内存中缓存当前模型的输出头规则
}

CST_EXECUTOR = ThreadPoolExecutor(max_workers=1)
class LoadModelRequest(BaseModel):
    model_name: str


class PredictRequest(BaseModel):
    features: List[float]
    target_index: int = -1


class ScanRequest(BaseModel):
    scan_x: str
    scan_y: str
    base_params: Dict[str, float]
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    grid_size: int = 30

    target_index: int = 0  # 目标在 PyTorch 输出张量中的索引
    target_name: str = ""  # 目标名称 (如 "Power")
    needs_inverse: bool = False  # 是否需要用 scaler_y 进行反归一化


# ==========================================
# 2. API 接口实现
# ==========================================
@nn_router.get("/models_list")
async def get_models_list():
    """
    动态扫描 models/ 目录下的所有 JSON 配置文件，
    为前端提供可用的模型清单和界面渲染元数据。
    """
    models_dir = "models"
    available_models = []

    # 如果目录不存在，返回空列表防崩
    if not os.path.exists(models_dir):
        return {"status": "success", "models": []}

    # 遍历并解析所有 .json 文件
    for filename in os.listdir(models_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(models_dir, filename)
            try:
                # 必须指定 utf-8，否则 Windows 环境下读取中文容易乱码
                with open(filepath, 'r', encoding='utf-8') as f:
                    model_config = json.load(f)
                    available_models.append(model_config)
            except json.JSONDecodeError:
                print(f"⚠️ 警告: 无法解析 JSON 文件 {filename}，请检查语法格式。")
            except Exception as e:
                print(f"⚠️ 警告: 读取 {filename} 时发生未知错误 - {str(e)}")

    return {
        "status": "success",
        "count": len(available_models),
        "models": available_models
    }

@nn_router.post("/load")
async def load_model(req: LoadModelRequest):
    """终极进化版：基于 TorchScript 的免解耦加载"""

    # 按照我们的新规范，约定模型和元数据的文件名
    model_path = os.path.join("models", f"{req.model_name}_traced.pt")
    meta_path = os.path.join("models", f"{req.model_name}_meta.pth")

    # 兼容根目录直接测试的情况
    if not os.path.exists(model_path):
        model_path = f"{req.model_name}_traced.pt"
        meta_path = f"{req.model_name}_meta.pth"

    if not os.path.exists(model_path) or not os.path.exists(meta_path):
        raise HTTPException(status_code=404, detail=f"找不到配套的模型或元数据文件，请确认是否已完成 TorchScript 转换！")

    try:
        # 1. 瞬间加载“环境工具箱”（允许读取安全的 scikit-learn 对象）
        meta_data = torch.load(meta_path, map_location='cpu', weights_only=False)

        # 2. 瞬间加载“黑盒模型”（彻底摆脱 class 类依赖）
        model = torch.jit.load(model_path, map_location='cpu')
        model.eval()  # 确保处于预测模式

        # 3. 极简挂载到全局状态
        NN_STATE["model"] = model
        NN_STATE["scaler_X"] = meta_data['scaler_X']
        NN_STATE["scaler_y"] = meta_data.get('pout_scaler', meta_data.get('scaler_y'))
        NN_STATE["model_type"] = meta_data.get('model_type', 'single_head')
        NN_STATE["input_dim"] = meta_data['input_size']
        NN_STATE["outputs_config"] = meta_data.get('outputs', [])

        return {
            "status": "success",
            "message": f"成功载入 {NN_STATE['model_type']} 架构 ({NN_STATE['input_dim']} 维)",
            "input_dim": NN_STATE['input_dim']
        }

    except Exception as e:
        traceback.print_exc()  # 在控制台打印完整报错
        raise HTTPException(status_code=500, detail=f"模型智能装载失败: {str(e)}")


@nn_router.post("/predict")
async def predict_single(data: PredictRequest):
    """多维正向推演 (完全动态版)"""
    if NN_STATE["model"] is None: raise HTTPException(status_code=400, detail="请先加载模型")

    try:
        input_arr = np.array([data.features])
        input_scaled = NN_STATE["scaler_X"].transform(input_arr)
        input_tensor = torch.FloatTensor(input_scaled)

        with torch.no_grad():
            model_out = NN_STATE["model"](input_tensor)

            if isinstance(model_out, tuple):
                raw_predictions = []
                outputs_cfg = NN_STATE.get("outputs_config", [])

                if not outputs_cfg:
                    # 兼容旧版本硬编码（防崩兜底，万一你加载了没写配置的老模型）
                    cls_val = float(model_out[0].numpy()[0][0])
                    pout_scaled = model_out[1].numpy()
                    pout_real = float(NN_STATE["scaler_y"].inverse_transform(pout_scaled)[0][0]) if NN_STATE[
                        "scaler_y"] else float(pout_scaled[0][0])
                    freq_real = float(model_out[2].numpy()[0][0])
                    raw_predictions = [cls_val, pout_real, freq_real]
                else:
                    # ✨ 全新动态解析逻辑：遍历模型所有的输出头
                    for i, out_tensor in enumerate(model_out):
                        val_scaled = out_tensor.numpy()
                        # 查找当前 tensor 对应的配置字典 (通过 index 对齐)
                        cfg = next((c for c in outputs_cfg if c.get('model_index', c.get('index', i)) == i), {})

                        # 如果配置中明确要求 needs_inverse，才进行反归一化
                        if cfg.get('needs_inverse', False) and NN_STATE["scaler_y"] is not None:
                            val_real = NN_STATE["scaler_y"].inverse_transform(val_scaled)[0][0]
                        else:
                            val_real = val_scaled[0][0]

                        # 保证严格按元组原始顺序塞入列表返回给前端
                        raw_predictions.append(float(val_real))
            else:
                # 兼容旧的单头模型
                pred_scaled = model_out.numpy()
                raw_pred = NN_STATE["scaler_y"].inverse_transform(pred_scaled)[0]
                raw_predictions = [float(x) for x in raw_pred]

            input_tensor_grad = torch.FloatTensor(input_scaled)
            input_tensor_grad.requires_grad = True

            with torch.enable_grad():
                grad_out = NN_STATE["model"](input_tensor_grad)

                # ✨ 核心修复 1：动态识别求导目标
                target_idx = 0
                if isinstance(grad_out, tuple):
                    if data.target_index >= 0:
                        target_idx = data.target_index
                    else:
                        # 兜底：如果没有指定，自动寻找第一个非分类头
                        for c_idx, cfg in enumerate(NN_STATE.get("outputs_config", [])):
                            name = cfg.get('name', '').lower()
                            if 'logit' not in name and 'class' not in name:
                                target_idx = cfg.get('model_index', c_idx)
                                break
                    target_obj = grad_out[target_idx].sum()
                else:
                    target_obj = grad_out.sum()

                target_obj.backward()

                # ✨ 核心修复 2：放弃乘以 input_scaled，避开归零陷阱！
                # 直接使用归一化空间的梯度，它完美代表了当前状态下参数的推移敏感度
                grads = input_tensor_grad.grad[0].numpy()

                # ✨ 将“按最大值固定放缩到20”改为“按绝对值总和计算相对贡献百分比 (%)”
                sum_abs_grads = np.sum(np.abs(grads)) + 1e-6

                # 这样所有参数的柱子绝对值加起来刚好是 100%，更加直观合理
                local_shap = [round(float(v / sum_abs_grads * 100.0), 2) for v in grads]

            return {
                "status": "success",
                "raw_predictions": raw_predictions,
                "local_shap": local_shap  # 👈 新增：返回局部参数推移数组
            }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"预测计算出错: {str(e)}")


@nn_router.post("/scan3d")
async def generate_3d_scan(data: ScanRequest):
    """自适应 3D 地形矩阵生成"""
    if NN_STATE["model"] is None: raise HTTPException(status_code=400, detail="请先加载模型")

    try:
        param_map = list(data.base_params.keys())
        x_idx = param_map.index(data.scan_x)
        y_idx = param_map.index(data.scan_y)

        base_vector = [data.base_params[p] for p in param_map]

        x_linspace = np.linspace(data.x_min, data.x_max, data.grid_size)
        y_linspace = np.linspace(data.y_min, data.y_max, data.grid_size)
        X_grid, Y_grid = np.meshgrid(x_linspace, y_linspace)
        X_flat, Y_grid_flat = X_grid.ravel(), Y_grid.ravel()

        batch_input = np.tile(base_vector, (len(X_flat), 1))
        batch_input[:, x_idx] = X_flat
        batch_input[:, y_idx] = Y_grid_flat

        batch_scaled = NN_STATE["scaler_X"].transform(batch_input)
        with torch.no_grad():
            model_out = NN_STATE["model"](torch.FloatTensor(batch_scaled))

            if isinstance(model_out, tuple):
                # 动态提取用户选定的目标通道
                idx = data.target_index
                val_scaled = model_out[idx].numpy()

                # 动态判断：如果该指标(如功率)是被归一化过的，则执行还原
                if data.needs_inverse and NN_STATE["scaler_y"] is not None:
                    z_values = NN_STATE["scaler_y"].inverse_transform(val_scaled).ravel()
                else:
                    z_values = val_scaled.ravel()
            else:
                # 兼容旧单头模型
                pred_batch_scaled = model_out.numpy()
                z_values = NN_STATE["scaler_y"].inverse_transform(pred_batch_scaled)[:, 0]

            # 智能兼容：如果是效率，自动转百分比格式
            if data.target_name.lower() == 'efficiency' and np.max(z_values) <= 1.05:
                z_values = z_values * 100

        surface_data = [[float(X_flat[i]), float(Y_grid_flat[i]), float(z_values[i])] for i in range(len(X_flat))]
        return {"status": "success", "surface_data": surface_data}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"矩阵计算失败: {str(e)}")


def calc_simple_online_fitness(metrics: dict, weights: dict, target_freq: float) -> float:
    """
    在线微调专用的极简适应度计算：
    功率、效率直接按比例加分；频率按偏差扣分。不设死区，保证梯度平滑。
    """
    score = 0.0

    # 1. 功率加分 (假设 metrics 里的 power_val 是瓦，转为 MW)
    if 'power_val' in metrics:
        p_mw = metrics['power_val'] / 1e6
        score += p_mw * (weights.get('Power', 0) / 100.0)

    # 2. 效率加分 (%)
    if 'eff_val' in metrics:
        score += metrics['eff_val'] * (weights.get('Efficiency', 0) / 100.0)

    # 3. 频率逼近扣分 (用一个放大系数让频率惩罚足够痛)
    if 'freq' in metrics and metrics['freq'] > 0:
        freq_diff = abs(metrics['freq'] - target_freq)
        # 偏差 0.1GHz 可能扣 100 分 (具体系数可调)
        score -= freq_diff * 1000.0 * (weights.get('Frequency', 0) / 100.0)

    return score


@nn_router.websocket("/ws/evolve")
async def nn_evolve_ws(websocket: WebSocket):
    """完全动态降维遗传算法核心 - 引入自适应变异与在线验证"""
    await websocket.accept()
    try:
        config = json.loads(await websocket.receive_text())

        # 1. 提取基础遗传参数
        bounds = config.get("bounds", [])
        pop_size = config.get("pop_size", 100)
        n_gen = config.get("n_gen", 50)
        pc, pm = config.get("pc", 0.7), config.get("pm", 0.2)
        target_freq = config.get("target_freq", 6.0)
        weights = config.get("weights", {})

        # ✨ 修复核心：补上自适应变异的参数提取，否则下方循环会报 NameError 崩溃！
        use_adaptive_mut = config.get("use_adaptive_mut", False)
        mut_phases = config.get("mut_phases", [0.3, 0.7])

        # 提取参数名映射，用于发给 CST
        param_names = config.get("param_names", [])

        # 🌟 2. 提取在线学习配置
        online_cfg = config.get("online", {})
        is_online = online_cfg.get("enable", False)
        k_samples = online_cfg.get("kSamples", 5)  # 默认 Top-5
        cst_path = online_cfg.get("cstPath", "")
        eff_path = online_cfg.get("effPath", "")

        cst_env = None
        project = None

        # 🌟 3. 如果开启了在线微调，提前拉起 CST 引擎并发送通知
        if is_online:
            if not os.path.exists(cst_path):
                await websocket.send_json({"error": "在线验证失败: CST 项目路径不存在！"})
                return

            await websocket.send_json({"type": "info", "message": "⚙️ 正在后台唤醒 CST 引擎，请稍候..."})
            import cst.interface
            loop = asyncio.get_running_loop()  # ✨ 获取当前事件循环

            # ✨ 改用 loop.run_in_executor 强绑定到单线程池
            cst_env = await loop.run_in_executor(CST_EXECUTOR, cst.interface.DesignEnvironment)
            project = await loop.run_in_executor(CST_EXECUTOR, cst_env.open_project, cst_path)
            await websocket.send_json({"type": "info", "message": "✅ CST 引擎连接成功，准备开始在线联合演化！"})

        n_params = len(bounds)
        lows, highs = np.array([b[0] for b in bounds]), np.array([b[1] for b in bounds])
        FieldD = ea.crtfld('RI', np.zeros(n_params), np.vstack([lows, highs]), np.ones((2, n_params)))
        pop = ea.crtpc('RI', pop_size, FieldD)
        FitnV, best_global_eff = None, 0.0

        # ✨ 新增：用于严谨追踪全局最高综合得分个体的各项指标
        global_best_score = -1e15
        global_best_metrics = {"power": None, "eff": None, "freq": None, "params": None}

        optimizer = None
        criterion = None
        history_X = []
        history_Y_power = []

        if is_online and NN_STATE["model"] is not None:
            import torch.optim as optim
            import torch.nn as nn
            import random
            import time

            model = NN_STATE["model"]

            # 1. 强制解锁 TorchScript 模型的梯度（默认是冻结的）
            for param in model.parameters():
                param.requires_grad = True

            # 2. 定义微调优化器（学习率 1e-4，微调不能步子太大）
            optimizer = optim.Adam(model.parameters(), lr=1e-4)
            criterion = nn.MSELoss()

            # 3. 读取历史训练集 (Experience Replay Buffer)
            # ⚠️ 假设你把训练集存成了 models/dataset.json，格式为 {"X": [[...], ...], "Y_power": [850, 920, ...]}
            dataset_path = "models/dataset.json"
            try:
                if os.path.exists(dataset_path):
                    with open(dataset_path, 'r', encoding='utf-8') as f:
                        hist_data = json.load(f)
                        history_X = hist_data.get('X', [])
                        history_Y_power = hist_data.get('Y_power', [])

                    await websocket.send_json({
                        "type": "info",
                        "message": f"📦 成功读取 {len(history_X)} 条历史数据进入防遗忘记忆池"
                    })
                else:
                    await websocket.send_json(
                        {"type": "info", "message": "⚠️ 未找到历史数据集，本次微调将仅依赖新探索数据"})
            except Exception as e:
                await websocket.send_json({"type": "info", "message": f"⚠️ 历史数据解析失败: {e}"})

        # 记录整个在线学习过程中收集到的所有真实真机数据
        total_online_collected_X = []

        for gen in range(n_gen):

            # 🌟 核心引擎：自适应变异策略动态调度
            current_pm = pm
            mut_oper = 'mutuni'  # 默认均匀变异

            if use_adaptive_mut:
                progress = gen / n_gen
                if progress < mut_phases[0]:
                    # 阶段1：探索期。使用均匀变异，稍微放大变异率
                    mut_oper = 'mutuni'
                    current_pm = min(1.0, pm * 1.2)
                elif progress < mut_phases[1]:
                    # 阶段2：收敛期。切换为高斯/布列德变异(mutbga)，聚焦局部
                    mut_oper = 'mutbga'
                    current_pm = pm
                else:
                    # 阶段3：微调期。保持布列德变异，但大幅降低变异率，保护精英解
                    mut_oper = 'mutbga'
                    current_pm = pm * 0.3

            if gen > 0 and FitnV is not None:
                SelCh = pop[ea.selecting('rws', FitnV, pop_size - 1), :]
                # 🌟 应用动态的 变异算子(mut_oper) 和 变异率(current_pm)
                SelCh = ea.mutate(mut_oper, 'RI', ea.recombin('xovdp', SelCh, pc), FieldD, current_pm)
                BestInd = pop[np.argmax(FitnV), :]
                pop = np.vstack([BestInd, SelCh])
                for k in range(n_params): pop[:, k] = np.clip(pop[:, k], lows[k], highs[k])

            if len(pop.shape) == 1:
                pop = pop.reshape(1, -1)

                # 如果 Geatpy 意外导致列数不匹配，强制用上一代的最优解补齐 (极小概率发生，但必须防备)
            if pop.shape[1] != n_params:
                print(f"⚠️ 警告: Geatpy 维度异常 {pop.shape}，已强制修复")
                pop = np.tile(BestInd, (pop_size, 1))

            pop_scaled = NN_STATE["scaler_X"].transform(pop)
            with torch.no_grad():
                model_out = NN_STATE["model"](torch.FloatTensor(pop_scaled))

                if isinstance(model_out, tuple):
                    outputs_cfg = NN_STATE.get("outputs_config", [])

                    # 默认创建全 0 数组占位
                    logit_val = np.ones(pop_size)  # 默认都起振
                    power_real = np.zeros(pop_size)
                    freq_real = np.zeros(pop_size)

                    if not outputs_cfg:
                        # --- 兼容旧模型硬编码 ---
                        logit_val = model_out[0].numpy()[:, 0]
                        pout_scaled = model_out[1].numpy()
                        power_real = NN_STATE["scaler_y"].inverse_transform(pout_scaled)[:, 0] if NN_STATE[
                                                                                                      "scaler_y"] is not None else \
                        pout_scaled[:, 0]
                        freq_real = model_out[2].numpy()[:, 0]
                    else:
                        # --- 🌟 动态解析多头模型 ---
                        for i, out_tensor in enumerate(model_out):
                            val_batch = out_tensor.numpy()
                            cfg = next((c for c in outputs_cfg if c.get('model_index', c.get('index', i)) == i), {})
                            name = cfg.get('name', '').lower()

                            # 判断是否反归一化
                            if cfg.get('needs_inverse', False) and NN_STATE["scaler_y"] is not None:
                                val_batch = NN_STATE["scaler_y"].inverse_transform(val_batch)

                            # ✨ 智能分发：无论模型的头什么顺序，只要名字对了就能装进正确的数组
                            if 'logit' in name or 'class' in name:
                                logit_val = val_batch[:, 0]
                            elif 'power' in name:
                                power_real = val_batch[:, 0]
                            elif 'freq' in name:
                                freq_real = val_batch[:, 0]
                            # 如果未来有 efficiency，可以直接加 elif 'eff' in name: eff_real = val_batch[:, 0]

                    # -------- 下面的算分逻辑保持原样不用动 --------
                    w_power = weights.get("Power", 50) / 100.0
                    w_freq = weights.get("Frequency", 50) / 100.0

                    freq_penalty = np.abs(freq_real - target_freq) * (1e8 * w_freq)
                    fitness_score = (power_real * w_power) - freq_penalty
                    fitness_score[logit_val < 0] = -1e12

                    FitnV = ea.ranking(np.array([fitness_score]).T * -1.0)
                    effs_percent = power_real
                    powers = freq_real

                    if is_online:
                        # 1. 挑出 NN 预测得分最高的 K 个体索引
                        top_k_indices = np.argsort(fitness_score)[-k_samples:]

                        await websocket.send_json({
                            "type": "info",
                            "message": f"🔍 Gen {gen + 1}: 正在将预测出的 Top-{k_samples} 送入 CST 进行真机物理校验..."
                        })

                        from engine.cst_wrapper import run_single_simulation

                        # 🌟 修复：对接前端透传过来的全量动态结果路径
                        cst_targets = {}
                        if weights.get("Power", 0) > 0:
                            cst_targets["power"] = {"enable": True,
                                                    "path": online_cfg.get("powerPath", r"Tables\1D Results\AVGpower")}
                        if weights.get("Efficiency", 0) > 0 and eff_path:
                            cst_targets["eff"] = {"enable": True, "path": eff_path}
                        if weights.get("Frequency", 0) > 0:
                            cst_targets["freq"] = {"enable": True,
                                                   "path": online_cfg.get("freqPath", r"Tables\1D Results\FFT"),
                                                   "target": target_freq, "blindGap": 0.05}

                        # 🌟 修复：必须在循环前初始化收集列表
                        real_X = []
                        real_Y_power = []

                        for idx in top_k_indices:
                            # 组装这组个体的真实物理参数
                            p_dict = {param_names[j]: float(pop[idx][j]) for j in range(len(param_names))}
                            env_cfg = {"stableTime": 20.0}

                            # 异步执行 CST
                            m = await loop.run_in_executor(
                                CST_EXECUTOR,
                                run_single_simulation, project, p_dict, cst_targets, env_cfg, cst_path
                            )

                            if 'error' not in m and m.get('freq', -1) > 0:
                                real_score = calc_simple_online_fitness(m, weights, target_freq)
                                fitness_score[idx] = real_score

                                # 提取真实的 MW 功率
                                p_mw = m.get('power_val', 0) / 1e6

                                if 'power_val' in m: power_real[idx] = p_mw
                                if 'eff_val' in m: effs_percent[idx] = m['eff_val']
                                if 'freq' in m: freq_real[idx] = m['freq']

                                # 🌟 修复：成功跑出结果后，必须把这组数据加入微调池！
                                real_X.append(pop[idx].tolist())
                                real_Y_power.append(p_mw)

                                await websocket.send_json({
                                    "type": "info",
                                    "message": f"   -> 校验完成: 预测分 {fitness_score[idx]:.2f} 修正为真实分 {real_score:.2f}"
                                })
                            else:
                                fitness_score[idx] = -1e12
                                await websocket.send_json({
                                    "type": "info",
                                    "message": f"   -> 校验失败: 该参数组合物理上无法起振，已淘汰"
                                })

                        if is_online and len(real_X) > 0:
                            total_online_collected_X.extend(real_X)  # 记录总共收集了多少新数据

                            # 1. 组装本批次的训练数据 (Batch)
                            batch_X = list(real_X)
                            batch_Y = list(real_Y_power)  # 这里的 power 是 CST 跑出来的真实 MW 值

                            # 2. 核心：从历史记忆池中随机抽取旧数据 (比例 1 : 5)
                            sample_size = min(len(history_X), len(real_X) * 5)
                            if sample_size > 0:
                                # 随机抽样索引
                                indices = random.sample(range(len(history_X)), sample_size)
                                batch_X.extend([history_X[i] for i in indices])
                                batch_Y.extend([history_Y_power[i] for i in indices])

                            # 3. 数据预处理 (归一化转 Tensor)
                            X_tensor = torch.FloatTensor(NN_STATE["scaler_X"].transform(batch_X))

                            # Y 需要归一化后才能算 Loss
                            Y_arr = np.array(batch_Y).reshape(-1, 1)
                            if NN_STATE["scaler_y"] is not None:
                                Y_scaled = NN_STATE["scaler_y"].transform(Y_arr).flatten()
                            else:
                                Y_scaled = Y_arr.flatten()
                            Y_tensor = torch.FloatTensor(Y_scaled)

                            # 4. 执行微调 (让模型反复吃透这批混合数据 3 个 Epoch)
                            model.train()  # 必须切到训练模式
                            for epoch in range(3):
                                optimizer.zero_grad()
                                preds = model(X_tensor)

                                # 兼容多头/单头模型结构
                                if isinstance(preds, tuple):
                                    # [1] 是功率头。squeeze() 确保维度对齐
                                    loss = criterion(preds[1].squeeze(), Y_tensor)
                                else:
                                    loss = criterion(preds.squeeze(), Y_tensor)

                                loss.backward()
                                optimizer.step()

                            model.eval()  # ⚠️ 极度重要：微调完必须切回推理模式，否则下一代预测就乱了！

                            await websocket.send_json({
                                "type": "info",
                                "message": f"🧠 代理模型微调完成 (混合样本: {len(real_X)}新 + {sample_size}旧, Loss: {loss.item():.4f})"
                            })
                    # 🌟🌟🌟 在线验证逻辑结束 🌟🌟🌟

                    if w_freq > 0.01:
                        valid_idx = np.where((logit_val > 0) & (np.abs(freq_real - target_freq) <= 0.2))[0]
                    else:
                        valid_idx = np.where(logit_val > 0)[0]

                    if len(valid_idx) > 0:
                        best_global_eff = max(best_global_eff, np.max(power_real[valid_idx]))
                else:
                    # --- 单头模型逻辑 ---
                    raw_pred = NN_STATE["scaler_y"].inverse_transform(model_out.numpy())
                    effs_percent = np.clip(raw_pred[:, 0], 0, 1) * 100
                    powers = raw_pred[:, 1] if raw_pred.shape[1] > 1 else [None] * pop_size
                    fitness_score = effs_percent  # ✨ 补齐适应度数组
                    FitnV = ea.ranking(np.array([effs_percent]).T * -1.0)
                    best_global_eff = max(best_global_eff, np.max(effs_percent))

            best_idx_gen = np.argmax(fitness_score)
            if fitness_score[best_idx_gen] > global_best_score:
                global_best_score = float(fitness_score[best_idx_gen])

                current_best_eff = None
                current_best_power = None
                current_best_freq = None

                # 智能识别当前输出的通道，提取数据
                if isinstance(model_out, tuple):
                    current_best_power = float(power_real[best_idx_gen])
                    current_best_freq = float(freq_real[best_idx_gen])
                else:
                    current_best_eff = float(effs_percent[best_idx_gen])
                    if raw_pred.shape[1] > 1:
                        current_best_power = float(raw_pred[best_idx_gen, 1])

                global_best_metrics = {
                    "eff": current_best_eff,
                    "power": current_best_power,
                    "freq": current_best_freq,
                    "params": {param_names[j]: float(pop[best_idx_gen][j]) for j in range(len(param_names))}
                }

            head_cache = {}
            if isinstance(model_out, tuple) and NN_STATE.get("outputs_config"):
                outputs_cfg = NN_STATE.get("outputs_config", [])
                for c_idx, cfg in enumerate(outputs_cfg):
                    name = cfg.get('name')
                    # 跳过分类头 (起振判断不画入散点图)
                    if 'logit' in name.lower() or 'class' in name.lower():
                        continue

                    val_batch = model_out[cfg.get('model_index', c_idx)].numpy()
                    if cfg.get('needs_inverse', False) and NN_STATE["scaler_y"] is not None:
                        val_batch = NN_STATE["scaler_y"].inverse_transform(val_batch)

                    head_cache[name] = val_batch[:, 0]

            # ✨ 核心修复：如果 meta.pth 丢失了输出配置，强制执行精准的物理量挂载兜底，杜绝错位
            if not head_cache:
                if 'power_real' in locals(): head_cache["Power"] = power_real
                if 'freq_real' in locals(): head_cache["Frequency"] = freq_real
                if 'effs_percent' in locals(): head_cache["Efficiency"] = effs_percent

            parallel_data, pareto_data = [], []
            for i in range(pop_size):
                # 1. 动态构造 Pareto 字典对象
                pareto_dict = {"Gen": gen + 1}
                for k, v_arr in head_cache.items():
                    pareto_dict[k] = float(v_arr[i])
                pareto_data.append(pareto_dict)

                # 2. Parallel 数据 (保持原有兼容逻辑)
                eff = float(effs_percent[i])
                pwr = float(powers[i]) if powers[i] is not None else None
                display_params = [float(val) for val in pop[i]]
                display_params.extend([pwr, eff])
                parallel_data.append(display_params)

            boxplot_dict = {}
            if 'head_cache' in locals() and head_cache:
                for k, v_arr in head_cache.items():
                    sorted_arr = np.sort(v_arr)
                    boxplot_dict[k] = [
                        float(sorted_arr[0]), float(np.percentile(sorted_arr, 25)),
                        float(np.median(sorted_arr)), float(np.percentile(sorted_arr, 75)), float(sorted_arr[-1])
                    ]
            else:
                effs_sorted = np.sort(effs_percent)
                boxplot_dict["Efficiency"] = [
                    float(effs_sorted[0]), float(np.percentile(effs_sorted, 25)),
                    float(np.median(effs_sorted)), float(np.percentile(effs_sorted, 75)), float(effs_sorted[-1])
                ]

            # ==========================================
            # ✨ 新增：计算优胜个体的皮尔逊相关系数矩阵
            # ==========================================
            heatmap_data = []
            try:
                # 截取得分排名前 50% 的“优良基因”个体进行耦合分析
                elite_count = max(5, pop_size // 2)
                elite_idx = np.argsort(fitness_score)[-elite_count:]
                elite_pop = pop[elite_idx]  # 取出物理参数

                # ✨ 使用 errstate 忽略预期的除零警告 (当某参数完全收敛时方差为0)
                with np.errstate(divide='ignore', invalid='ignore'):
                    corr_matrix = np.corrcoef(elite_pop.T)
                    corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)

                    np.fill_diagonal(corr_matrix, 1.0)

                # 转换成 ECharts 热力图需要的 [x, y, value] 一维数组格式
                for i in range(n_params):
                    for j in range(n_params):
                        heatmap_data.append([i, j, round(float(corr_matrix[i, j]), 2)])
            except Exception as e:
                print(f"⚠️ 热力图矩阵计算失败: {e}")

            await websocket.send_json({
                "gen": gen + 1,
                "best_global_eff": float(best_global_eff),
                "best_global_metrics": global_best_metrics,
                "parallel_data": parallel_data,
                "pareto_data": pareto_data,
                "boxplot_data": boxplot_dict,
                "heatmap_data": heatmap_data  # 👈 新增：向前端推送热力图数据
            })
            await asyncio.sleep(0.15)

        if is_online and len(total_online_collected_X) > 0:
            timestamp = int(time.time())

            # 使用时间戳防覆盖，例如 models/Finetuned_1712300000.pt
            new_model_name = f"Finetuned_{timestamp}"
            save_path = os.path.join("models", f"{new_model_name}_traced.pt")

            try:
                model.eval()
                # TorchScript 需要一个 Dummy Input 来追踪网络结构
                dummy_input = torch.randn(1, n_params)
                traced_model = torch.jit.trace(model, dummy_input)
                torch.jit.save(traced_model, save_path)

                # 可选：如果想在界面上也能直接切到新模型，可以把原模型的 Meta 数据也复制一份
                # import shutil
                # old_meta = os.path.join("models", f"{config.get('model_name')}_meta.pth")
                # new_meta = os.path.join("models", f"{new_model_name}_meta.pth")
                # if os.path.exists(old_meta): shutil.copy(old_meta, new_meta)

                await websocket.send_json({
                    "type": "info",
                    "message": f"💾 在线学习圆满结束！共探索 {len(total_online_collected_X)} 个真机数据，新模型已保存为: {new_model_name}"
                })
            except Exception as e:
                await websocket.send_json({"type": "info", "message": f"⚠️ 新模型保存失败: {e}"})

        await websocket.send_json({"status": "complete"})
        await websocket.close()
    except Exception as e:
        traceback.print_exc()
        try:
            await websocket.close()
        except:
            pass


@nn_router.get("/global_importance")
async def get_global_importance():
    """✨ 使用 PyTorch Autograd 计算全局参数敏感度 (Global Sensitivity)"""
    if NN_STATE["model"] is None:
        raise HTTPException(status_code=400, detail="请先加载模型")

    try:
        model = NN_STATE["model"]
        dim = NN_STATE["input_dim"]

        # 1. 模拟一个覆盖全空间的大 Batch (如 500 个样本)
        # 假设输入已经被 MinMaxScaler 缩放到 [0, 1] 附近
        bg_tensor = torch.rand(500, dim, requires_grad=True)

        # 2. 前向传播
        model_out = model(bg_tensor)

        # 3. 聚合所有目标头的输出以计算总梯度
        if isinstance(model_out, tuple):
            loss = sum([out.sum() for out in model_out])
        else:
            loss = model_out.sum()

        # 4. 反向求导，提取输入层的平均绝对梯度
        loss.backward()
        avg_grads = bg_tensor.grad.abs().mean(dim=0).numpy()

        # 5. 归一化为百分比 (%)
        if avg_grads.sum() == 0:
            importance = np.ones(dim) / dim * 100
        else:
            importance = (avg_grads / avg_grads.sum()) * 100.0

        # 6. 从元数据中读取特征名称 (如果存了的话)，否则用 Dim 索引
        feature_names = [f"Param_{i + 1}" for i in range(dim)]

        return {
            "status": "success",
            "importance": [float(v) for v in importance]  # 直接返回数组即可
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"敏感度矩阵计算失败: {str(e)}")