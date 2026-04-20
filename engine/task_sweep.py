import asyncio
import json
import itertools
import numpy as np
from database import SessionLocal, Task, Individual, Waveform
from .cst_wrapper import run_single_simulation


def run_sweep_task(task_id: str, config_dict: dict, ws_manager, loop: asyncio.AbstractEventLoop,
                   task_status_flags: dict):
    """
    网格化扫参专属引擎：生成笛卡尔积 -> 驱动 CST -> 落库 -> 推送前端
    """
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
        targets_cfg = config_dict['targets']
        env_cfg = config_dict.get('env', {'stableTime': 20.0})  # 给个默认稳态时间
        params_list = config_dict['paramsList']

        # 1. 解析参数配置，分离【扫描变量】与【固定变量】
        sweep_vars = []
        fixed_params = {}
        for p in params_list:
            if p.get('isSweep'):
                sweep_vars.append(p)
            else:
                fixed_params[p['name']] = p['val']

        # 2. 构建多维扫描空间
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

        # 3. 生成笛卡尔积 (全网格组合)
        all_combinations = list(itertools.product(*var_spaces))
        total_steps = len(all_combinations)

        print(f"[{task_id}] 📊 计划进行 {total_steps} 次网格扫描...")

        project = cst_env.open_project(cst_path)

        try:
            # 4. 开启扫描主循环
            for idx, combo in enumerate(all_combinations):
                current_step = idx + 1

                # 检查是否被前端强制终止
                if task_status_flags.get(task_id) == "stopped":
                    asyncio.run_coroutine_threadsafe(
                        ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 扫参任务已被强制终止！"}),
                                                task_id), loop)
                    break

                print(f"  -> 正在求解 ID: {current_step}/{total_steps} ...")

                # 组装当前物理参数
                current_params = fixed_params.copy()
                current_params.update(dict(zip(var_names, combo)))

                # 🚀 调用 CST Wrapper 进行物理求解
                m = run_single_simulation(project, current_params, targets_cfg, env_cfg, cst_path)

                # 解析安全数据 (防御性兜底，防止前端 ECharts 报错)
                power_val = float(m.get('power_val', 0) / 1e6) if m.get('power_val') is not None else 0.0
                eff_val = float(m.get('eff_val', 0)) if m.get('eff_val') is not None else 0.0
                freq_val = float(m.get('freq', 0)) if m.get('freq') is not None else 0.0

                # 组装波形数据对象
                wave_data = {
                    "power": m.get('power_curve'),
                    "eff": m.get('eff_curve'),
                    "fft": m.get('fft_curve'),
                    "mainMode": m.get('main_mode_curve'),
                    "params": current_params
                }

                # 组装返回给前端的数据结构
                result_data = {
                    "power_val": power_val,
                    "eff_val": eff_val,
                    "freq": freq_val,
                    "params": current_params,
                    **wave_data
                }

                # --- 🗄️ 数据库落库逻辑 (复用现有的表结构) ---
                db = SessionLocal()
                try:
                    # 扫参为了兼容优化表结构，固定 Gen 为 1，Ind 为当前的 Sweep ID
                    new_individual = Individual(
                        task_id=task_id,
                        gen_index=1,
                        ind_index=current_step,
                        params_json=current_params,
                        score=0.0,  # 扫参没有分数
                        power_val=float(m.get('power_val', 0)),
                        eff_val=eff_val,
                        freq_val=freq_val,
                        side_ratio=float(m.get('side_ratio')) if m.get('side_ratio') is not None else None,
                        is_valid=True if 'error' not in m else False
                    )
                    db.add(new_individual)
                    db.flush()

                    new_wave = Waveform(
                        individual_id=new_individual.id,
                        task_id=task_id,
                        gen_index=1,
                        ind_index=current_step,
                        power_wave=wave_data.get('power'),
                        eff_wave=wave_data.get('eff'),
                        fft_wave=wave_data.get('fft'),
                        main_mode_wave=wave_data.get('mainMode')
                    )
                    db.add(new_wave)
                    db.commit()
                except Exception as db_e:
                    print(f"[{task_id}] ⚠️ 组合 {current_step} 写入数据库失败: {db_e}")
                    db.rollback()
                finally:
                    db.close()

                # --- 📡 WebSocket 推送给前端 ---
                payload = {
                    "type": "sweep_progress",
                    "current": current_step,
                    "total": total_steps,
                    "data": result_data
                }
                asyncio.run_coroutine_threadsafe(ws_manager.send_to_task(json.dumps(payload), task_id), loop)

        finally:
            project.close()

        # 5. 全部扫描完成收尾
        db = SessionLocal()
        # ✨ 根据真实 flag 动态决定落库状态是 stopped 还是 completed
        final_status = "stopped" if task_status_flags.get(task_id) == "stopped" else "completed"
        db.query(Task).filter(Task.id == task_id).update({"status": final_status})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = final_status

        # 根据状态推送不同的结束文案给前端
        if final_status == "completed":
            asyncio.run_coroutine_threadsafe(
                ws_manager.send_to_task(json.dumps({"type": "finish", "message": "✅ 网格扫参任务全部圆满完成！"}),
                                        task_id),
                loop)
        else:
            asyncio.run_coroutine_threadsafe(
                ws_manager.send_to_task(json.dumps({"type": "error", "message": "🛑 扫参任务已中断"}), task_id),
                loop)

    except Exception as e:
        db = SessionLocal()
        db.query(Task).filter(Task.id == task_id).update({"status": "error"})
        db.commit()
        db.close()
        if task_id in task_status_flags: task_status_flags[task_id] = "error"

        err_msg = f"引擎异常中断: {str(e)}"
        print(f"[{task_id}] ❌ {err_msg}")
        asyncio.run_coroutine_threadsafe(
            ws_manager.send_to_task(json.dumps({"type": "error", "message": err_msg}), task_id), loop)
    finally:
        cst_env.close()