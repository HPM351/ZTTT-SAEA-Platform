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


def extract_freq_extremum(results_obj, result_path, extremum_type='min'):
    """
    全频带极值提取：找曲线的最大值或最小值点
    适用于：S11谐振点（最小值）、S21最大传输点等
    返回: dict with 'value', 'freq', 'curve'
    """
    res = {'value': 0.0, 'freq': 0.0, 'valid': False, 'curve': None}
    try:
        item = results_obj.get_3d().get_result_item(result_path)
        if item is None:
            return res
        y, x = np.array(item.get_ydata()), np.array(item.get_xdata())

        # 曲线降采样用于前端展示
        target_pts = 4000
        if len(x) > target_pts:
            indices = np.linspace(0, len(x) - 1, target_pts).astype(int)
            res['curve'] = {'x': x[indices].tolist(), 'y': y[indices].tolist()}
        else:
            res['curve'] = {'x': x.tolist(), 'y': y.tolist()}

        if len(y) == 0:
            return res

        # 根据类型找极值
        if extremum_type == 'min':
            idx = np.argmin(y)
        else:  # 'max'
            idx = np.argmax(y)

        res['value'] = float(y[idx])
        res['freq'] = float(x[idx])
        res['valid'] = True
    except:
        pass
    return res


def extract_bandwidth(results_obj, result_path, threshold, compare='less', freq_range=None):
    """
    带宽提取：计算曲线在阈值以上/以下的频率范围宽度
    适用于：S11 < -10dB 带宽、S21 > -3dB 带宽等
    参数:
        threshold: 阈值 (dB)
        compare: 'less' (小于阈值) 或 'greater' (大于阈值)
        freq_range: [min_freq, max_freq] 可选，限制计算范围
    返回: dict with 'value', 'start_freq', 'end_freq', 'center_freq', 'curve'
    """
    res = {'value': 0.0, 'start_freq': 0.0, 'end_freq': 0.0, 'center_freq': 0.0, 'valid': False, 'curve': None}
    try:
        item = results_obj.get_3d().get_result_item(result_path)
        if item is None:
            return res
        y, x = np.array(item.get_ydata()), np.array(item.get_xdata())

        # 曲线降采样用于前端展示
        target_pts = 4000
        if len(x) > target_pts:
            indices = np.linspace(0, len(x) - 1, target_pts).astype(int)
            res['curve'] = {'x': x[indices].tolist(), 'y': y[indices].tolist()}
        else:
            res['curve'] = {'x': x.tolist(), 'y': y.tolist()}

        if len(y) == 0:
            return res

        # 可选：限制频率范围
        if freq_range is not None:
            mask = (x >= freq_range[0]) & (x <= freq_range[1])
            x = x[mask]
            y = y[mask]
            if len(y) == 0:
                return res

        # 找满足条件的频段
        if compare == 'less':
            mask = y < threshold
        else:  # 'greater'
            mask = y > threshold

        # 找最长连续频段
        bandwidths = []
        in_band = False
        start_idx = 0

        for i in range(len(mask)):
            if mask[i] and not in_band:
                start_idx = i
                in_band = True
            elif not mask[i] and in_band:
                bw = x[i - 1] - x[start_idx]
                bandwidths.append({
                    'start': float(x[start_idx]),
                    'end': float(x[i - 1]),
                    'bw': float(bw),
                    'center': float((x[start_idx] + x[i - 1]) / 2)
                })
                in_band = False

        # 处理末尾
        if in_band:
            bw = x[-1] - x[start_idx]
            bandwidths.append({
                'start': float(x[start_idx]),
                'end': float(x[-1]),
                'bw': float(bw),
                'center': float((x[start_idx] + x[-1]) / 2)
            })

        # 返回最大带宽
        if bandwidths:
            best = max(bandwidths, key=lambda b: b['bw'])
            res['value'] = best['bw']
            res['start_freq'] = best['start']
            res['end_freq'] = best['end']
            res['center_freq'] = best['center']
            res['valid'] = True
    except:
        pass
    return res


def extract_freq_point(results_obj, result_path, target_freq, interp=True):
    """
    指定频率点读取：提取特定频率点的值
    适用于：读取 2.45GHz 处的 S11 值等
    参数:
        target_freq: 目标频率
        interp: 是否插值
    返回: dict with 'value', 'actual_freq', 'curve'
    """
    res = {'value': 0.0, 'actual_freq': 0.0, 'valid': False, 'curve': None}
    try:
        item = results_obj.get_3d().get_result_item(result_path)
        if item is None:
            return res
        y, x = np.array(item.get_ydata()), np.array(item.get_xdata())

        # 曲线降采样用于前端展示
        target_pts = 4000
        if len(x) > target_pts:
            indices = np.linspace(0, len(x) - 1, target_pts).astype(int)
            res['curve'] = {'x': x[indices].tolist(), 'y': y[indices].tolist()}
        else:
            res['curve'] = {'x': x.tolist(), 'y': y.tolist()}

        if len(y) == 0:
            return res

        if interp:
            # 线性插值获取精确值
            res['value'] = float(np.interp(target_freq, x, y))
            res['actual_freq'] = float(target_freq)
        else:
            # 找最近的点
            idx = np.argmin(np.abs(x - target_freq))
            res['value'] = float(y[idx])
            res['actual_freq'] = float(x[idx])

        res['valid'] = True
    except:
        pass
    return res


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

        # [Level 0.5] 检测提取失败的哨兵值 (-1)
        # freq_peak 找不到峰值时返回 -1，这种情况应该直接判为死区
        extract_method = t_cfg.get('extractMethod', 'time_mean')
        if extract_method == 'freq_peak' and val == -1:
            is_dead = True
            depth = 1.0  # 直接判为深度死区
            if algo_type == "BO":
                smooth_penalty = 500.0 * depth
                total_score += (0.0 - smooth_penalty)
            else:
                any_dead = True
            continue
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
            # 对于bandwidth，零值意味着没有找到满足条件的频段，应判为死区
            if extract_method == 'bandwidth' and val == 0:
                is_dead = True
                depth = 1.0
            else:
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
        # Level 1.7: 指定频率点极值约束
        # ==========================================
        is_extremum_key = f"{t_name}_is_extremum"
        if is_extremum_key in metrics and constraints.get('enable', False):
            require_extremum = t_cfg.get('require_extremum', False)
            if require_extremum:
                is_extremum = metrics.get(is_extremum_key, 0.0)
                if is_extremum < 0.5:  # 该点不是极值点
                    # 软惩罚：根据偏离程度递减分数
                    penalty_ratio = 0.8  # 固定惩罚80%
                    base_score *= (1.0 - penalty_ratio)

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