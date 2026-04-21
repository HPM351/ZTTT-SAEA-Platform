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
            res['fluc'] = (np.max(stable_y) - np.min(stable_y)) / abs(p_mean) if abs(p_mean) > 1e-9 else 0.0
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
        t_name = t_cfg.get('name')
        val = metrics.get(t_name, 0.0)

        mode = t_cfg.get('mode', 'maximize')
        weight = float(t_cfg.get('weight', 1.0))
        scale = float(t_cfg.get('reference_scale', 1.0))
        constraints = t_cfg.get('constraints', {})

        is_dead = False
        depth = 0.0
        base_score = 0.0

        # ==========================================
        # Level 1: 计算无视死区的基础得分 (锚定连续性)
        # ==========================================
        if mode == 'maximize':
            base_score = (val / (scale + 1e-9)) * weight
        elif mode == 'minimize':
            # 翻转为正向奖励，表现越好越接近满分 weight
            base_score = (1.0 - (val / (scale + 1e-9))) * weight
        elif mode == 'target':
            target_val = float(t_cfg.get('target_val', 0.0))
            tol = float(t_cfg.get('tolerance', 0.0))
            diff = abs(val - target_val)
            if diff <= tol:
                base_score = 1.0 * weight
            else:
                # 容差外平滑衰减
                base_score = (1.0 - (diff - tol) / (scale + 1e-9)) * weight

        # ==========================================
        # Level 2: 刚性约束拦截网校验
        # ==========================================
        if constraints.get('enable', False):
            if mode == 'target':
                max_diff = constraints.get('max_diff')
                if max_diff is not None and abs(val - target_val) > max_diff:
                    is_dead = True
                    depth = abs(val - target_val) - max_diff
            else:
                min_val = constraints.get('min')
                max_val = constraints.get('max')
                if min_val is not None and val < min_val:
                    is_dead = True
                    depth = (min_val - val) / (abs(min_val) + 1e-6)
                if max_val is not None and val > max_val:
                    is_dead = True
                    depth = (val - max_val) / (abs(max_val) + 1e-6)

        # ==========================================
        # Level 3: 策略结算与惩罚融合
        # ==========================================
        if is_dead:
            any_dead = True
            if algo_type == "BO":
                # BO 专属：消除断崖！继承该个体的优秀基础分，仅叠加平滑斜率惩罚
                smooth_penalty = 500.0 * depth
                total_score += (base_score - smooth_penalty)
            else:
                pass  # GA 模式下只要有一次 dead，总分直接作废，这里无需累加
        else:
            total_score += base_score

    # ==========================================
    # 最终总评与量级放大
    # ==========================================
    if any_dead and algo_type != "BO":
        return -1e7  # GA/PSO 一票否决

    # 统一放大 100 倍，拉开方差，刺激算法寻找梯度
    return total_score * 100.0