import numpy as np
from scipy.signal import find_peaks


# ==========================================
# 基础提取工具 (保留原样，作为纯粹的工具函数)
# ==========================================
def get_auto_scaled_power(y_vals):
    max_val = np.max(np.abs(y_vals))
    if max_val >= 1e9:
        return y_vals / 1e9, "GW"
    elif max_val >= 1e6:
        return y_vals / 1e6, "MW"
    elif max_val >= 1e3:
        return y_vals / 1e3, "kW"
    else:
        return y_vals, "W"


def get_time_domain_metric(results_obj, result_path, stable_start):
    """时域曲线稳态提取"""
    res = {'mean': 0.0, 'fluc': 0.0, 'valid': False, 'curve': None}
    try:
        item = results_obj.get_3d().get_result_item(result_path)
        if item is None: return res
        y, x = np.array(item.get_ydata()), np.array(item.get_xdata())

        target_points = 2000
        if len(x) > target_points:
            indices = np.linspace(0, len(x) - 1, target_points).astype(int)
            res['curve'] = {'x': x[indices].tolist(), 'y': y[indices].tolist()}
        else:
            res['curve'] = {'x': x.tolist(), 'y': y.tolist()}

        mask = x > stable_start
        stable_y = y[mask]
        if len(stable_y) > 10:
            p_mean = np.mean(stable_y)
            res['mean'] = p_mean

            max_dev = np.max(np.abs(stable_y - p_mean))
            # 同时提取相对值与绝对值
            res['fluc_rel'] = max_dev / abs(p_mean) if abs(p_mean) > 1e-9 else 0.0
            res['fluc_abs'] = max_dev
            res['valid'] = True
    except:
        pass
    return res


def analyze_spectrum(results_obj, fft_path, target_freq=None, gap_blind=None):
    """频域提取与杂波比计算"""
    res_data = {'main': -1, 'ratio': None, 'curve': None}
    try:
        spec_item = results_obj.get_3d().get_result_item(fft_path)
        if not spec_item: return -1, None, None
        y, x = np.array(spec_item.get_ydata()), np.array(spec_item.get_xdata())

        target_pts = 4000
        if len(x) > target_pts:
            indices = np.linspace(0, len(x) - 1, target_pts).astype(int)
            res_data['curve'] = {'x': x[indices].tolist(), 'y': y[indices].tolist()}
        else:
            res_data['curve'] = {'x': x.tolist(), 'y': y.tolist()}

        max_val = np.max(y)
        if max_val < 1e-9: return -1, None, res_data['curve']

        peaks, _ = find_peaks(y, height=max_val * 0.05)
        if len(peaks) == 0: return -1, None, res_data['curve']

        peak_ys, peak_xs = y[peaks], x[peaks]
        main_freq = peak_xs[np.argmax(peak_ys)]

        if target_freq is None or gap_blind is None:
            return main_freq, None, res_data['curve']

        lower_bound, upper_bound = target_freq - gap_blind, target_freq + gap_blind
        max_side = max([py for px, py in zip(peak_xs, peak_ys) if px < lower_bound or px > upper_bound], default=0.0)

        return main_freq, max_side / max_val, res_data['curve']
    except:
        return -1, None, None


