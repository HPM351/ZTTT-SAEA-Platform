import numpy as np
from scipy.signal import find_peaks


# ==========================================
# 基础提取工具 (保持原样，无需改动)
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
# 模块 0：公共奖励计算 (仅针对安全区的管子)
# ==========================================
def _calc_shared_reward(m, objs):
    """
    当管子跨越所有生死线后，进入此模块进行精细的内卷打分。
    ✨ 修复了 Target 模式下的十倍放大失衡 Bug，现已做到功率效率 1:1 公平对决。
    """
    reward_score = 0.0
    BASE_L3 = -10.0

    for metric_key, config_key in [('power', 'power'), ('eff', 'eff')]:
        if config_key in objs and objs[config_key].get('enable', False):
            o = objs[config_key]
            val_key, fluc_key = f"{metric_key}_val", f"{metric_key}_fluc"

            val = m.get(val_key, 0)
            fluc = m.get(fluc_key, 0)

            raw_target = o['target']
            tol_fluc = o['fluc'] / 100.0
            tol_target = o.get('tolerance', o['fluc']) / 100.0
            weight = o['weight']

            # --- 单位统一与归一化标尺 ---
            if config_key == 'power':
                # 这里的 target_val 就是前端填的“参考基准”
                target_val = raw_target * 1e6
                norm_val = val / (target_val + 1e-6)
            else:
                target_val = raw_target
                norm_val = val / 100.0

            # --- 时域纹波罚分 (独立结算) ---
            if fluc > tol_fluc:
                reward_score += BASE_L3 * (fluc / tol_fluc) * 2.0

            # --- 目标模式判决 ---
            if o['mode'] == 'target':
                if val < target_val:
                    diff_from_target = target_val - val
                    allowed_error = target_val * tol_target

                    # 只有跌出平顶区边缘，才开始计算惩罚
                    if diff_from_target > allowed_error:
                        dist_from_edge = diff_from_target - allowed_error

                        # 1. 边缘平滑扣分
                        reward_score += BASE_L3 * (dist_from_edge / (allowed_error + 1e-6))

                        # 2. ✨ 核心修复：移除 *10.0 的暴君惩罚，改为与 Maximize 完全对等的相对归一化扣分
                        norm_dist = dist_from_edge / (target_val + 1e-6)
                        reward_score -= norm_dist * weight
            else:
                # Maximize 模式：无限向上加分
                reward_score += norm_val * weight

    return reward_score


# ==========================================
# 算法流派一：GA/PSO (断崖淘汰派)
# ==========================================
def calc_score_ga(m, objs):
    """
    GA 和 PSO 专属评分：不惧断崖，优胜劣汰，只保留绝对的数字层级。
    """
    # [Level 4] 致命错误：直接 -1e7 秒杀
    if 'error' in m or m.get('freq', -1) <= 0: return -1e7
    if 'eff' in objs and objs['eff'].get('checkPhys', True):
        eff_val = m.get('eff_val', 0)
        if eff_val < 0 or eff_val > 100: return -1e7

    # [Level 3] 频率错误：短路截断，直接按偏离程度重罚
    if 'freq' in objs and objs['freq'].get('enable', False):
        o = objs['freq']
        freq_val, target_f, blind_gap = m['freq'], o['target'], o['blindGap']
        side_ratio = m.get('side_ratio', 1.0)

        if abs(freq_val - target_f) > blind_gap:
            base = -abs(o.get('penaltyBase', 10000))
            return base * (1.0 + o.get('decayK', 10.0) * abs(freq_val - target_f))
        if side_ratio > 0.1:
            return -abs(o.get('clutterPenalty', 3000)) * side_ratio

    # [Level 2] 死区判定：无视梯度，-300 分出局
    dead_penalty = -300.0
    if 'power' in objs and objs['power'].get('enable', False):
        if m.get('power_val', 0) < objs['power']['deadThresh'] * 1e6: return dead_penalty
    if 'eff' in objs and objs['eff'].get('enable', False):
        if m.get('eff_val', 0) < objs['eff']['deadThresh']: return dead_penalty

    # [Level 1] 安全区：正分疯狂放大 (100倍)
    raw_score = _calc_shared_reward(m, objs)
    return raw_score * 100.0 if raw_score > 0 else raw_score


