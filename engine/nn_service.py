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
    """终极进化版：JSON 确立配置主权，TorchScript 免解耦加载"""

    # 按照规范，寻找“三剑客”文件
    model_path = os.path.join("models", f"{req.model_name}_traced.pt")
    meta_path = os.path.join("models", f"{req.model_name}_meta.pth")
    json_path = os.path.join("models", f"{req.model_name}.json")  # ✨ 新增 JSON 路径查找

    # 兼容根目录直接测试的情况
    if not os.path.exists(model_path):
        model_path = f"{req.model_name}_traced.pt"
        meta_path = f"{req.model_name}_meta.pth"
        json_path = f"{req.model_name}.json"

    # 严格校验三文件必须同时存在
    if not os.path.exists(model_path) or not os.path.exists(meta_path) or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail=f"找不到配套的模型(.pt)、元数据(.pth)或配置文件(.json)！")

    try:
        # 0. 🌟 确立 JSON 主权：直接将 JSON 作为唯一配置源
        with open(json_path, 'r', encoding='utf-8') as f:
            model_config = json.load(f)

        # 1. 加载“环境工具箱”（仅用于读取安全的 scikit-learn Scaler 对象）
        meta_data = torch.load(meta_path, map_location='cpu', weights_only=False)

        # 2. 加载“黑盒模型”（彻底摆脱 class 类依赖）
        model = torch.jit.load(model_path, map_location='cpu')
        model.eval()  # 确保处于预测模式

        # 3. 极简挂载到全局状态
        NN_STATE["model"] = model
        NN_STATE["scaler_X"] = meta_data.get('scaler_X')
        NN_STATE["scaler_y"] = meta_data.get('pout_scaler', meta_data.get('scaler_y'))

        # ✨ 抛弃从 pth 读取配置，全部由 JSON 接管
        NN_STATE["model_type"] = model_config.get('meta', {}).get('topology', 'single_head')
        NN_STATE["input_dim"] = len(model_config.get('input_features', []))
        NN_STATE["outputs_config"] = model_config.get('outputs', [])  # 👈 确保多头配置被 100% 正确加载！

        return {
            "status": "success",
            "message": f"成功载入 {req.model_name} ({NN_STATE['input_dim']} 维)",
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

                # ========================================================
                # 🌟 第一步：动态解析多头模型输出，挂载到 head_cache
                # ========================================================
                outputs_cfg = NN_STATE.get("outputs_config", [])
                head_cache = {}
                logit_val = np.ones(pop_size)  # 默认都起振

                if isinstance(model_out, tuple):
                    if outputs_cfg:
                        for c_idx, cfg in enumerate(outputs_cfg):
                            name = cfg.get('name', f'Out_{c_idx}')
                            val_batch = model_out[cfg.get('model_index', c_idx)].numpy()

                            # 自动反归一化
                            if cfg.get('needs_inverse', False) and NN_STATE["scaler_y"] is not None:
                                val_batch = NN_STATE["scaler_y"].inverse_transform(val_batch)

                            if 'logit' in name.lower() or 'class' in name.lower():
                                logit_val = val_batch[:, 0]
                            else:
                                head_cache[name] = val_batch[:, 0]
                    else:
                        # 兜底：处理丢失了 outputs_cfg 的多头模型 (防崩兜底)
                        logit_val = model_out[0].numpy()[:, 0]
                        pout_scaled = model_out[1].numpy()
                        if NN_STATE["scaler_y"] is not None:
                            head_cache["Power"] = NN_STATE["scaler_y"].inverse_transform(pout_scaled)[:, 0]
                        else:
                            head_cache["Power"] = pout_scaled[:, 0]

                        if len(model_out) > 2:
                            head_cache["Frequency"] = model_out[2].numpy()[:, 0]
                else:
                    # 兼容真正的单头老模型 (此时 model_out 才是真正的单 Tensor)
                    raw_pred = NN_STATE["scaler_y"].inverse_transform(model_out.numpy())
                    head_cache["Efficiency"] = np.clip(raw_pred[:, 0], 0, 1) * 100

                # ========================================================
                # 🌟 第二步：离线打分 (The Dreamer) -> 彻底剥离物理硬编码
                # ========================================================
                fitness_score = np.zeros(pop_size)

                for t_name, pred_vals in head_cache.items():
                    w = weights.get(t_name, 0) / 100.0
                    if 'freq' in t_name.lower():
                        # 频率：靶点逼近惩罚 (平滑的绝对误差)
                        fitness_score -= np.abs(pred_vals - target_freq) * (1e8 * w)
                    else:
                        # 功率/效率：线性奖励
                        fitness_score += pred_vals * w

                # 断崖死区：物理不上电(未起振)直接枪毙
                fitness_score[logit_val < 0] = -1e12
                FitnV = ea.ranking(np.array([fitness_score]).T * -1.0)

                # ========================================================
                # 🌟 第三步：在线物理验证与网络微调 (The Reality Check)
                # ========================================================
                if is_online:
                    top_k_indices = np.argsort(fitness_score)[-k_samples:]
                    await websocket.send_json({
                        "type": "info",
                        "message": f"🔍 Gen {gen + 1}: 将 Top-{k_samples} 优胜个体送入 CST 真实物理引擎校验..."
                    })

                    from engine.cst_wrapper import run_single_simulation
                    from engine.evaluator import calc_score

                    targets_list = online_cfg.get("targetsList", [])

                    real_X = []
                    real_Y_all = []  # ✨ 存储包含所有头的复合向量，替代原先单一的 real_Y_power

                    for idx in top_k_indices:
                        p_dict = {param_names[j]: float(pop[idx][j]) for j in range(len(param_names))}
                        env_cfg = {"useStableTime": True, "stableTime": 20.0}

                        # 发送给 CST 物理层提取
                        m = await loop.run_in_executor(
                            CST_EXECUTOR,
                            run_single_simulation, project, p_dict, targets_list, env_cfg, cst_path
                        )

                        # 如果没有报错，且频率不是默认的失败值
                        is_freq_failed = any(
                            t.get('extractMethod') == 'freq_peak' and m.get(t['name'], 0) == -1
                            for t in targets_list
                        )

                        # 只要 CST 没报系统级 error，且频域提取没彻底失败，就交给打分器
                        if 'error' not in m and not is_freq_failed:
                            # 1. 使用严格网关算出物理真机得分
                            real_score = calc_score(m, targets_list, algo_type="SAEA-GA")
                            fitness_score[idx] = real_score  # 修正基因池得分

                            # 2. ✨ 构建与 outputs_cfg 严格对齐的多头靶向特征向量
                            real_y_vec = []
                            for c_idx, cfg in enumerate(outputs_cfg):
                                name = cfg.get('name')
                                if 'logit' in name.lower() or 'class' in name.lower():
                                    real_y_vec.append(1.0)  # 起振标志位
                                else:
                                    real_y_vec.append(m.get(name, 0.0))  # 读取 CST 中真实的 功率/频率等

                            # 加入微调训练集
                            real_X.append(pop[idx].tolist())
                            real_Y_all.append(real_y_vec)

                            # 为了让 Vue 界面能及时把真实值画在图上，反写回 head_cache 缓存
                            for k, v in m.items():
                                if k in head_cache:
                                    head_cache[k][idx] = v

                            await websocket.send_json({
                                "type": "info",
                                "message": f"   -> 校验成功: 预测分修正为 {real_score:.2f} (真实指标已提取)"
                            })
                        else:
                            fitness_score[idx] = -1e12
                            await websocket.send_json({
                                "type": "info",
                                "message": f"   -> 校验失败: 未起振或提取异常"
                            })

                    # ✨✨ 执行神经网络全头微调 ✨✨
                    if is_online and len(real_X) > 0:
                        total_online_collected_X.extend(real_X)
                        batch_X = list(real_X)
                        batch_Y = list(real_Y_all)

                        # 经验回放 (抽历史池)
                        sample_size = min(len(history_X), len(real_X) * 5)
                        if sample_size > 0:
                            import random
                            indices = random.sample(range(len(history_X)), sample_size)
                            batch_X.extend([history_X[i] for i in indices])
                            # 如果 history 存的不是向量而是旧标量，需额外处理，建议未来存向量
                            batch_Y.extend([history_Y_power[i] if isinstance(history_Y_power[0], list) else [1.0,
                                                                                                             history_Y_power[
                                                                                                                 i],
                                                                                                             4.8] for i
                                            in indices])

                        X_tensor = torch.FloatTensor(NN_STATE["scaler_X"].transform(batch_X))

                        # 缩放真实 Y 目标
                        Y_arr = np.array(batch_Y)
                        if NN_STATE["scaler_y"] is not None:
                            Y_scaled = NN_STATE["scaler_y"].transform(Y_arr)
                        else:
                            Y_scaled = Y_arr
                        Y_tensor = torch.FloatTensor(Y_scaled)

                        model.train()
                        for epoch in range(3):
                            optimizer.zero_grad()
                            preds = model(X_tensor)

                            # 累加所有回归头的 MSE 误差
                            loss = 0
                            for c_idx, cfg in enumerate(outputs_cfg):
                                pred_tensor = preds[cfg.get('model_index', c_idx)].squeeze()
                                target_tensor = Y_tensor[:, c_idx]
                                loss += criterion(pred_tensor, target_tensor)

                            loss.backward()
                            optimizer.step()

                        model.eval()
                        await websocket.send_json({
                            "type": "info",
                            "message": f"🧠 代理模型自适应微调完成 (全局 Loss: {loss.item():.4f})"
                        })

            # ========================================================
            # 🌟 第四步：图表数据下发整理 -> 彻底消除硬编码
            # ========================================================
            best_idx_gen = np.argmax(fitness_score)
            if fitness_score[best_idx_gen] > global_best_score:
                global_best_score = float(fitness_score[best_idx_gen])
                global_best_metrics = {
                    "params": {param_names[j]: float(pop[best_idx_gen][j]) for j in range(len(param_names))}
                }
                # 动态填充最优指标值
                for k, v_arr in head_cache.items():
                    # Vue 界面的发光指标卡片依赖 eff, power, freq 等小写命名
                    if 'eff' in k.lower(): global_best_metrics['eff'] = float(v_arr[best_idx_gen])
                    if 'power' in k.lower(): global_best_metrics['power'] = float(v_arr[best_idx_gen])
                    if 'freq' in k.lower(): global_best_metrics['freq'] = float(v_arr[best_idx_gen])

            parallel_data, pareto_data = [], []
            opt_names_list = list(head_cache.keys())

            # 匹配 Vue 平行坐标系期待的排列顺序 [..., Secondary, Primary]
            primary_name = opt_names_list[0] if len(opt_names_list) > 0 else None
            secondary_name = opt_names_list[1] if len(opt_names_list) > 1 else primary_name

            for i in range(pop_size):
                # 1. 散点数据
                pareto_dict = {"Gen": gen + 1}
                for k, v_arr in head_cache.items():
                    pareto_dict[k] = float(v_arr[i])
                pareto_data.append(pareto_dict)

                # 2. 平行坐标数据
                display_params = [float(val) for val in pop[i]]
                if primary_name:
                    p1 = float(head_cache[primary_name][i])
                    p2 = float(head_cache[secondary_name][i])
                    display_params.extend([p2, p1])
                parallel_data.append(display_params)

            # 3. 箱线图数据
            boxplot_dict = {}
            for k, v_arr in head_cache.items():
                sorted_arr = np.sort(v_arr)
                boxplot_dict[k] = [
                    float(sorted_arr[0]), float(np.percentile(sorted_arr, 25)),
                    float(np.median(sorted_arr)), float(np.percentile(sorted_arr, 75)), float(sorted_arr[-1])
                ]

                # 4. 计算优胜个体的参数相关性热力图 (Pearson Correlation)
            heatmap_data = []
            if pop.shape[0] > 1:
                # np.corrcoef 期望每一行代表一个变量，所以需要对 pop 进行转置 (pop.T)
                corr_matrix = np.corrcoef(pop.T)
                n_p = pop.shape[1]
                for r_idx in range(n_p):
                    for c_idx in range(n_p):
                        val = corr_matrix[r_idx, c_idx]
                        if np.isnan(val): val = 0.0  # 防止某个参数这一代完全没变化导致方差为0除以0 (NaN)
                        heatmap_data.append([r_idx, c_idx, round(float(val), 2)])

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