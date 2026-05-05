<template>
  <n-card class="modern-card sandbox-card" size="large" hoverable>
    <template #header>
      <div class="sandbox-header">
        <n-icon size="28" color="#10b981"><Aperture /></n-icon>
        <span class="title-text">去物理化评分引擎演示沙盒</span>
      </div>
    </template>

    <n-grid :x-gap="24" :cols="24" style="align-items: stretch">
      <n-gi :span="7" class="panel-section input-panel">
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
          "
        >
          <n-h4 class="panel-title" style="margin: 0">1. 指标与规则设定</n-h4>
          <n-radio-group
            v-model:value="selectedAlgo"
            size="small"
            type="button"
          >
            <n-radio-button value="GA">GA (断崖)</n-radio-button>
            <n-radio-button value="BO">BO (平滑)</n-radio-button>
          </n-radio-group>
        </div>

        <n-scrollbar style="max-height: 520px; padding-right: 12px">
          <div
            v-for="(metric, index) in metrics"
            :key="index"
            class="metric-block"
          >
            <div class="metric-header">
              <span class="metric-name">{{ metric.name }}</span>
              <n-tag
                :type="metric.mode === 'maximize' ? 'success' : 'info'"
                size="small"
              >
                {{ metric.mode }}
              </n-tag>
            </div>

            <n-space vertical :size="16">
              <div class="control-row">
                <span class="label">模拟输出:</span>
                <n-slider
                  v-model:value="metric.val"
                  :min="metric.sliderMin"
                  :max="metric.sliderMax"
                  :step="metric.step"
                  style="flex: 1"
                />
                <n-input-number
                  v-model:value="metric.val"
                  size="small"
                  style="width: 85px"
                  :step="metric.step"
                  :show-button="false"
                />
              </div>

              <div class="control-row" v-if="metric.mode === 'maximize'">
                <span class="label">下限死区:</span>
                <n-input-number
                  v-model:value="metric.min_val"
                  size="small"
                  :step="metric.step"
                />
              </div>

              <template v-if="metric.mode === 'target'">
                <div class="control-row">
                  <span class="label">靶心频点:</span>
                  <n-input-number
                    v-model:value="metric.target_val"
                    size="small"
                    :step="metric.step"
                  />
                </div>
                <div class="control-row">
                  <span class="label">完美容差:</span>
                  <n-input-number
                    v-model:value="metric.tolerance"
                    size="small"
                    :step="0.01"
                  />
                </div>
                <div class="control-row">
                  <span class="label">最大偏离差:</span>
                  <n-input-number
                    v-model:value="metric.max_diff"
                    size="small"
                    :step="0.01"
                  />
                </div>
              </template>
            </n-space>
          </div>
        </n-scrollbar>
      </n-gi>

      <n-gi :span="11" class="panel-section flow-panel">
        <n-h4 class="panel-title">2. 评判流水线 ({{ selectedAlgo }} 策略)</n-h4>
        <div class="flow-center-wrapper">
          <div class="flow-container">
            <div
              v-for="(res, index) in evaluationResults.details"
              :key="index"
              class="flow-track"
            >
              <div class="flow-node input-node">
                <div class="node-title">基础适应度</div>
                <div class="node-val">
                  {{
                    (res.baseScore > 0 ? "+" : "") + res.baseScore.toFixed(2)
                  }}
                </div>
              </div>

              <div
                class="flow-connector"
                :class="{ 'connector-dead': res.isDead }"
              >
                <div class="flow-beam beam-blue"></div>
              </div>

              <div
                class="flow-node filter-node"
                :class="{ 'node-dead': res.isDead, 'node-pass': !res.isDead }"
              >
                <div class="node-title">拦截网关</div>
                <div class="node-status" v-if="!res.isDead">
                  <n-icon size="16"><CheckCircle2 /></n-icon> 畅通
                </div>
                <div class="node-status status-error" v-else>
                  <n-icon size="16"><XCircle /></n-icon> 越界 (Depth:
                  {{ res.depth.toFixed(2) }})
                </div>
              </div>

              <div
                class="flow-connector"
                :class="{ 'connector-dead': res.isDead }"
              >
                <div class="flow-beam beam-green"></div>
              </div>

              <div
                class="flow-node calc-node"
                :class="{
                  'node-dead-dim': res.isDead && selectedAlgo !== 'BO',
                }"
              >
                <div class="node-title">
                  {{
                    res.isDead && selectedAlgo === "BO"
                      ? "惩罚融合 (C0连续)"
                      : "单项最终得分"
                  }}
                </div>
                <div
                  class="node-score"
                  :class="{
                    'text-green': res.finalScore > 0 && !res.isDead,
                    'text-red': res.finalScore < 0,
                  }"
                >
                  {{
                    (res.finalScore >= 0 ? "+" : "") + res.finalScore.toFixed(2)
                  }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </n-gi>

      <n-gi :span="6" class="panel-section result-panel">
        <n-h4 class="panel-title" style="align-self: flex-start; width: 100%"
          >3. 综合适应度</n-h4
        >
        <div class="result-center-wrapper">
          <div
            class="final-score-box"
            :class="{
              'score-dead': evaluationResults.totalScore < -100,
              'score-good': evaluationResults.totalScore >= 0,
            }"
          >
            <div class="score-label">Fitness Score (&times; 100)</div>
            
            <div class="score-value-wrapper">
              <n-number-animation
                ref="numberAnimationInstRef"
                :from="lastScore"
                :to="evaluationResults.totalScore"
                :precision="1"
              />
            </div>
            
          </div>
          <div class="status-indicator">
            <n-alert
              :type="evaluationResults.totalScore < -100 ? 'error' : 'success'"
              :show-icon="true"
              class="custom-alert"
            >
              <template #icon>
                <n-icon
                  ><AlertTriangle
                    v-if="evaluationResults.totalScore < -100" /><Activity
                    v-else
                /></n-icon>
              </template>
              <div style="font-size: 13px; line-height: 1.5">
                <span v-if="selectedAlgo === 'BO' && evaluationResults.anyDead">
                  <b>BO策略：</b>已抹除断崖。得分在越界边界处绝对连续
                  ($C^0$)，平滑向负空间延伸，防止GP核函数崩溃。
                </span>
                <span v-else-if="evaluationResults.anyDead">
                  <b>GA策略：</b>触发刚性死区，得分强制锁定为
                  -10,000,000，执行一票否决淘汰。
                </span>
                <span v-else>
                  <b>状态完美：</b
                  >所有参数均在安全区，得分乘以倍率以拉开方差，增强寻优动机。
                </span>
              </div>
            </n-alert>
          </div>
        </div>
      </n-gi>
    </n-grid>
  </n-card>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import {
  Aperture,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Activity,
} from "lucide-vue-next";