# ==========================================
# Level 4：算法流派策略模式 (Gateway)
# 也是对外暴露的唯一接口
# ==========================================
def calc_score(metrics, targets_list, algo_type="SAEA-GA"):
    """
    通用大网关：接收扁平化的 metrics 字典和动态目标列表 targets_list。
    根据 algo_type 分发不同的死区惩罚策略。
    """
    # [Level 0] 致命错误：CST 崩溃或未能提取数据
    if 'error' in metrics:
        return -50000.0 if algo_type == "BO" else -1e7

    total_score = 0.0
    any_dead = False

    # 遍历所有目标，执行评估
    for t_cfg in targets_list:
        mode = t_cfg.get('mode', 'maximize')

        # 遇到“仅展示模式”，直接放行，不产生任何分数和惩罚
        if mode == 'display_only':
            continue

        t_name = t_cfg.get('name')
        val = metrics.get(t_name, 0.0)

        weight = float(t_cfg.get('weight', 1.0))
        scale = float(t_cfg.get('reference_scale', 1.0))
        constraints = t_cfg.get('constraints', {})

        is_dead = False
        depth = 0.0
        base_score = 0.0

        # ==========================================
        # Level 1: 计算无视死区的基础得分
        # ==========================================
        if mode == 'maximize':
            base_score = (val / (scale + 1e-9)) * weight
        elif mode == 'minimize':
            base_score = (1.0 - (val / (scale + 1e-9))) * weight
        elif mode == 'target':
            target_val = float(t_cfg.get('target_val', 0.0))
            tol = float(t_cfg.get('tolerance', 0.0))
            diff = abs(val - target_val)
            if diff <= tol:
                base_score = 1.0 * weight
            else:
                base_score = (1.0 - (diff - tol) / (scale + 1e-9)) * weight

        # ==========================================
        # Level 1.5: 时域波动率软/硬惩罚
        # ==========================================
        if constraints.get('enable', False) and constraints.get('max_fluc') is not None:
            fluc_type = constraints.get('fluc_type', 'relative')
            max_fluc_input = float(constraints.get('max_fluc'))

            # 智能分发判定基准
            if fluc_type == 'relative':
                actual_fluc = metrics.get(f"{t_name}_fluc_rel", 0.0)
                fluc_A = max_fluc_input / 100.0
                fluc_B = fluc_A * 3.0
            else:
                actual_fluc = metrics.get(f"{t_name}_fluc_abs", 0.0)
                fluc_A = max_fluc_input
                fluc_B = fluc_A * 3.0

            if actual_fluc > fluc_A:
                if actual_fluc <= fluc_B:
                    # 加重惩罚梯度！最高削减 95% 基础分，让震荡波形彻底失去竞争力
                    penalty_ratio = 0.95 * ((actual_fluc - fluc_A) / (fluc_B - fluc_A))
                    base_score *= (1.0 - penalty_ratio)
                else:
                    is_dead = True
                    depth += (actual_fluc - fluc_B) / (fluc_B + 1e-6)

        # ==========================================
        # Level 1.6: 频域杂模抑制软/硬惩罚
        # ==========================================
        side_ratio_key = f"{t_name}_side_ratio"
        if side_ratio_key in metrics and constraints.get('enable', False):
            # 前端如果没传，默认 A 为 10%，B 为 30%
            ratio_A = float(constraints.get('max_side_ratio', 10.0)) / 100.0
            ratio_B = float(constraints.get('max_side_ratio_B', ratio_A * 3.0)) / 100.0

            actual_ratio = metrics[side_ratio_key]
            if actual_ratio > ratio_A:
                if actual_ratio <= ratio_B:
                    # 缓坡惩罚
                    p_ratio = 0.5 * ((actual_ratio - ratio_A) / (ratio_B - ratio_A))
                    base_score *= (1.0 - p_ratio)
                else:
                    # 杂模超过 B：频域崩溃，触发死区
                    is_dead = True
                    depth += (actual_ratio - ratio_B) / (ratio_B + 1e-6)

        # ==========================================
        # Level 2: 刚性约束拦截网校验 (原始 min/max)
        # ==========================================
        if constraints.get('enable', False):
            if mode == 'target':
                max_diff = constraints.get('max_diff')
                if max_diff is not None and abs(val - target_val) > max_diff:
                    is_dead = True
                    depth += (abs(val - target_val) - max_diff) / (max_diff + 1e-6)
            else:
                min_val = constraints.get('min')
                max_val = constraints.get('max')
                if min_val is not None and val < min_val:
                    is_dead = True
                    depth += (min_val - val) / (abs(min_val) + 1e-6)
                if max_val is not None and val > max_val:
                    is_dead = True
                    depth += (val - max_val) / (abs(max_val) + 1e-6)

        # ==========================================
        # Level 3: 策略结算与惩罚融合
        # ==========================================
        if is_dead:
            any_dead = True
            if algo_type == "BO":
                # 恢复 BO 的负梯度深渊设计
                smooth_penalty = 500.0 * depth
                total_score += (base_score - smooth_penalty)
        else:
            total_score += base_score

    # ==========================================
    # 最终总评与量级放大
    # ==========================================
    if any_dead and algo_type != "BO":
        return -1e7  # GA/PSO 只要踩到任何红线，直接打入深渊

    return total_score * 100.0