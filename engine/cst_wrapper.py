import time
import gc
import sys
import os
import json

# === 恢复你原有的 CST 环境变量配置 ===
cst_lib_path = r"D:\CST Studio Suite 2024\AMD64\python_cst_libraries"
if cst_lib_path not in sys.path:
    sys.path.append(cst_lib_path)

# 从同级目录导入 evaluator
from .evaluator import get_time_domain_metric, analyze_spectrum

def parse_cst_parameters(cst_path):
    """
    扫描 CST 项目目录，提取数值型变量
    """
    params = {}
    cst_dir = os.path.splitext(cst_path)[0]

    if not os.path.exists(cst_dir):
        return params

    # 策略 A: 读取 Parameters.json
    json_path = os.path.join(cst_dir, "Model", "Parameters.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "parameters" in data:
                for item in data["parameters"]:
                    name = item.get("name")
                    expr_str = item.get("expr")
                    if name and expr_str:
                        try:
                            params[name] = float(expr_str)
                        except ValueError:
                            pass
                if params: return params
        except Exception:
            pass

    # 策略 B: 搜索 Model.par
    par_file_path = None
    for root, dirs, files in os.walk(cst_dir):
        if "Model.par" in files:
            par_file_path = os.path.join(root, "Model.par")
            break

    if par_file_path:
        content = []
        for enc in ['utf-8', 'gbk', 'latin-1']:
            try:
                with open(par_file_path, 'r', encoding=enc) as f:
                    content = f.readlines()
                break
            except:
                continue

        for line in content:
            if "=" in line:
                try:
                    parts = line.split("=", 1)
                    key = parts[0].strip()
                    val_str = parts[1].strip().replace('"', '').replace(';', '')
                    params[key] = float(val_str)
                except:
                    pass
    return params

def run_single_simulation(project, param_dict, targets_cfg, env_cfg, cst_path):
    """
    执行单次 CST 仿真，提取特征并返回字典。
    """
    metrics = {}
    stable_time = env_cfg.get('stableTime', 20.0)

    try:
        # 1. 写入参数
        modeler = project.model3d
        for k, v in param_dict.items():
            modeler.add_to_history('StoreParameter', f'StoreParameter("{k}", "{v}")')

        # 2. 启动求解器
        modeler.run_solver()
        project.save()
        time.sleep(1.0)  # 缓冲写入

        # 3. 读取结果
        import cst.results
        res = cst.results.ProjectFile(cst_path, allow_interactive=True)

        # 提取频率
        if 'freq' in targets_cfg and targets_cfg['freq'].get('enable', False):
            f_cfg = targets_cfg['freq']
            f_val, side_ratio, fft_curve = analyze_spectrum(res, f_cfg['path'], f_cfg['target'], f_cfg['blindGap'])
        else:
            # 默认提取主频供展示，不计算杂波比
            f_val, side_ratio, fft_curve = analyze_spectrum(res, r"Tables\1D Results\FFT")
        metrics.update({'freq': f_val, 'side_ratio': side_ratio, 'fft_curve': fft_curve})

        # 提取功率
        if 'power' in targets_cfg and 'path' in targets_cfg['power']:
            p_data = get_time_domain_metric(res, targets_cfg['power']['path'], stable_time)
            metrics.update({'power_val': p_data['mean'], 'power_fluc': p_data['fluc'],
                            'power_valid': p_data['valid'], 'power_curve': p_data['curve']})

        # 提取效率
        if 'eff' in targets_cfg and 'path' in targets_cfg['eff']:
            e_data = get_time_domain_metric(res, targets_cfg['eff']['path'], stable_time)
            metrics.update({'eff_val': e_data['mean'] * 100, 'eff_fluc': e_data['fluc'],
                            'eff_valid': e_data['valid'], 'eff_curve': e_data['curve']})

        if 'mainMode' in targets_cfg and targets_cfg['mainMode'].get('enable', False):
            m_path = targets_cfg['mainMode']['path']
            # 复用时域提取函数抓取曲线 (Port signals 也是时域曲线)
            m_data = get_time_domain_metric(res, m_path, stable_time)
            metrics.update({'main_mode_curve': m_data['curve']})

    except Exception as e:
        metrics['error'] = str(e)
        print(f"❌ CST 仿真失败: {e}")
    finally:
        try:
            del res
        except:
            pass
        gc.collect()

    return metrics