const selectedAlgo = ref("GA");

const metrics = ref([
  {
    name: "输出功率 (GW)",
    val: 1.8,
    sliderMin: 0.0,
    sliderMax: 3.5,
    step: 0.01,
    mode: "maximize",
    min_val: 1.5,
    scale: 1.0,
    weight: 1.0,
  },
  {
    name: "起振频点 (GHz)",
    val: 3.02,
    sliderMin: 2.5,
    sliderMax: 3.5,
    step: 0.01,
    mode: "target",
    target_val: 3.0,
    tolerance: 0.05,
    max_diff: 0.3,
    scale: 0.1,
    weight: 10.0,
  },
  {
    name: "运行效率 (%)",
    val: 65.0,
    sliderMin: 0.0,
    sliderMax: 100.0,
    step: 0.5,
    mode: "maximize",
    min_val: 30.0,
    scale: 100.0,
    weight: 5.0,
  },
]);

const lastScore = ref(0);

const evaluationResults = computed(() => {
  let totalScore = 0;
  const details = [];
  let anyDead = false;

  for (const m of metrics.value) {
    let isDead = false;
    let depth = 0;
    let baseScore = 0;
    let finalScore = 0;

    // 1. 无论死活，先计算基础得分（保证边界连续性的基础）
    if (m.mode === "maximize") {
      baseScore = (m.val / (m.scale + 1e-9)) * m.weight;
    } else if (m.mode === "target") {
      const diff = Math.abs(m.val - m.target_val);
      if (diff <= m.tolerance) {
        baseScore = 1.0 * m.weight;
      } else {
        baseScore = (1.0 - (diff - m.tolerance) / (m.scale + 1e-9)) * m.weight;
      }
    }

    // 2. 检查死区并计算偏离深度
    if (m.mode === "maximize") {
      if (m.val < m.min_val) {
        isDead = true;
        depth = (m.min_val - m.val) / (Math.abs(m.min_val) + 1e-6);
      }
    } else if (m.mode === "target") {
      const diff = Math.abs(m.val - m.target_val);
      if (m.max_diff && diff > m.max_diff) {
        isDead = true;
        depth = (diff - m.max_diff) / (m.max_diff + 1e-6);
      }
    }

    // 3. 策略分发结算
    if (isDead) {
      anyDead = true;
      if (selectedAlgo.value === "BO") {
        // ✨ 核心修复：绝对连续的平滑衰减
        // 不再暴力设置为 -10000，而是继承边界处的 baseScore，并减去与 depth 相关的平滑惩罚
        // 这里用一个强大的线性/二次惩罚把分数拉下去
        const smoothPenalty = 500.0 * depth;
        finalScore = baseScore - smoothPenalty;
      } else {
        finalScore = -10000; // GA 单项展示的象征性断崖，总分会被重置
      }
    } else {
      finalScore = baseScore;
    }

    totalScore += finalScore;
    details.push({
      val: m.val,
      baseScore,
      depth,
      isDead,
      weight: m.weight,
      finalScore,
    });
  }

  // ✨ 最终结算：统一放大 100 倍，拉开方差，激活 GP
  let finalTotal = totalScore * 100.0;
  if (selectedAlgo.value === "GA" && anyDead) finalTotal = -10000000.0; // GA 一票否决

  return { totalScore: finalTotal, details, anyDead };
});

