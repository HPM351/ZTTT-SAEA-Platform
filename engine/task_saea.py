import asyncio
import json
import numpy as np
import geatpy as ea
from database import SessionLocal, Task, Generation, Individual, Waveform
from datetime import datetime
# 导入底层驱动和打分系统
from .cst_wrapper import run_single_simulation
from .evaluator import calc_score


def eval_pop(Phen, gen_idx, opt_names, fixed_dict, project, targets_cfg, env_cfg, cst_path, ws_manager, task_id, loop,
             task_status_flags, algo_type="SAEA-GA", global_cache=None):
    """
    评估当前种群中所有个体 (增加了单步实时推送)
    去物理化版本：全量字典动态路由，不再做任何硬编码转换
    """
    if global_cache is None:
        global_cache = {}

    n = Phen.shape[0]
    Fit = np.zeros((n, 1))
    current_batch_logs = []
    waves_dict = {}

    for i in range(n):
        if task_status_flags.get(task_id) == "stopped":
            print(f"[{task_id}] 🛑 收到急停指令，终止当前代剩余个体的计算")
            raise InterruptedError("User stopped the task manually.")
        try:
            p = {**{k: float(v) for k, v in zip(opt_names, Phen[i, :])}, **fixed_dict}

            # ==========================================
            # 算力白嫖：参数哈希与缓存拦截
            # ==========================================
            param_key = tuple(round(p[k], 5) for k in sorted(p.keys()))

            if param_key in global_cache:
                print(f"  -> Gen {gen_idx} | 个体 {i + 1}/{n} 🎯 命中缓存！直接读取历史数据，跳过 CST...")
                m = global_cache[param_key]
            else:
                print(f"  -> Gen {gen_idx} | 个体 {i + 1}/{n} ⚙️ 启动 CST 求解...")
                m = run_single_simulation(project, p, targets_cfg, env_cfg, cst_path)
                if 'error' not in m:
                    global_cache[param_key] = m

            # 核心联动：将前端传来的算法类型，喂给底层打分网关
            scr = calc_score(m, targets_cfg, algo_type)
            Fit[i, 0] = scr

            # =======================================================
            # 去物理化：数据智能分流
            # 将字典中的标量 (数值) 与矢量 (曲线) 自动剥离
            # =======================================================
            current_metrics = {k: v for k, v in m.items() if not k.endswith('_curve') and k != 'error'}
            current_waves = {k: v for k, v in m.items() if k.endswith('_curve')}

            rec = {
                "No": i + 1,
                "Score": float(scr),
                "metrics": current_metrics,
                "params": p
            }
            current_batch_logs.append(rec)

            waves_dict[str(i + 1)] = {
                **current_waves,
                "params": p
            }

            db = SessionLocal()
            try:
                is_valid = float(scr) > -1e6
                new_individual = Individual(
                    task_id=task_id,
                    gen_index=gen_idx,
                    ind_index=i + 1,
                    params_json=p,
                    score=float(scr),
                    metrics_json=current_metrics,
                    is_valid=is_valid
                )
                db.add(new_individual)
                db.flush()

                new_wave = Waveform(
                    individual_id=new_individual.id,
                    task_id=task_id,
                    gen_index=gen_idx,
                    ind_index=i + 1,
                    waves_json=current_waves
                )
                db.add(new_wave)
                db.commit()
            except Exception as db_e:
                print(f"[{task_id}] ⚠️ 个体 {i + 1} 写入数据库失败: {db_e}")
                db.rollback()
            finally:
                db.close()

            ind_msg = {
                "type": "individual_progress",
                "gen": gen_idx, "ind": i + 1, "total_ind": n,
                "score": float(scr),
                "metrics": current_metrics,
                "wave_data": waves_dict[str(i + 1)]
            }
            asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(ind_msg), task_id), loop)

        except Exception as e:
            print(f"❌ 个体 {i + 1} 评估崩溃: {e}")
            Fit[i, 0] = -50000.0 if algo_type == "BO" else -1e7
            fallback_params = {**dict(zip(opt_names, Phen[i, :])), **fixed_dict}
            current_batch_logs.append({
                "No": i + 1, "Score": Fit[i, 0], "metrics": {}, "params": fallback_params
            })
            waves_dict[str(i + 1)] = {
                "params": fallback_params
            }

    return Fit, current_batch_logs, waves_dict


