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
             task_status_flags, algo_type="SAEA-GA"):
    """
    评估当前种群中所有个体 (增加了单步实时推送)
    ✨ 已完美对接三大算法的独立打分体系
    """
    n = Phen.shape[0]
    Fit = np.zeros((n, 1))
    current_batch_logs = []
    waves_dict = {}

    for i in range(n):
        if task_status_flags.get(task_id) == "stopped":
            print(f"[{task_id}] 🛑 收到急停指令，终止当前代剩余个体的计算")
            # ✨ 修复：绝不能用 break，必须抛出异常直接跳出 Geatpy 的 C++ 核心循环
            raise InterruptedError("User stopped the task manually.")
        try:
            print(f"  -> 正在计算 Gen {gen_idx} | 个体 {i + 1}/{n} ...")

            p = {**{k: float(v) for k, v in zip(opt_names, Phen[i, :])}, **fixed_dict}
            m = run_single_simulation(project, p, targets_cfg, env_cfg, cst_path)

            # ✨ 核心联动：将前端传来的算法类型，喂给底层打分网关
            scr = calc_score(m, targets_cfg, algo_type)
            Fit[i, 0] = scr

            rec = {
                "No": i + 1, "Score": float(scr), "Power": float(m.get('power_val', 0) / 1e6),
                "Eff": round(float(m.get('eff_val', 0)), 2), "Freq": round(float(m.get('freq', 0)), 3),
                "SideRatio": m.get('side_ratio', None), "params": p
            }
            current_batch_logs.append(rec)

            wave_data = {
                "power": m.get('power_curve'), "eff": m.get('eff_curve'),
                "fft": m.get('fft_curve'), "mainMode": m.get('main_mode_curve'),
                "timeX": (m.get('power_curve') or {}).get('x', []),
                "powerData": (m.get('power_curve') or {}).get('y', []),
                "effData": [val * 100 for val in (m.get('eff_curve') or {}).get('y', [])] if m.get('eff_curve') else [],
                "params": p
            }
            waves_dict[str(i + 1)] = wave_data

            db = SessionLocal()
            try:
                is_valid = float(scr) > -1e6
                new_individual = Individual(
                    task_id=task_id,
                    gen_index=gen_idx,
                    ind_index=i + 1,
                    params_json=p,
                    score=float(scr),
                    power_val=float(m.get('power_val', 0)),
                    eff_val=float(m.get('eff_val', 0)),
                    freq_val=float(m.get('freq', 0)),
                    side_ratio=float(m.get('side_ratio')) if m.get('side_ratio') is not None else None,
                    is_valid=is_valid
                )
                db.add(new_individual)
                db.flush()

                new_wave = Waveform(
                    individual_id=new_individual.id,
                    task_id=task_id,
                    gen_index=gen_idx,
                    ind_index=i + 1,
                    power_wave=wave_data.get('power'),
                    eff_wave=wave_data.get('eff'),
                    fft_wave=wave_data.get('fft'),
                    main_mode_wave=wave_data.get('mainMode')
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
                "score": float(scr), "power": rec["Power"], "eff": rec["Eff"],
                "wave_data": wave_data
            }
            asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(ind_msg), task_id), loop)

        except Exception as e:
            print(f"❌ 个体 {i + 1} 评估崩溃: {e}")
            Fit[i, 0] = -50000.0 if algo_type == "BO" else -1e7
            fallback_params = {**dict(zip(opt_names, Phen[i, :])), **fixed_dict}
            current_batch_logs.append({
                "No": i + 1, "Score": Fit[i, 0], "Power": 0.0, "Eff": 0.0, "Freq": 0.0,
                "SideRatio": None, "params": fallback_params
            })
            waves_dict[str(i + 1)] = {
                "power": None, "eff": None, "fft": None, "mainMode": None,
                "timeX": [], "powerData": [], "effData": [], "params": fallback_params
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
        targets_cfg = config_dict['targets']
        env_cfg = config_dict['env']

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
            # BO 我们直接把先验数据喂给代理模型，GA/PSO 放进初始化矩阵
            try:
                inject_dict = json.loads(inject_json_str)
                injection_vec = []
                for i, name in enumerate(opt_names):
                    injection_vec.append(float(inject_dict.get(name, (opt_bounds[i][0] + opt_bounds[i][1]) / 2.0)))
                print(f"[{task_id}] 💉 准备注入先验参数组合")
            except Exception as e:
                print(f"[{task_id}] ⚠️ 基因注入解析失败: {e}")

        # === 3. 初始化各算法的独立大脑 ===
        # [GA 初始化]
        FieldD = ea.crtfld('RI', np.zeros(len(opt_names)), ranges, np.ones((2, len(opt_names))))
        Chrom, FitnV = None, None

        # [PSO 初始化]
        pso_cfg = algo_cfg.get('pso', {})
        p_w, p_c1, p_c2 = pso_cfg.get('w', 0.8), pso_cfg.get('c1', 1.5), pso_cfg.get('c2', 1.5)
        pso_V, pbest_X, pbest_Fit, gbest_X, gbest_Fit = None, None, None, None, -np.inf

        # [BO 初始化]
        bo_opt = None
        bo_X_history = []  # ✨ 增加：记录所有跑过的参数
        bo_Y_history = []  # ✨ 增加：记录所有跑过的分数
        current_bo_acq = 'LCB'
        if algo_type == 'BO':
            try:
                from skopt import Optimizer
                from skopt.space import Real
                bo_cfg = algo_cfg.get('bo', {})
                use_auto_acq = bo_cfg.get('useAutoAcq', False) # ✨ 获取前端自适应开关

                # 如果开启自适应，第一阶段强制用 LCB 拓荒；否则尊重用户手选
                acq_func = 'LCB' if use_auto_acq else bo_cfg.get('acqFunc', 'EI')
                kappa, xi = bo_cfg.get('kappa', 2.5), bo_cfg.get('xi', 0.01)
                current_bo_acq = acq_func # 记录当前真实在用的策略

                # 建立贝叶斯的物理边界空间
                bo_space = [Real(b[0], b[1], name=name) for name, b, in zip(opt_names, opt_bounds)]
                bo_opt = Optimizer(bo_space, base_estimator="GP", acq_func=acq_func,
                                   acq_func_kwargs={"kappa": kappa, "xi": xi})

                # 如果有注入基因，在 BO 启动前直接塞进它的记忆里
                if injection_vec is not None:
                    asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(
                        json.dumps({"type": "info", "message": "🧠 贝叶斯代理模型正在吸收先验经验..."}), task_id), loop)
            except ImportError:
                err_msg = json.dumps(
                    {"type": "error", "message": "❌ 缺失 scikit-optimize 库。请在后端运行: pip install scikit-optimize"})
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(err_msg, task_id), loop)
                return

        # ========================================================
        # 🌟 4. 进化/迭代 主循环 (策略模式)
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
                # ----------------------------------------------------
                # 阶段 1：算法吐出下一次需要验证的矩阵 (Chrom)
                # ----------------------------------------------------
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
                        Chrom = np.clip(Chrom, ranges[0], ranges[1])  # 强制拉回物理边界

                elif algo_type == 'BO':
                    use_auto_acq = algo_cfg.get('bo', {}).get('useAutoAcq', False)

                    # ✨✨ 自适应策略核心逻辑 (仅在前端开启时触发) ✨✨
                    if use_auto_acq:
                        progress_ratio = gen / n_gen
                        target_acq = 'LCB' if progress_ratio <= 0.5 else 'EI'

                        # 触发策略切换（在 50% 进度时发生）
                        if target_acq != current_bo_acq:
                            print(f"[{task_id}] 🧠 BO 策略自适应切换: 测绘完成，从 {current_bo_acq} 切换为 {target_acq} 极限收敛！")
                            bo_cfg = algo_cfg.get('bo', {})
                            kappa, xi = bo_cfg.get('kappa', 2.5), bo_cfg.get('xi', 0.01)

                            # ✨ 修复：同时传入 kappa 和 xi，防止底层报错
                            bo_opt = Optimizer(bo_space, base_estimator="GP", acq_func=target_acq, acq_func_kwargs={"kappa": kappa, "xi": xi})

                            # 瞬间灌入前半生的所有记忆
                            if len(bo_X_history) > 0:
                                bo_opt.tell(bo_X_history, bo_Y_history)
                            current_bo_acq = target_acq

                    # 正常要数据
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
                        Chrom = np.vstack([Chrom[best_idx, :], Sel])  # 精英保留
                        if Chrom.shape[0] > n_pop:
                            Chrom = Chrom[np.random.choice(Chrom.shape[0], n_pop, replace=False), :]

                # ----------------------------------------------------
                # 阶段 2：去 CST 跑出真实物理数据并打分 (统一网关)
                # ----------------------------------------------------
                Fit, batch_logs, waves_dict = eval_pop(Chrom, gen, opt_names, fixed_dict, project, targets_cfg, env_cfg,
                                                       cst_path, ws_manager, task_id, loop, task_status_flags,
                                                       algo_type)

                if task_status_flags.get(task_id) == "stopped":
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 任务已成功终止！"}), task_id),
                        loop)
                    break

                # ----------------------------------------------------
                # 阶段 3：算法吞下评估结果，进化记忆
                # ----------------------------------------------------
                if algo_type == 'PSO':
                    mask = Fit > pbest_Fit
                    pbest_X[mask.flatten()] = Chrom[mask.flatten()]
                    pbest_Fit[mask] = Fit[mask]
                    max_idx = np.argmax(pbest_Fit)
                    if pbest_Fit[max_idx, 0] > gbest_Fit:
                        gbest_Fit = pbest_Fit[max_idx, 0]
                        gbest_X = pbest_X[max_idx, :].copy()


                elif algo_type == 'BO':
                    # 吞下分数并学习
                    bo_opt.tell(bo_batch, (-Fit).flatten().tolist())
                    # ✨ 记录到历史库中，为可能的策略切换做准备
                    bo_X_history.extend(bo_batch)
                    bo_Y_history.extend((-Fit).flatten().tolist())

                else:  # SAEA-GA
                    FitnV = ea.ranking(Fit * -1)

                # ----------------------------------------------------
                # 阶段 4：结果入库与前端渲染推送 (基建共享)
                # ----------------------------------------------------
                best_idx = np.argmax(Fit)
                best_ind = batch_logs[best_idx]

                db = SessionLocal()
                try:
                    new_gen = Generation(
                        task_id=task_id, gen_index=gen, best_score=float(best_ind['Score']),
                        best_eff=float(best_ind['Eff']), best_power=float(best_ind['Power'] * 1e6),
                        best_freq=float(best_ind['Freq'])
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

                progress_data = {
                    "type": "progress", "gen": gen, "total_gen": n_gen,
                    "best_eff": best_ind["Eff"], "best_power": best_ind["Power"], "best_freq": best_ind["Freq"],
                    "message": f"第 {gen} 批次计算完成！{algo_type} 本轮最高得分: {best_ind['Score']:.2e}",
                    "batch_logs": batch_logs, "waves_dict": waves_dict
                }
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(progress_data), task_id), loop)

            finally:
                project.close()

        # 全部完成收尾工作
        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "completed"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "completed"
        asyncio.run_coroutine_threadsafe(
            ws_manager.send_to_task(json.dumps({"type": "finish", "message": "✅ CST 联合优化全部完成！"}), task_id),
            loop)


    except InterruptedError:
        # ✨ 新增：拦截手动强退异常，标记状态为 stopped 而不是 error
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
        cst_env.close()