watch(
  () => evaluationResults.value.totalScore,
  (newVal, oldVal) => {
    lastScore.value = oldVal;
  },
);
</script>

<style scoped>
/* 样式与上一版保持一致，这里保留以确保渲染正常 */
.sandbox-card {
  background-color: var(--n-color);
  border-radius: 12px;
}
.sandbox-header {
  display: flex;
  align-items: center;
  gap: 14px;
}
.title-text {
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 1px;
}
.panel-section {
  padding: 20px;
  background: rgba(128, 128, 128, 0.02);
  border-radius: 10px;
  border: 1px solid rgba(128, 128, 128, 0.08);
  display: flex;
  flex-direction: column;
  height: 100%;
}
.panel-title {
  margin-top: 0;
  margin-bottom: 24px;
  font-weight: 600;
  font-size: 16px;
  color: var(--n-text-color);
  opacity: 0.85;
}

.metric-block {
  background: var(--n-card-color);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
  border-left: 4px solid #3b82f6;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}
.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: bold;
  font-size: 16px;
}
.control-row {
  display: flex;
  align-items: center;
  gap: 14px;
}
.control-row .label {
  width: 90px;
  font-size: 13px;
  opacity: 0.7;
}
.flow-center-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
/* ✨ 新增：右侧结果面板强制垂直与水平双居中 */
.result-center-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}
.flow-container {
  display: flex;
  flex-direction: column;
  gap: 36px;
  padding-top: 12px;
}
.flow-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.flow-connector {
  flex: 1;
  min-width: 40px;
  height: 6px;
  background: rgba(128, 128, 128, 0.15);
  margin: 0 12px;
  position: relative;
  overflow: hidden;
  border-radius: 3px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
}
.flow-beam {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-size: 200% 100%;
  animation: data-flow 1.2s linear infinite; /* 加快流动速度 */
}
/* ✨ 增加发光阴影，让渐变色真正产生“霓虹管”的视觉冲击 */
.beam-blue {
  background-image: linear-gradient(
    90deg,
    transparent 0%,
    #3b82f6 50%,
    transparent 100%
  );
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.6);
}
.beam-green {
  background-image: linear-gradient(
    90deg,
    transparent 0%,
    #10b981 50%,
    transparent 100%
  );
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);
}
.connector-dead {
  background: rgba(239, 68, 68, 0.2);
}
.connector-dead .flow-beam {
  animation: none;
  background: #ef4444;
  opacity: 0.9;
  box-shadow: 0 0 10px rgba(239, 68, 68, 0.6);
}

@keyframes data-flow {
  0% {
    background-position: 100% 0;
  }
  100% {
    background-position: -100% 0;
  }
}

.flow-node {
  padding: 14px 12px;
  border-radius: 8px;
  text-align: center;
  min-width: 120px;
  background: var(--n-card-color);
  border: 1px solid rgba(128, 128, 128, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.node-title {
  font-size: 11px;
  opacity: 0.6;
  margin-bottom: 8px;
  font-weight: bold;
}
.node-val {
  font-size: 20px;
  font-family: "JetBrains Mono", monospace;
  font-weight: 900;
  -webkit-text-stroke: 0.5px var(--n-text-color); /* 增肌描边 */
}
.node-score {
  font-size: 18px;
  font-family: "JetBrains Mono", monospace;
  font-weight: 900;
  -webkit-text-stroke: 0.5px currentColor; /* 增肌描边 */
}
.score-value-wrapper { 
  font-size: 40px; /* 超大字号 */
  font-weight: 900; /* 最粗字重 */
  font-family: 'JetBrains Mono', monospace; 
  -webkit-text-stroke: 2px currentColor; /* 核心：双倍物理描边，彻底消灭发虚 */
  text-shadow: 0 0 25px currentColor; /* 霓虹光晕扩散 */
  line-height: 1.1;
}

/* ✨ 击穿组件防护墙！强制让组件内部的动态数字继承我们刚刚写的巨型样式 */
.score-value-wrapper :deep(span) {
  font-size: inherit !important;
  font-weight: inherit !important;
  font-family: inherit !important;
}


.status-error {
  color: #ef4444;
}
.text-green {
  color: #10b981;
}
.text-red {
  color: #ef4444;
}
.node-dead-dim {
  opacity: 0.3;
  filter: grayscale(1);
  border-style: dashed;
}

.final-score-box {
  text-align: center;
  padding: 40px 0;
  border-radius: 12px;
  margin-bottom: 24px;
  border: 1px solid transparent;
}
.score-label { 
  font-size: 18px; /* 字体加大 */
  text-transform: uppercase; 
  letter-spacing: 2px; 
  opacity: 0.85; 
  margin-bottom: 16px; 
  font-weight: 900; /* 加粗 */
}

.score-good {
  color: #10b981;
  background: radial-gradient(
    circle,
    rgba(16, 185, 129, 0.1) 0%,
    transparent 75%
  );
}
.score-dead {
  color: #ef4444;
  background: radial-gradient(
    circle,
    rgba(239, 68, 68, 0.1) 0%,
    transparent 75%
  );
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(239, 68, 68, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}
</style>