def run_optimization_task(task_id: str, config_dict: dict, ws_manager, loop: asyncio.AbstractEventLoop,
                          task_status_flags: dict):
    """
    后台任务的主控枢纽：完美融合 SAEA-GA, PSO, BO 三大引擎
    """
    print(f"[{task_id}] 🚀 多擎联合仿真核心已启动...")

    import cst.interface
    cst_env = None

    try:
        cst_env = cst.interface.DesignEnvironment()
    except Exception as e:
        err_msg = json.dumps({"type": "error", "message": f"❌ CST 启动失败: {e}"})
        asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(err_msg, task_id), loop)
        return

    try:
        # === 1. 解析前端全量配置 ===
        cst_path = config_dict['cstPath']
        algo_cfg = config_dict['algo']

        targets_cfg = config_dict.get('targetsList', [])
        env_cfg = config_dict.get('env', {})

        algo_type = algo_cfg.get('type', 'SAEA-GA')
        n_pop = algo_cfg['nPop']
        n_gen = algo_cfg['nGen']

        opt_names, opt_bounds = [], []
        fixed_dict = {}
        for item in config_dict['paramsList']:
            if item['opt']:
                opt_names.append(item['name'])
                opt_bounds.append([item['min'], item['max']])
            else:
                fixed_dict[item['name']] = item['val']

        ranges = np.array(opt_bounds).T

        # === 2. 提取并准备“基因注入 (先验知识)” ===
        inject_json_str = algo_cfg.get('injectJson', '')
        injection_vec = None
        if inject_json_str and inject_json_str.strip() and algo_type != 'BO':
            try:
                inject_dict = json.loads(inject_json_str)
                injection_vec = []
                for i, name in enumerate(opt_names):
                    injection_vec.append(float(inject_dict.get(name, (opt_bounds[i][0] + opt_bounds[i][1]) / 2.0)))
                print(f"[{task_id}] 💉 准备注入先验参数组合")
            except Exception as e:
                print(f"[{task_id}] ⚠️ 基因注入解析失败: {e}")

        global_simulation_cache = {}
        print(f"[{task_id}] 全局仿真记忆字典已挂载")

        # === 3. 初始化各算法的独立大脑 ===
        FieldD = ea.crtfld('RI', np.zeros(len(opt_names)), ranges, np.ones((2, len(opt_names))))
        Chrom, FitnV = None, None

        pso_cfg = algo_cfg.get('pso', {})
        p_w, p_c1, p_c2 = pso_cfg.get('w', 0.8), pso_cfg.get('c1', 1.5), pso_cfg.get('c2', 1.5)
        pso_V, pbest_X, pbest_Fit, gbest_X, gbest_Fit = None, None, None, None, -np.inf

        bo_opt = None
        bo_X_history = []
        bo_Y_history = []
        current_bo_acq = 'LCB'
        if algo_type == 'BO':
            try:
                from skopt import Optimizer
                from skopt.space import Real
                bo_cfg = algo_cfg.get('bo', {})
                use_auto_acq = bo_cfg.get('useAutoAcq', False)

                acq_func = 'LCB' if use_auto_acq else bo_cfg.get('acqFunc', 'EI')
                kappa, xi = bo_cfg.get('kappa', 2.5), bo_cfg.get('xi', 0.01)
                current_bo_acq = acq_func

                bo_space = [Real(b[0], b[1], name=name) for name, b, in zip(opt_names, opt_bounds)]
                bo_opt = Optimizer(bo_space, base_estimator="GP", acq_func=acq_func,
                                   acq_func_kwargs={"kappa": kappa, "xi": xi})

                if injection_vec is not None:
                    asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(
                        json.dumps({"type": "info", "message": "🧠 贝叶斯代理模型正在吸收先验经验..."}), task_id), loop)
            except ImportError:
                err_msg = json.dumps(
                    {"type": "error", "message": "❌ 缺失 scikit-optimize 库。请在后端运行: pip install scikit-optimize"})
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(err_msg, task_id), loop)
                return

        # ========================================================
        # 4. 进化/迭代 主循环 (策略模式)
        # ========================================================
        for gen in range(1, n_gen + 1):
            if task_status_flags.get(task_id) == "stopped":
                asyncio.run_coroutine_threadsafe(
                    ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 任务已被强制终止！"}), task_id),
                    loop)
                break

            print(f"\n--- 🧬 开始第 {gen} 代 / 批次 | 引擎: {algo_type} ---")
            project = cst_env.open_project(cst_path)

            try:
                if algo_type == 'PSO':
                    if gen == 1:
                        Chrom = np.random.uniform(ranges[0], ranges[1], (n_pop, len(opt_names)))
                        if injection_vec is not None: Chrom[0, :] = injection_vec
                        pso_V = np.zeros_like(Chrom)
                        pbest_X = np.copy(Chrom)
                        pbest_Fit = np.full((n_pop, 1), -np.inf)
                    else:
                        r1, r2 = np.random.rand(n_pop, 1), np.random.rand(n_pop, 1)
                        pso_V = p_w * pso_V + p_c1 * r1 * (pbest_X - Chrom) + p_c2 * r2 * (gbest_X - Chrom)
                        Chrom = Chrom + pso_V
                        Chrom = np.clip(Chrom, ranges[0], ranges[1])

                elif algo_type == 'BO':
                    use_auto_acq = algo_cfg.get('bo', {}).get('useAutoAcq', False)
                    if use_auto_acq:
                        progress_ratio = gen / n_gen
                        target_acq = 'LCB' if progress_ratio <= 0.5 else 'EI'

                        if target_acq != current_bo_acq:
                            print(
                                f"[{task_id}] 🧠 BO 策略自适应切换: 测绘完成，从 {current_bo_acq} 切换为 {target_acq} 极限收敛！")
                            bo_cfg = algo_cfg.get('bo', {})
                            kappa, xi = bo_cfg.get('kappa', 2.5), bo_cfg.get('xi', 0.01)
                            bo_opt = Optimizer(bo_space, base_estimator="GP", acq_func=target_acq,
                                               acq_func_kwargs={"kappa": kappa, "xi": xi})

                            if len(bo_X_history) > 0:
                                bo_opt.tell(bo_X_history, bo_Y_history)
                            current_bo_acq = target_acq

                    if gen == 1 and injection_vec is not None:
                        bo_batch = bo_opt.ask(n_points=n_pop - 1)
                        bo_batch.insert(0, injection_vec)
                    else:
                        bo_batch = bo_opt.ask(n_points=n_pop)
                    Chrom = np.array(bo_batch)

                else:  # SAEA-GA
                    if gen == 1:
                        Chrom = ea.crtpc('RI', n_pop, FieldD)
                        if injection_vec is not None: Chrom[0, :] = injection_vec
                    else:
                        rec_code, pc, mut_code, pm = algo_cfg['ga']['recCode'], algo_cfg['ga']['pc'], algo_cfg['ga'][
                            'mutCode'], algo_cfg['ga']['pm']
                        use_auto_mut = algo_cfg['ga'].get('useAutoMut', False)
                        if use_auto_mut:
                            r_low, r_high = algo_cfg['ga']['autoMutRange'][0] / 100.0, algo_cfg['ga']['autoMutRange'][
                                1] / 100.0
                            mut_code = 'mutuni' if gen / n_gen <= r_low else (
                                'mutgau' if gen / n_gen <= r_high else 'mutbga')

                        Sel = Chrom[ea.selecting('rws', FitnV, n_pop - 1), :]
                        Sel = ea.mutate(mut_code, 'RI', ea.recombin(rec_code, Sel, pc), FieldD, pm)
                        best_idx = np.argmax(FitnV)
                        Chrom = np.vstack([Chrom[best_idx, :], Sel])
                        if Chrom.shape[0] > n_pop:
                            Chrom = Chrom[np.random.choice(Chrom.shape[0], n_pop, replace=False), :]

                Fit, batch_logs, waves_dict = eval_pop(Chrom, gen, opt_names, fixed_dict, project, targets_cfg, env_cfg,
                                                       cst_path, ws_manager, task_id, loop, task_status_flags,
                                                       algo_type, global_simulation_cache)

                if task_status_flags.get(task_id) == "stopped":
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 任务已成功终止！"}), task_id),
                        loop)
                    break

                if algo_type == 'PSO':
                    mask = Fit > pbest_Fit
                    pbest_X[mask.flatten()] = Chrom[mask.flatten()]
                    pbest_Fit[mask] = Fit[mask]
                    max_idx = np.argmax(pbest_Fit)
                    if pbest_Fit[max_idx, 0] > gbest_Fit:
                        gbest_Fit = pbest_Fit[max_idx, 0]
                        gbest_X = pbest_X[max_idx, :].copy()

                elif algo_type == 'BO':
                    bo_opt.tell(bo_batch, (-Fit).flatten().tolist())
                    bo_X_history.extend(bo_batch)
                    bo_Y_history.extend((-Fit).flatten().tolist())

                else:  # SAEA-GA
                    FitnV = ea.ranking(Fit * -1)

                best_idx = np.argmax(Fit)
                best_ind = batch_logs[best_idx]

                db = SessionLocal()
                try:
                    new_gen = Generation(
                        task_id=task_id,
                        gen_index=gen,
                        best_score=float(best_ind['Score']),
                        best_metrics_json=best_ind['metrics']
                    )
                    if gen == 1:
                        db.query(Task).filter(Task.id == task_id).update(
                            {"name": config_dict.get('taskName', 'Unnamed_Task')})
                    db.add(new_gen)
                    db.commit()
                except Exception as db_e:
                    db.rollback()
                finally:
                    db.close()

                telemetry_data = {}
                try:
                    if algo_type == 'SAEA-GA':
                        # GA遥测：种群多样性(基因标准差) 与 当前变异策略
                        diversity = np.mean(np.std(Chrom, axis=0))
                        current_pm = algo_cfg['ga']['pm']
                        if algo_cfg['ga'].get('useAutoMut', False):
                            r_low = algo_cfg['ga']['autoMutRange'][0] / 100.0
                            r_high = algo_cfg['ga']['autoMutRange'][1] / 100.0
                            if gen / n_gen <= r_low:
                                current_pm = f"探索期(均匀变异)"
                            elif gen / n_gen <= r_high:
                                current_pm = f"收敛期(高斯变异)"
                            else:
                                current_pm = f"微调期(布列德变异)"
                        telemetry_data = {
                            "种群多样性 (Diversity)": f"{diversity:.4f}",
                            "当前变异状态": str(current_pm)
                        }

                    elif algo_type == 'PSO':
                        # PSO遥测：粒子群平均飞行速度 与 全局极值
                        avg_vel = np.mean(np.abs(pso_V)) if pso_V is not None else 0.0
                        telemetry_data = {
                            "群平均速度 (Velocity)": f"{avg_vel:.4f}",
                            "当前全局极值 (gBest)": f"{gbest_Fit:.2f}" if gbest_Fit != -np.inf else "N/A"
                        }

                    elif algo_type == 'BO':
                        # BO遥测：当前采集函数 与 代理模型对新样本的预测不确定度(方差)
                        model_uncertainty = "评估中..."
                        if bo_opt and len(bo_opt.models) > 0:
                            try:
                                # 让高斯过程模型输出刚刚预测的这一批点的标准差(不确定度)
                                _, std = bo_opt.models[-1].predict(bo_opt.space.transform(bo_batch), return_std=True)
                                model_uncertainty = f"{np.mean(std):.4f}"
                            except:
                                pass
                        telemetry_data = {
                            "当前采集策略 (Acq)": current_bo_acq,
                            "模型不确定度 (Std)": model_uncertainty
                        }
                except Exception as tele_e:
                    print(f"[{task_id}] ⚠️ 遥测数据提取失败: {tele_e}")

                progress_data = {
                    "type": "progress", "gen": gen, "total_gen": n_gen,
                    "best_metrics": best_ind['metrics'],
                    "message": f"第 {gen} 批次计算完成！{algo_type} 本轮最高得分: {best_ind['Score']:.2e}",
                    "batch_logs": batch_logs, "waves_dict": waves_dict,
                    "telemetry": telemetry_data
                }
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(progress_data), task_id), loop)

            finally:
                project.close()

        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "completed"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "completed"
        asyncio.run_coroutine_threadsafe(
            ws_manager.send_to_task(json.dumps({"type": "finish", "message": "✅ CST 联合优化全部完成！"}), task_id),
            loop)

    except InterruptedError:
        print(f"[{task_id}] 任务已安全手动终止。")
        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "stopped"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "stopped"
        asyncio.run_coroutine_threadsafe(
            ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 任务已被手动终止"}), task_id),
            loop)

    except Exception as e:
        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "error"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "error"
        asyncio.run_coroutine_threadsafe(
            ws_manager.send_to_task(json.dumps({"type": "error", "message": f"引擎异常中断: {str(e)}"}), task_id), loop)
    finally:
        if cst_env:
            cst_env.close()