def calc_score_pso(m, objs):
    # PSO 目前与 GA 的逻辑完美兼容
    return calc_score_ga(m, objs)


# ==========================================
# 算法流派二：贝叶斯优化 BO (平滑梯度派)
# ==========================================
def calc_score_bo(m, objs):
    """
    BO 专属评分：必须处处连续可导，利用相对深度和有理渐近线完美护航层级。
    """
    # [Level 4] 致命错误：用 -50000 作为谷底
    if 'error' in m or m.get('freq', -1) <= 0: return -50000.0
    if 'eff' in objs and objs['eff'].get('checkPhys', True):
        eff_val = m.get('eff_val', 0)
        if eff_val < 0 or eff_val > 100: return -50000.0

    penalty_score = 0.0
    is_dead = False

    # [Level 3] 频率错误：✨ 采用有理函数渐近线 (-10000 ~ -40000)
    if 'freq' in objs and objs['freq'].get('enable', False):
        o = objs['freq']
        freq_val, target_f, blind_gap = m['freq'], o['target'], o['blindGap']
        side_ratio = m.get('side_ratio', 1.0)

        diff = abs(freq_val - target_f)
        if diff > blind_gap:
            base_penalty = -10000.0
            max_extra_penalty = 30000.0
            decay_k = 0.5  # 曲线衰减平缓度
            net_diff = diff - blind_gap

            # 有理衰减，偏离10000GHz也不会跌穿-40000
            penalty_score += base_penalty - max_extra_penalty * (net_diff / (net_diff + decay_k))
            is_dead = True

        if side_ratio > 0.1:
            penalty_score -= abs(o.get('clutterPenalty', 3000)) * side_ratio
            is_dead = True

    # [Level 2] 死区判定：采用相对深度连续陡坡 (-100 ~ -2200)
    # 只有频率没问题时，才去计算死区，防止层级分数混合干扰
    if not is_dead:
        p_thresh = objs['power']['deadThresh'] * 1e6 if 'power' in objs and objs['power'].get('enable', False) else 0
        e_thresh = objs['eff']['deadThresh'] if 'eff' in objs and objs['eff'].get('enable', False) else 0

        p_val = m.get('power_val', 0)
        e_val = m.get('eff_val', 0)

        dead_zone_penalty = 0.0
        if p_thresh > 0 and p_val < p_thresh:
            depth = (p_thresh - p_val) / p_thresh
            dead_zone_penalty -= (100.0 + 1000.0 * depth)
            is_dead = True

        if e_thresh > 0 and e_val < e_thresh:
            depth = (e_thresh - e_val) / e_thresh
            dead_zone_penalty -= (100.0 + 1000.0 * depth)
            is_dead = True

        penalty_score += dead_zone_penalty

    # 如果在前面的流程中跌落了任何深渊（层级被短路锁定）
    if is_dead or penalty_score < 0:
        return penalty_score

    # [Level 1] 安全区
    # ✨ 接受沙盘推演的 Hotfix：BO 的原分直接返回，不乘 100 倍！
    # 高斯过程不需要放大也能拟合正分区的微小地形，且防止死区层级倒挂
    raw_score = _calc_shared_reward(m, objs)
    return raw_score


# ==========================================
# 网关路由 (对外暴露的主入口)
# ==========================================
def calc_score(m, objs, algo_type="SAEA-GA"):
    """
    通过前端传来的 algo_type (默认 GA)，自动将数据分发给最适合该算法数学特性的评估引擎。
    """
    if algo_type == "BO":
        return calc_score_bo(m, objs)
    elif algo_type == "PSO":
        return calc_score_pso(m, objs)
    else:
        return calc_score_ga(m, objs)