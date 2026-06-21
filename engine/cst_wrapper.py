import time
import gc
import sys
import os
import json
import traceback

cst_lib_path = os.getenv(
    "CST_PYTHON_PATH",
    r"D:\CST Studio Suite 2024\AMD64\python_cst_libraries"
)
if cst_lib_path not in sys.path:
    sys.path.append(cst_lib_path)

# 从同级目录导入 evaluator
from .evaluator import get_time_domain_metric, analyze_spectrum, extract_freq_extremum, extract_bandwidth, extract_freq_point

def parse_cst_parameters(cst_path):
    """
    扫描 CST 项目目录,提取数值型变量
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


def run_single_simulation(project, param_dict, targets_list, env_cfg, cst_path, cst_env=None):
    """
    执行单次 CST 仿真,提取特征并返回扁平化的物理量字典。
    支持动态目标列表解析与智能提取分发。
    cst_env: 可选,用于失败时重新打开 project 做重试。
    """
    metrics = {}

    use_stable_time = env_cfg.get('useStableTime', True)
    stable_time = env_cfg.get('stableTime', 20.0) if use_stable_time else 0.0

    try:
        # 1. 写入参数
        modeler = project.model3d
        param_str = ', '.join(f'{k}={v}' for k, v in list(param_dict.items())[:3])
        print(f"  [CST] 写入参数: {param_str}...", flush=True)
        for k, v in param_dict.items():
            modeler.add_to_history('StoreParameter', f'StoreParameter("{k}", "{v}")')

        # 2. 非阻塞启动求解器 + 轮询 + 中间态结果刷新
        poll_interval = float(env_cfg.get('pollInterval', 15.0))
        print(f"  [CST] 启动求解器(非阻塞)... 轮询间隔 {poll_interval}s", flush=True)
        modeler.start_solver()

        elapsed = 0.0
        while modeler.is_solver_running():
            time.sleep(poll_interval)
            elapsed += poll_interval
            # 刷新结果树，强制 CST 将当前仿真数据写入磁盘
            modeler.add_to_history('ResultTree', 'ResultTree.UpdateTree()')
            # 预留中间态数据提取接口（轮询时读 S 参数/功率曲线用于前端实时渲染）

        print(f"  [CST] 求解器完成 (耗时 {elapsed:.0f}s)，保存项目...", flush=True)
        project.save()

        # 3. 等待 CST 将结果写入磁盘
        # PIC 仿真结束后，CST 需要时间把内存数据 flush 到 .results 文件
        # 默认等 3 秒，可在 env_cfg 中配置 resultWaitTime 覆盖
        result_wait = float(env_cfg.get('resultWaitTime', 3.0))
        print(f"  [CST] 等待 {result_wait}s 让结果写入磁盘...", flush=True)
        time.sleep(result_wait)

        # 4. 校验结果文件
        import cst.results
        import os
        cst_dir = os.path.splitext(cst_path)[0]
        # CST 结果通常在 .results 目录下
        results_dir = cst_dir + '.results'
        if os.path.exists(results_dir):
            result_files = os.listdir(results_dir)
            total_size = sum(os.path.getsize(os.path.join(results_dir, f)) for f in result_files if os.path.isfile(os.path.join(results_dir, f)))
            print(f"  [CST] 结果目录: {len(result_files)} 个文件, 总大小 {total_size / 1024:.1f} KB", flush=True)
        else:
            print(f"  [CST] ⚠️ 结果目录不存在: {results_dir}", flush=True)

        # 5. 打开结果文件（带重试）
        res = None
        for attempt in range(3):
            try:
                res = cst.results.ProjectFile(cst_path, allow_interactive=True)
                break
            except Exception as open_e:
                print(f"  [CST] ⚠️ 打开结果文件失败 (尝试 {attempt+1}/3): {open_e}", flush=True)
                if attempt < 2:
                    time.sleep(2.0)

        if res is None:
            raise RuntimeError(f"无法打开 CST 结果文件 (已重试 3 次): {cst_path}")


        # 6.核心:遍历前端传来的动态目标列表进行数据抓取
        for t_cfg in targets_list:
            t_name = t_cfg.get('name', 'Unknown')
            t_path = t_cfg.get('path', '')
            t_mode = t_cfg.get('mode', 'maximize')
            extract_method = t_cfg.get('extractMethod', 'time_mean')
            multiplier = float(t_cfg.get('multiplier', 1.0))

            if not t_path:
                continue

            try:
                # 规则 A:频域找主峰
                if extract_method == 'freq_peak':
                    target_val = t_cfg.get('target_val') if t_mode == 'target' else None
                    blind_gap = t_cfg.get('constraints', {}).get('max_diff', None)

                    f_val, side_ratio, fft_curve = analyze_spectrum(res, t_path, target_val, blind_gap)

                    metrics[t_name] = f_val * multiplier if f_val != -1 else f_val
                    metrics[f'{t_name}_curve'] = fft_curve

                    if side_ratio is not None:
                        metrics[f'{t_name}_side_ratio'] = side_ratio

                # 规则 B:直接读取单值标量 (例如驻波比、损耗等 0D 结果)
                elif extract_method == '0d_scalar':
                    item = res.get_3d().get_result_item(t_path)
                    val = float(item.get_ydata()[0])
                    metrics[t_name] = val * multiplier

                # 规则 C:带宽提取
                elif extract_method == 'bandwidth':
                    threshold = t_cfg.get('bw_threshold', -10.0)
                    compare = t_cfg.get('bw_compare', 'less')
                    freq_range = t_cfg.get('bw_freq_range', None)
                    data = extract_bandwidth(res, t_path, threshold, compare, freq_range)
                    val = data.get('value', 0.0)
                    metrics[t_name] = val * multiplier
                    metrics[f'{t_name}_start_freq'] = data.get('start_freq', 0.0)
                    metrics[f'{t_name}_end_freq'] = data.get('end_freq', 0.0)
                    metrics[f'{t_name}_center_freq'] = data.get('center_freq', 0.0)
                    metrics[f'{t_name}_curve'] = data.get('curve')

                # 规则 D:指定频率点读取
                elif extract_method == 'freq_point':
                    target_freq = t_cfg.get('target_freq', 0.0)
                    use_interp = t_cfg.get('freq_interp', True)
                    require_extremum = t_cfg.get('require_extremum', False)
                    extremum_type = t_cfg.get('extremum_type', 'min')

                    data = extract_freq_point(res, t_path, target_freq, use_interp)
                    val = data.get('value', 0.0)
                    metrics[t_name] = val * multiplier
                    metrics[f'{t_name}_actual_freq'] = data.get('actual_freq', 0.0)
                    metrics[f'{t_name}_curve'] = data.get('curve')

                    # 如果要求该点为极值点,额外提取极值信息用于约束检查
                    if require_extremum:
                        extremum_data = extract_freq_extremum(res, t_path, extremum_type)
                        extremum_val = extremum_data.get('value', 0.0)
                        extremum_freq = extremum_data.get('freq', 0.0)
                        metrics[f'{t_name}_extremum_val'] = extremum_val * multiplier
                        metrics[f'{t_name}_extremum_freq'] = extremum_freq
                        # 检查指定频率点是否是极值点(允许0.1GHz的容差)
                        is_extremum = abs(target_freq - extremum_freq) < 0.1
                        metrics[f'{t_name}_is_extremum'] = 1.0 if is_extremum else 0.0

                # 规则 E:时域稳态求平均 (默认兜底)
                else:
                    data = get_time_domain_metric(res, t_path, stable_time)
                    val = data.get('mean', 0.0)
                    metrics[t_name] = val * multiplier
                    metrics[f'{t_name}_curve'] = data.get('curve')
                    # 提取双轨波动率,且绝对波动必须同频乘以用户的量纲!
                    metrics[f'{t_name}_fluc_rel'] = data.get('fluc_rel', 0.0)
                    metrics[f'{t_name}_fluc_abs'] = data.get('fluc_abs', 0.0) * multiplier

            except Exception as inner_e:
                # 容错拦截：如果这个特定的指标没提出来（比如路径错了，或者 CST 没出这个图）
                # 记录警告，并给予默认的死区数值，但绝不中断整个个体的打分！
                print(f"⚠️ 指标 [{t_name}] 提取失败，已设为兜底值 0.0。原因: {inner_e}", flush=True)

                # 给一个兜底的数值,防止后续计分器因为找不到 Key 报错
                metrics[t_name] = 0.0

                # 如果这个指标前端需要画曲线,塞一个空的曲线数据进去,防止前端 ECharts 渲染崩溃
                if extract_method in ['freq_peak', 'time_mean', 'bandwidth', 'freq_point', '0d_scalar']:
                    metrics[f'{t_name}_curve'] = {'x': [], 'y': []}

    except Exception as e:
        # 外层的 try-except 现在只负责捕捉"致命错误"
        # 例如:CST 软件卡死、求解器彻底报错没跑完、文件读写权限被拒等
        metrics['error'] = str(e)
        print(f"❌ CST 致命仿真失败: {e}", flush=True)
        print(f"   完整堆栈:\n{traceback.format_exc()}", flush=True)
    finally:
        try:
            del res
        except:
            pass
        gc.collect()

    return metrics