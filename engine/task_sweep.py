import asyncio
import json
import itertools
import numpy as np
from database import SessionLocal, Task, Individual, Waveform
from .cst_wrapper import run_single_simulation


def run_sweep_task(task_id: str, config_dict: dict, ws_manager, loop: asyncio.AbstractEventLoop, task_status_flags: dict):
    print(f"[{task_id}] 🚀 网格扫参引擎已启动...")

    import cst.interface
    cst_env = None
    try:
        cst_env = cst.interface.DesignEnvironment()
    except Exception as e:
        err_msg = json.dumps({"type": "error", "message": f"❌ CST 启动失败: {e}"})
        asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(err_msg, task_id), loop)
        return

    try:
        cst_path = config_dict['cstPath']
        # 1. 动态获取目标列表 (TargetsList)
        targets_list = config_dict.get('targetsList', [])
        env_cfg = config_dict.get('env', {'useStableTime': True, 'stableTime': 20.0})
        params_list = config_dict['paramsList']

        sweep_vars = []
        fixed_params = {}
        for p in params_list:
            if p.get('isSweep'):
                sweep_vars.append(p)
            else:
                fixed_params[p['name']] = p['val']

        var_names = []
        var_spaces = []
        for v in sweep_vars:
            var_names.append(v['name'])
            pts = int(v.get('points', 1))
            if pts > 1:
                space = np.linspace(v['min'], v['max'], pts).tolist()
            else:
                space = [v['min']]
            var_spaces.append(space)

        all_combinations = list(itertools.product(*var_spaces))
        total_steps = len(all_combinations)

        print(f"[{task_id}] 📊 计划进行 {total_steps} 次网格扫描...")

        project = cst_env.open_project(cst_path)

        try:
            for idx, combo in enumerate(all_combinations):
                current_step = idx + 1

                if task_status_flags.get(task_id) == "stopped":
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 扫参任务已被强制终止！"}), task_id), loop)
                    break

                print(f"  -> 正在求解 ID: {current_step}/{total_steps} ...")
                current_params = fixed_params.copy()
                current_params.update(dict(zip(var_names, combo)))

                # 2. 扔给动态 CST Wrapper 提取数据
                m = run_single_simulation(project, current_params, targets_list, env_cfg, cst_path)

                # 3. 全自动数据分流：标量入 metrics，波形入 waves
                metrics_json = {}
                waves_json = {}
                for k, v in m.items():
                    if k == 'error': continue
                    if k.endswith('_curve'):
                        waves_json[k.replace('_curve', '')] = v
                    else:
                        metrics_json[k] = float(v)

                # 组装返回给前端的数据结构
                result_data = {
                    "params": current_params,
                    "metrics": metrics_json,
                    "waves": waves_json,
                    "is_valid": 'error' not in m
                }

                # 4. 极简落库：直接把字典存入 SQLite
                db = SessionLocal()
                try:
                    new_individual = Individual(
                        task_id=task_id, gen_index=1, ind_index=current_step,
                        params_json=current_params, score=0.0,
                        metrics_json=metrics_json,
                        is_valid='error' not in m
                    )
                    db.add(new_individual)
                    db.flush()

                    new_wave = Waveform(
                        individual_id=new_individual.id, task_id=task_id, gen_index=1, ind_index=current_step,
                        waves_json=waves_json
                    )
                    db.add(new_wave)
                    db.commit()
                except Exception as db_e:
                    print(f"[{task_id}] ⚠️ 组合 {current_step} 写入数据库失败: {db_e}")
                    db.rollback()
                finally:
                    db.close()

                # --- WebSocket 推送给前端 ---
                payload = {"type": "sweep_progress", "current": current_step, "total": total_steps, "data": result_data}
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(payload), task_id), loop)

        finally:
            project.close()

        # 5. 收尾逻辑保持不变 ...
        db = SessionLocal()
        final_status = "stopped" if task_status_flags.get(task_id) == "stopped" else "completed"
        db.query(Task).filter(Task.id == task_id).update({"status": final_status})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = final_status

        if final_status == "completed":
            asyncio.run_coroutine_threadsafe(
                ws_manager.send_to_task(json.dumps({"type": "finish", "message": "✅ 网格扫参圆满完成！"}), task_id), loop)
        else:
            asyncio.run_coroutine_threadsafe(
                ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 扫参任务已中断"}), task_id), loop)

    except Exception as e:
        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "error"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "error"
        err_msg = f"引擎异常中断: {str(e)}"
        print(f"[{task_id}] ❌ {err_msg}")
        asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps({"type": "error", "message": err_msg}), task_id), loop)
    finally:
        if cst_env: cst_env.close()