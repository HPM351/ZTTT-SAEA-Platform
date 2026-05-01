import time
import gc
import sys
import os
import json

cst_lib_path = os.getenv(
    "CST_PYTHON_PATH", 
    r"D:\CST Studio Suite 2024\AMD64\python_cst_libraries"
)
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


def run_single_simulation(project, param_dict, targets_list, env_cfg, cst_path):
    """
    执行单次 CST 仿真，提取特征并返回扁平化的物理量字典。
    支持动态目标列表解析与智能提取分发。
    """
    metrics = {}

    # 新增：从前端提取“稳态时间”与“是否使用稳态时间”开关
    use_stable_time = env_cfg.get('useStableTime', True)
    stable_time = env_cfg.get('stableTime', 20.0) if use_stable_time else 0.0

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


        # 5.核心：遍历前端传来的动态目标列表进行数据抓取
        for t_cfg in targets_list:
            t_name = t_cfg.get('name', 'Unknown')
            t_path = t_cfg.get('path', '')
            t_mode = t_cfg.get('mode', 'maximize')
            extract_method = t_cfg.get('extractMethod', 'time_mean')
            multiplier = float(t_cfg.get('multiplier', 1.0))

            if not t_path:
                continue

            try:
                # 规则 A：频域找主峰
                if extract_method == 'freq_peak':
                    target_val = t_cfg.get('target_val') if t_mode == 'target' else None
                    blind_gap = t_cfg.get('constraints', {}).get('max_diff', None)

                    f_val, side_ratio, fft_curve = analyze_spectrum(res, t_path, target_val, blind_gap)

                    metrics[t_name] = f_val * multiplier if f_val != -1 else f_val
                    metrics[f'{t_name}_curve'] = fft_curve

                    if side_ratio is not None:
                        metrics[f'{t_name}_side_ratio'] = side_ratio

                # 规则 B：直接读取单值标量 (例如驻波比、损耗等 0D 结果)
                elif extract_method == '0d_scalar':
                    item = res.get_3d().get_result_item(t_path)
                    val = float(item.get_ydata()[0])
                    metrics[t_name] = val * multiplier

                # 规则 C：时域稳态求平均 (默认兜底)
                else:
                    data = get_time_domain_metric(res, t_path, stable_time)
                    val = data.get('mean', 0.0)
                    metrics[t_name] = val * multiplier
                    metrics[f'{t_name}_curve'] = data.get('curve')
                    # 提取双轨波动率，且绝对波动必须同频乘以用户的量纲！
                    metrics[f'{t_name}_fluc_rel'] = data.get('fluc_rel', 0.0)
                    metrics[f'{t_name}_fluc_abs'] = data.get('fluc_abs', 0.0) * multiplier

            except Exception as inner_e:
                # 容错拦截：如果这个特定的指标没提出来（比如路径错了，或者 CST 没出这个图）
                # 记录警告，并给予默认的死区数值，但绝不中断整个个体的打分！
                print(f"⚠️ 指标 [{t_name}] 提取失败，已设为兜底值 0.0。原因: {inner_e}")

                # 给一个兜底的数值，防止后续计分器因为找不到 Key 报错
                metrics[t_name] = 0.0

                # 如果这个指标前端需要画曲线，塞一个空的曲线数据进去，防止前端 ECharts 渲染崩溃
                if extract_method in ['freq_peak', 'time_mean']:
                    metrics[f'{t_name}_curve'] = {'x': [], 'y': []}

    except Exception as e:
        # 外层的 try-except 现在只负责捕捉“致命错误”
        # 例如：CST 软件卡死、求解器彻底报错没跑完、文件读写权限被拒等
        metrics['error'] = str(e)
        print(f"❌ CST 致命仿真失败: {e}")
    finally:
        try:
            del res
        except:
            pass
        gc.collect()

    return metrics