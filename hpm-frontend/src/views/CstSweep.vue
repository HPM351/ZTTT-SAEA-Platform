<template>
  <div class="cst-container" :class="isDarkMode ? 'dark-mode' : 'light-mode'">
    <div class="sidebar">
      <div class="sidebar-header">
        <n-space align="center">
          <h2 style="margin: 0; font-weight: 700; letter-spacing: 1px">
            联合扫参配置
          </h2>
        </n-space>
        <n-space align="center">
          <n-tag
            :type="isRunning ? 'primary' : 'default'"
            round
            :bordered="false"
            size="large"
          >
            {{ isRunning ? "扫描引擎执行中" : "系统空闲" }}
          </n-tag>
        </n-space>
      </div>

      <n-scrollbar style="max-height: calc(100vh - 180px); padding-right: 16px">
        <n-form label-placement="top" :show-feedback="false">
<!-- ================= 模块 1: 项目与任务配置 (扫参配置加载) ================= -->
          <n-card class="modern-card" size="small">
            <template #header
              ><span class="card-title">📂 项目与任务</span></template
            >
            <n-form-item label="加载历史扫描任务">
              <n-select
                v-model:value="config.selectedHistoryTask"
                :options="historyTaskOptions"
                placeholder="选择一个已完成的任务..."
                @update:value="loadHistoricalTask"
              />
            </n-form-item>
            <n-form-item label="CST 项目路径">
              <div class="vertical-group">
                <n-input-group>
                  <n-input
                    v-model:value="config.cstPath"
                    placeholder="请输入完整 .cst 路径"
                    clearable
                    @blur="
                      () => {
                        fetchModelPreview();
                        tryLoadConfig(config.cstPath);
                      }
                    "
                  />
                  <n-button type="primary" secondary @click="triggerFileInput"
                    >📁 本地浏览</n-button
                  >
                </n-input-group>
              </div>
            </n-form-item>
            <n-form-item label="当前扫描任务名称" style="margin-top: 16px">
              <n-input
                v-model:value="config.taskName"
                placeholder="例如: Sweep_Plan_A"
                clearable
              />
            </n-form-item>
          </n-card>
<!-- ================= 模块 2: 变量遍历控制 (笛卡尔积/步长设置) ================= -->
          <n-card class="modern-card" size="small">
            <template #header>
              <div
                style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                "
              >
                <span class="card-title">变量管理</span>
                <n-space>
                  <n-button
                    type="info"
                    secondary
                    size="small"
                    @click="readFromCST"
                    >从CST导入</n-button
                  >
                  <n-button
                    type="primary"
                    secondary
                    size="small"
                    @click="saveConfig"
                    >保存配置</n-button
                  >
                </n-space>
              </div>
            </template>
            <n-button
              type="default"
              dashed
              block
              style="margin-bottom: 16px"
              @click="addVariable"
              >+ 新增变量维度</n-button
            >

            <transition-group
              name="list-anim"
              tag="div"
              class="params-list-container"
            >
              <div
                v-for="item in config.paramsList"
                :key="item.id"
                class="var-item"
              >
                <n-grid
                  :x-gap="12"
                  :y-gap="12"
                  :cols="24"
                  style="align-items: center"
                >
                  <n-gi :span="8">
                    <n-input v-model:value="item.name" placeholder="变量名" />
                  </n-gi>
                  <n-gi
                    :span="13"
                    style="display: flex; justify-content: flex-end"
                  >
                    <n-switch
                      v-model:value="item.isSweep"
                      size="medium"
                      @update:value="sortParamsList"
                    >
                      <template #checked>Sweep (扫参)</template>
                      <template #unchecked>Fix (固定值)</template>
                    </n-switch>
                  </n-gi>
                  <n-gi :span="3" style="text-align: right">
                    <n-button
                      type="error"
                      quaternary
                      circle
                      size="small"
                      @click="removeVariable(item.id)"
                      >🗑️</n-button
                    >
                  </n-gi>
                </n-grid>

                <div
                  v-if="item.isSweep"
                  class="sweep-row"
                  style="margin-top: 12px"
                >
                  <n-grid :x-gap="8" :cols="3">
                    <n-gi>
                      <n-input-number
                        v-model:value="item.min"
                        :show-button="false"
                        size="small"
                      >
                        <template #prefix
                          ><span class="inner-label">Min</span></template
                        >
                      </n-input-number>
                    </n-gi>
                    <n-gi>
                      <n-input-number
                        v-model:value="item.max"
                        :show-button="false"
                        size="small"
                      >
                        <template #prefix
                          ><span class="inner-label">Max</span></template
                        >
                      </n-input-number>
                    </n-gi>
                    <n-gi>
                      <n-input-number
                        v-model:value="item.points"
                        :show-button="false"
                        size="small"
                        :min="1"
                      >
                        <template #prefix
                          ><span class="inner-label">Pts</span></template
                        >
                      </n-input-number>
                    </n-gi>
                  </n-grid>
                  <div class="step-hint" v-if="item.points > 1">
                    步长:
                    {{ ((item.max - item.min) / (item.points - 1)).toFixed(4) }}
                  </div>
                </div>
                <div v-else class="var-fix-row">
                  <n-slider
                    v-model:value="item.val"
                    :min="item.min"
                    :max="item.max"
                    :step="0.001"
                    style="flex: 1; margin: 0 12px"
                  />
                  <n-input-number
                    v-model:value="item.val"
                    style="width: 80px"
                    :show-button="false"
                    size="small"
                  />
                </div>
              </div>
            </transition-group>

            <div class="total-count-tag" v-if="totalCombinations > 0">
              预计总仿真次数:
              <span class="text-neon-blue">{{ totalCombinations }}</span>
            </div>
          </n-card>
<!-- ================= 模块 3: 动态目标与指标路径注册 ================= -->
          <n-collapse :default-expanded-names="['paths']">
            <n-collapse-item title="📂 CST 动态监控目标配置" name="paths">
              <n-button dashed block @click="addTarget" style="margin-bottom: 12px;">+ 新增监控目标</n-button>
              <div v-for="(t, idx) in config.targetsList" :key="idx" class="inner-panel">
                <n-grid :cols="24" :x-gap="12">
                  <n-gi :span="6"><n-input v-model:value="t.name" size="small" placeholder="变量名(英文)" /></n-gi>
                  <n-gi :span="6"><n-input v-model:value="t.display" size="small" placeholder="显示名(中文)" /></n-gi>
                  <n-gi :span="10"><n-input v-model:value="t.path" size="small" placeholder="CST 结果树路径" /></n-gi>
                  <n-gi :span="2"><n-button type="error" quaternary size="small" @click="config.targetsList.splice(idx, 1)">🗑️</n-button></n-gi>
                </n-grid>
                <n-grid :cols="2" :x-gap="12" style="margin-top: 8px;">
                  <n-gi>
                    <n-select size="small" v-model:value="t.extractMethod" :options="[{label:'时域均值', value:'time_mean'}, {label:'频域主峰', value:'freq_peak'}, {label:'零维标量', value:'0d_scalar'}]" />
                  </n-gi>
                  <n-gi>
                    <n-input-number size="small" v-model:value="t.multiplier" placeholder="量纲倍率 (如 1e-6)" />
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>
          </n-collapse>
        </n-form>
      </n-scrollbar>
<!-- ================= 模块 4: 扫参引擎动作触发区 ================= -->
      <div class="action-area">
        <n-button
          v-if="!isRunning"
          type="primary"
          size="large"
          class="start-btn"
          @click="startSweep"
          >启动网格扫参</n-button
        >
        <n-button
          v-else
          type="error"
          size="large"
          class="start-btn"
          @click="stopOptimization"
          >强制终止 (Kill)</n-button
        >
      </div>
    </div>

    <div class="main-content">
<!-- ================= 模块 5: 总体扫描进度面板 ================= -->
      <n-grid :x-gap="16" :cols="1" style="margin-bottom: 16px">
        <n-gi>
          <n-card class="metric-card" size="small">
            <n-statistic label="总体扫描进度 (Sweep Progress)">
              <div style="display: flex; align-items: center; min-height: 45px">
                <n-progress
                  type="line"
                  :percentage="
                    totalCombinations
                      ? Math.round((currentSweepIdx / totalCombinations) * 100)
                      : 0
                  "
                  :height="14"
                  status="info"
                  processing
                  style="width: 100%"
                >
                  <span
                    style="
                      font-weight: 800;
                      font-size: 24px;
                      color: var(--n-text-color);
                      margin-left: 14px;
                    "
                  >
                    {{ currentSweepIdx }}
                    <span class="text-sub" style="font-size: 18px"
                      >/ {{ totalCombinations }}</span
                    >
                  </span>
                </n-progress>
              </div>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>
<!-- ================= 模块 6: 结构预览面板 ================= -->
      <div class="middle-row">
        <n-card
          class="chart-card model-card"
          style="flex: 3"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div class="card-header">
            <span class="card-title">结构预览</span>
            <n-button
              size="tiny"
              secondary
              type="info"
              @click="fetchModelPreview"
              :loading="isFetchingImage"
              >刷新</n-button
            >
          </div>
          <div class="model-preview-container">
            <img
              v-if="modelImageUrl"
              :src="modelImageUrl"
              class="model-image"
            />
            <div v-else class="hologram-scanner">AWAITING .dib ...</div>
          </div>
        </n-card>
<!-- ================= 模块 7: 扫参波形动态审查 (按需加载) ================= -->
        <n-card
          class="chart-card wave-card"
          style="flex: 7"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div
            class="card-header"
            style="
              flex-direction: column;
              align-items: flex-start;
              gap: 14px;
              padding: 16px;
            "
          >
            <div
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
                flex-wrap: wrap;
                gap: 12px;
              "
            >
              <n-space align="center" :size="16" wrap>
                <span class="card-title" style="white-space: nowrap"
                  >波形审查台
                  <span
                    style="font-weight: normal; font-size: 13px"
                    class="text-sub"
                    >| ID: {{ inspectIdx }}</span
                  ></span
                >
                <n-radio-group v-model:value="activeWaveTab" size="small" @update:value="updateInspectorChart">
                  <n-radio-button v-for="t in config.targetsList" :key="t.name" :value="t.name">
                    {{ t.display || t.name }}
                  </n-radio-button>
                </n-radio-group>
              </n-space>

              <n-space align="center" :size="12" wrap style="margin-left: auto">
                <n-input-group style="width: auto">
                  <n-input-group-label size="small" style="padding: 0 8px"
                    >ID</n-input-group-label
                  >
                  <n-select
                    v-model:value="inspectIdx"
                    :options="sweepIdxOptions"
                    size="small"
                    style="width: 100px"
                    @update:value="updateInspectorChart"
                  />
                </n-input-group>
                <n-button
                  quaternary
                  circle
                  size="small"
                  @click="toggleFullscreen"
                  ><n-icon><Maximize /></n-icon
                ></n-button>
              </n-space>
            </div>

            <div
              class="param-tags-container"
              style="margin-top: 4px; align-items: center"
            >
              <span
                style="font-size: 13px; margin-right: 12px; flex-shrink: 0"
                class="text-sub"
                >组合参数:</span
              >
              <div
                v-if="inspectedParams"
                class="param-tags-wrapper"
                style="gap: 8px"
              >
                <n-tag
                  v-for="(v, k) in inspectedParams"
                  :key="k"
                  size="small"
                  type="info"
                  :bordered="false"
                  style="
                    font-family: monospace;
                    font-size: 13px;
                    padding: 0 10px;
                  "
                >
                  {{ k }}:
                  {{ typeof v === "number" && v % 1 !== 0 ? v.toFixed(3) : v }}
                </n-tag>
              </div>
              <span v-else style="font-size: 13px" class="text-sub"
                >等待数据传入...</span
              >
            </div>
          </div>

          <div style="flex: 1; position: relative; min-width: 0; min-height: 0">
            <div
              ref="inspectorChartRef"
              style="
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                width: 100%;
                height: 100%;
                border-radius: 0 0 8px 8px;
                overflow: hidden;
              "
            ></div>
          </div>
        </n-card>
      </div>

      <div class="bottom-row">
<!-- ================= 模块 8: 多维遍历结果分布 (全量散点) ================= -->
        <n-card
          class="chart-card scatter-card"
          style="flex: 6.5"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div class="card-header">
            <span class="card-title">多维结果分布 (散点映射)</span>
            <n-space align="center" :size="12">
              <n-input-group>
                <n-input-group-label size="small">X轴</n-input-group-label>
                <n-select
                  v-model:value="scatterConfig.xAxis"
                  :options="axisOptions"
                  size="small"
                  style="width: 130px"
                  @update:value="refreshScatterChart"
                />
              </n-input-group>
              <n-input-group>
                <n-input-group-label size="small">Y轴</n-input-group-label>
                <n-select
                  v-model:value="scatterConfig.yAxis"
                  :options="axisOptions"
                  size="small"
                  style="width: 130px"
                  @update:value="refreshScatterChart"
                />
              </n-input-group>
              <n-input-group>
                <n-input-group-label size="small">颜色轴</n-input-group-label>
                <n-select
                  v-model:value="scatterConfig.color"
                  :options="axisOptions"
                  size="small"
                  style="width: 130px"
                  @update:value="refreshScatterChart"
                />
              </n-input-group>
              <n-button quaternary circle size="small" @click="toggleFullscreen"
                ><n-icon><Maximize /></n-icon
              ></n-button>
            </n-space>
          </div>
          <div style="flex: 1; position: relative">
            <div
              ref="scatterChartRef"
              style="position: absolute; inset: 0"
            ></div>
          </div>
        </n-card>
<!-- ================= 模块 9: 扫参运行终端 (WebSocket) ================= -->
        <n-card
          class="chart-card terminal-card"
          style="flex: 3.5"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div class="card-header">
            <span class="card-title">Sweep Log</span>
          </div>
          <div style="flex: 1; position: relative;">
            <div class="log-window" ref="logWindowRef">
              <div v-for="(log, i) in logs" :key="i" class="log-item">
                <span class="log-prefix">root@sweep:~$</span
                ><span v-html="log"></span>
              </div>
            </div>
          </div>
        </n-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  reactive,
  onMounted,
  onUnmounted,
  computed,
  inject,
  nextTick,
} from "vue";
import { Maximize } from "lucide-vue-next";
import { NIcon, useMessage, useDialog } from "naive-ui";
import * as echarts from "echarts";
import axios from "axios";

// === 响应式状态与主题管理 ===
const isDarkMode = inject("globalTheme", ref(true));
const islandState = inject("islandState");
const message = useMessage();
const dialog = useDialog();
const API_BASE = "/api";
const WS_BASE = `ws://${window.location.host}/ws`;
const currentTaskId = ref(null);
const historyTaskOptions = ref([]);

// 1. 读取历史任务列表
const fetchHistoryTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/recent_tasks?task_type=sweep`); 
    if (res.data.status === "success") {
      historyTaskOptions.value = res.data.tasks.map((t) => ({
        label: t.name,
        value: t.id,
      }));
    }
  } catch (err) {
    console.error("获取历史任务失败", err);
  }
};

// 2. 点击历史任务后，恢复界面和数据
const loadHistoricalTask = async (taskId) => {
  message.loading(`正在还原任务 [${taskId}] ...`);
  try {
    const resData = await axios.get(`${API_BASE}/get_task_data/${taskId}`);
    
    // 拦截后端的错误报错并显示出来
    if (resData.data.status !== "success") {
      message.error(resData.data.message || "读取历史数据失败");
      return;
    }

    const d = resData.data;
    
    // 1. 恢复前端配置和图表动态坐标
    if (d.config_json) {
      Object.assign(config, d.config_json);
      if (config.targetsList && config.targetsList.length > 0) {
        const targetExists = config.targetsList.some(t => t.name === activeWaveTab.value);
        if (!targetExists) activeWaveTab.value = config.targetsList[0].name;
        
        scatterConfig.xAxis = config.targetsList[0]?.name || "";
        scatterConfig.yAxis = config.targetsList[1]?.name || config.targetsList[0]?.name || "";
        scatterConfig.color = config.targetsList[2]?.name || config.targetsList[0]?.name || "";
      }
      if (config.cstPath) fetchModelPreview();
    }

    // 2. 数据入池
    Object.keys(allDataPool).forEach(k => delete allDataPool[k]);

    const pool = d.all_data_pool || {};
    if (pool["1"] && !pool["1"].params && !pool["1"].metrics) {
       Object.assign(allDataPool, pool["1"]);
    } else {
       Object.assign(allDataPool, pool);
    }

    try {
      const indRes = await fetch(`${API_BASE}/tasks/${taskId}/individuals`);
      const indData = await indRes.json();
      const inds = indData.individuals || [];
      
      // 将真实数据库 ID 注入到内存池中，为后续按需加载波形做准备
      inds.forEach(ind => {
        if (!allDataPool[ind.ind_index]) {
          allDataPool[ind.ind_index] = {}; // 兜底，防止该节点丢失
        }
        allDataPool[ind.ind_index].db_id = ind.id;
        allDataPool[ind.ind_index].params = ind.params_json || {};
        allDataPool[ind.ind_index].metrics = ind.metrics_json || {};
      });
    } catch (e) {
      console.warn("拉取数据库个体数据失败", e);
    }

    // 3. 恢复指针和进度
    const keys = Object.keys(allDataPool);
    if (keys.length > 0) {
      currentSweepIdx.value = Math.max(...keys.map(Number));
      inspectIdx.value = currentSweepIdx.value;
    }

    await nextTick();
    refreshScatterChart();
    updateInspectorChart();
    
    message.success("✅ 历史扫参数据已无损复原");
    
  } catch (err) {
    message.error("网络异常，数据恢复失败");
    console.error(err);
  }
};

// 3. 根据路径自动加载本地配置
const tryLoadConfig = async (path) => {
  if (!path) return;
  try {
    const res = await axios.post(`${API_BASE}/load_config`, { cstPath: path });
    if (res.data.status === "success") {
      const saved = res.data.config;

      // 1. 恢复参数列表并触发排序
      if (saved.paramsList) {
        config.paramsList = saved.paramsList;
        sortParamsList(); 
      }

      // 2. 恢复动态目标列表
      if (saved.targetsList && Array.isArray(saved.targetsList)) {
        config.targetsList = saved.targetsList;
      }

      message.success(`📂 已同步 CST 项目参数与结果路径`);
    }
  } catch (err) {
    console.error("加载配置失败", err);
  }
};

// 4. 保存当前配置到本地
const saveConfig = async () => {
  if (!config.cstPath) {
    message.warning("请先填写 CST 路径再保存！");
    return;
  }
  try {
    const res = await axios.post(`${API_BASE}/save_config`, config);
    if (res.data.status === "success") {
      message.success("扫参配置已保存！");
    }
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.message || err.message;
    message.error(`保存失败: ${detail}`);
  }
};

// 5. 从 CST 导入变量
const readFromCST = async () => {
  if (!config.cstPath) return message.warning("请先填写 CST 项目路径！");
  message.loading("正在扫描 CST 变量...");
  try {
    const res = await axios.post(`${API_BASE}/parse_cst_params`, {
      cstPath: config.cstPath,
    });
    if (res.data.status === "success") {
      config.paramsList = []; // 清空旧列表
      let count = 0;
      for (const [p_name, p_val] of Object.entries(res.data.params)) {
        let p_min = p_val === 0 ? -10.0 : p_val > 0 ? p_val * 0.5 : p_val * 1.5;
        let p_max = p_val === 0 ? 10.0 : p_val > 0 ? p_val * 1.5 : p_val * 0.5;

        config.paramsList.push({
          id: Math.random().toString(36).substr(2, 9),
          name: p_name,
          min: Number(p_min.toFixed(2)),
          max: Number(p_max.toFixed(2)),
          val: p_val,
          points: 5, 
          isSweep: false, 
        });
        count++;
      }
      message.success(`✅ 成功导入 ${count} 个变量！`);
    } else {
      message.warning(res.data.message);
    }
  } catch (err) {
    message.error("请求失败，请确保后台已启动");
  }
};

const config = reactive({
  cstPath: "",
  taskName: "Sweep_Task_001",
  paramsList: [],
  targetsList: [
    { name: "Power", display: "功率(MW)", path: "Tables\\1D Results\\AVGpower", extractMethod: "time_mean", multiplier: 1e-6 },
    { name: "Efficiency", display: "效率(%)", path: "Tables\\1D Results\\EFF", extractMethod: "time_mean", multiplier: 100 },
    { name: "Frequency", display: "频率(GHz)", path: "Tables\\1D Results\\FFT", extractMethod: "freq_peak", multiplier: 1 }
  ]
});

const addTarget = () => {
  config.targetsList.push({ name: "NewMetric", display: "新指标", path: "", extractMethod: "time_mean", multiplier: 1 });
};

// 计算总仿真组合数 (Cartesian Product)
const totalCombinations = computed(() => {
  const sweepVars = config.paramsList.filter((p) => p.isSweep);
  if (sweepVars.length === 0) return 0;
  return sweepVars.reduce((acc, curr) => acc * (curr.points || 1), 1);
});

const isRunning = ref(false);
const currentSweepIdx = ref(0);
const inspectIdx = ref(1);
const activeWaveTab = ref("power");
const logs = ref(["[SYSTEM] READY FOR PARAMETER SWEEP."]);
const logWindowRef = ref(null);
const modelImageUrl = ref("");
const isFetchingImage = ref(false);

const allDataPool = reactive({}); // 扁平化存储：{ sweepIdx: data }
const sweepIdxOptions = computed(() =>
  Object.keys(allDataPool).map((idx) => ({
    label: `ID: ${idx}`,
    value: parseInt(idx),
  })),
);
const inspectedParams = computed(
  () => allDataPool[inspectIdx.value]?.params || null,
);

// 散点图多维配置
const scatterConfig = reactive({
  xAxis: config.targetsList[0]?.name || "",
  yAxis: config.targetsList[1]?.name || "",
  color: config.targetsList[2]?.name || config.targetsList[0]?.name || ""
});
// 动态生成坐标轴可选项 (包含参数和结果)
const axisOptions = computed(() => {
  const options = [];
  config.paramsList.forEach(p => {
    if (p.isSweep) options.push({ label: `[参数] ${p.name}`, value: p.name });
  });
  config.targetsList.forEach(t => {
    options.push({ label: `[指标] ${t.display || t.name}`, value: t.name });
  });
  return options;
});

// === ECharts 初始化 ===
let inspectorChart = null;
let scatterChart = null;
let inspectorResizeObserver = null;
let scatterResizeObserver = null;
const inspectorChartRef = ref(null);
const scatterChartRef = ref(null);

const getThemeColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.7)" : "rgba(0, 0, 0, 0.7)";
const getGridColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.05)" : "rgba(0, 0, 0, 0.1)";

const initCharts = () => {
  if (inspectorChartRef.value) {
    inspectorChart = echarts.init(inspectorChartRef.value);
  
    inspectorResizeObserver = new ResizeObserver(() => {
      if (inspectorChart) inspectorChart.resize();
    });
    inspectorResizeObserver.observe(inspectorChartRef.value);
  }
  
  if (scatterChartRef.value) {
    scatterChart = echarts.init(scatterChartRef.value);
    
    // 监听散点图点击事件，联动波形台
    scatterChart.on('click', (params) => {
      if (params.data && params.data.id) {
        inspectIdx.value = Number(params.data.id);
        updateInspectorChart();
        message.info(`已切换至扫描点 ID: ${params.data.id}`);
      }
    });
    
    scatterResizeObserver = new ResizeObserver(() => {
      if (scatterChart) scatterChart.resize();
    });
    scatterResizeObserver.observe(scatterChartRef.value);
    
    refreshScatterChart();
  }
};

const updateInspectorChart = async () => {
  if (!inspectorChart) return;

  // 1. 取出当前选中的 Sweep ID 对应的数据
  const currentData = allDataPool[inspectIdx.value];
  if (!currentData) {
    inspectorChart.clear(); // 没数据时清空画布
    return;
  }

  const targetName = activeWaveTab.value;

  // 补全按需加载逻辑。如果内存里没有波形数据，但存在 db_id，就向后端 DataCenter 发起请求拉取波形
  if (!currentData.waves && !currentData[`${targetName}_curve`] && currentData.db_id) {
    try {
      const res = await axios.get(`${API_BASE}/individuals/${currentData.db_id}/waveform`);
      if (res.data.status === "success" && res.data.waveforms) {
        // 将后端返回的全量字典缓存到内存中，避免重复请求
        currentData.waves = res.data.waveforms;
      }
    } catch (e) {
      console.warn(`[Sweep] 按需加载波形失败 (ID: ${currentData.db_id})`, e);
    }
  }

  // 2. 根据选中的标签提取对应的波形坐标数组
  let wave = null;
  if (currentData.waves && currentData.waves[targetName]) {
    wave = currentData.waves[targetName];           // 走实时扫参或刚拉取的数据流
  } else if (currentData[`${targetName}_curve`]) {
    wave = currentData[`${targetName}_curve`];      // 兼容历史老版本格式
  }

  if (!wave || !wave.x || !wave.y || wave.x.length === 0) {
    inspectorChart.clear();
    return;
  }

  const textColor = getThemeColor();
  const gridColor = getGridColor();

  // 3. 动态配置坐标轴名称
  let xName = "Time / Freq";
  let yName = "Amplitude";
  let multiplier = 1;
  
  // 自动从动态目标列表中查找当前激活的 Tab 配置
  const currentTargetConfig = config.targetsList.find(t => t.name === activeWaveTab.value);
  if (currentTargetConfig) {
      if (currentTargetConfig.extractMethod === 'freq_peak') {
          xName = "Frequency (GHz)";
          yName = "幅度 (Amplitude)"; 
      } else {
          xName = "Time (ns)";
          yName = currentTargetConfig.display || currentTargetConfig.name;
      }
      multiplier = currentTargetConfig.multiplier || 1;
  }
  const scaledY = wave.y.map(val => val * multiplier);

  // 4. 组装 ECharts 渲染参数 (与优化界面保持一致的霓虹绿渐变风格)
  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
    },
    grid: { top: 40, right: 40, bottom: 40, left: 60 },
    xAxis: {
      name: xName,
      type: "category",
      data: wave.x.map((val) => Number(val).toFixed(4)),
      axisLabel: { color: textColor },
      splitLine: { show: false },
    },
    yAxis: {
      name: yName,
      type: "value",
      scale: true,
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: "dashed" } },
    },
    series: [
      {
        type: "line",
        data: scaledY,
        smooth: true,
        showSymbol: false,
        lineStyle: { width: 2, color: "#10b981" }, // 主题绿
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(16,185,129,0.3)" },
            { offset: 1, color: "rgba(16,185,129,0.05)" },
          ]),
        },
      },
    ],
  };
  inspectorChart.setOption(option, true);
};

const refreshScatterChart = () => {
  if (!scatterChart) return;
  const textColor = getThemeColor();
  const gridColor = getGridColor();

  let minColorVal = Infinity;
  let maxColorVal = -Infinity;

  // 组装数据并提取当前颜色维度的极小值与极大值
  const seriesData = Object.entries(allDataPool).map(([idx, data]) => {
    const getVal = (key) => {
      if (data.metrics && data.metrics[key] !== undefined) return data.metrics[key];
      if (data.params && data.params[key] !== undefined) return data.params[key];
      return 0; 
    };

    const cVal = getVal(scatterConfig.color);
    if (cVal < minColorVal) minColorVal = cVal;
    if (cVal > maxColorVal) maxColorVal = cVal;

    return {
      value: [getVal(scatterConfig.xAxis), getVal(scatterConfig.yAxis), cVal],
      id: idx,
      params: data.params,
    };
  });

  // 如果当前只有一个点，或者所有点的颜色映射值都一样，强行拉开极值，防止 ECharts 颜色条崩溃
  if (minColorVal === Infinity || minColorVal === maxColorVal) {
    minColorVal = minColorVal === Infinity ? 0 : minColorVal - 1;
    maxColorVal = minColorVal + 2;
  }

  // 辅助函数：根据选项值获取中文 Label
  const getLabel = (val) =>
    axisOptions.value.find((o) => o.value === val)?.label || val;

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item",
      formatter: (params) => {
        // 解析扫参变量
        let paramHtml = "";
        if (params.data.params) {
          for (let k in params.data.params) {
            let v = params.data.params[k];
            paramHtml += `${k}: <span style="color:#3b82f6">${v % 1 !== 0 ? v.toFixed(3) : v}</span><br/>`;
          }
        }
        if (!paramHtml)
          paramHtml = "<span style='color: gray;'>等待数据传入...</span>";

        // 组装悬浮框
        return `<div style="font-family: monospace;">
                  <b>Sweep ID: ${params.data.id}</b><br/>
                  <hr style="margin:6px 0; border:0; border-top:1px solid rgba(255,255,255,0.1)" />
                  ${getLabel(scatterConfig.xAxis)}: <span style="color:#f59e0b">${params.value[0].toFixed(3)}</span><br/>
                  ${getLabel(scatterConfig.yAxis)}: <span style="color:#10b981">${params.value[1].toFixed(3)}</span><br/>
                  ${getLabel(scatterConfig.color)}: <span style="color:#ef4444">${params.value[2].toFixed(3)}</span><br/>
                  <hr style="margin:6px 0; border:0; border-top:1px dashed rgba(255,255,255,0.2)" />
                  <span style="font-size:12px; color:var(--n-text-color-3);">[当前扫描参数组合]</span><br/>
                  ${paramHtml}
                </div>`;
      },
    },
    grid: { top: 40, right: 80, bottom: 40, left: 60 }, // 右侧留出 80px 给颜色映射条
    xAxis: {
      name: getLabel(scatterConfig.xAxis),
      type: "value",
      scale: true,
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: "dashed" } },
    },
    yAxis: {
      name: getLabel(scatterConfig.yAxis),
      type: "value",
      scale: true,
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { color: gridColor, type: "dashed" } },
    },
    visualMap: {
      min: minColorVal,
      max: maxColorVal,
      dimension: 2,
      calculable: true,
      orient: "vertical",
      right: 0,
      top: "center",
      textStyle: { color: textColor },
      inRange: {
        // 冷色到暖色的经典科学映射
        color: [
          "#313695",
          "#4575b4",
          "#abd9e9",
          "#fee090",
          "#f46d43",
          "#a50026",
        ],
      },
    },
    series: [
      {
        type: "scatter",
        data: seriesData,
        symbolSize: 10,
        itemStyle: {
          opacity: 0.8,
          borderColor: "var(--n-card-color)",
          borderWidth: 1,
        },
      },
    ],
  };

  scatterChart.setOption(option, true);
};

// === 核心业务逻辑 (迁移自 CstOpt) ===

const triggerFileInput = async () => {
  try {
    const res = await axios.get(`${API_BASE}/browse_cst`);
    if (res.data.status === "success") {
      config.cstPath = res.data.path;
      fetchModelPreview();
      tryLoadConfig(config.cstPath);
    }
  } catch (err) {
    message.error("唤起资源管理器失败");
  }
};

const fetchModelPreview = async () => {
  if (!config.cstPath) return;
  isFetchingImage.value = true;
  try {
    const res = await axios.get(`${API_BASE}/get_model_image`, {
      params: { cst_path: config.cstPath },
      responseType: "blob",
    });
    if (modelImageUrl.value) URL.revokeObjectURL(modelImageUrl.value);
    modelImageUrl.value = URL.createObjectURL(res.data);
  } catch (e) {
    modelImageUrl.value = "";
  } finally {
    isFetchingImage.value = false;
  }
};

const connectWebSocket = (taskId) => {
  const ws = new WebSocket(`${WS_BASE}/progress/${taskId}`);
  ws.onmessage = async (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "sweep_progress") {
      currentSweepIdx.value = data.current;
      // 确保响应式赋值
      allDataPool[data.current] = data.data;

      if (
        currentSweepIdx.value === 1 ||
        inspectIdx.value === data.current - 1
      ) {
        inspectIdx.value = data.current;
        updateInspectorChart();
      }

      if (islandState && islandState.CstSweep.isRunning) {
        islandState.CstSweep.progress = totalCombinations.value
          ? Math.round((data.current / totalCombinations.value) * 100)
          : 0;
      }

      // 等待 DOM 更新后刷新散点图
      await nextTick();
      refreshScatterChart();

      //这里必须加 .value，否则脚本会在此处崩溃导致后续不执行
      logs.value.push(
        `[PROGRESS] 扫描组合 ${data.current}/${totalCombinations.value} 完成`,
      );
      scrollToBottom();
    } else if (data.type === "finish") {
      isRunning.value = false;
      if (islandState) islandState.CstSweep.isRunning = false;
      message.success("网格扫参任务全部完成！");
    }
  };
};

const startSweep = async () => {
  if (!config.cstPath) return message.error("路径不能为空");
  isRunning.value = true;

  if (islandState) {
    islandState.CstSweep.isRunning = true;
    islandState.CstSweep.taskName = config.taskName || "网格扫参任务";
    islandState.CstSweep.filePath = config.cstPath;
    islandState.CstSweep.progress = 0;
    islandState.CstSweep.abortFn = stopOptimization;
  }

  logs.value.push(
    "<span style='color:#10b981;'>[INFO]</span> 扫参任务已提交至后台...",
  );
  try {
    const res = await axios.post(`${API_BASE}/start_sweep`, config);
    if (res.data.status === "success") {
      currentTaskId.value = res.data.task_id; 
      connectWebSocket(res.data.task_id);
    }
  } catch (e) {
    isRunning.value = false;
    if (islandState) islandState.CstSweep.isRunning = false;
    message.error("任务启动失败");
  }
};

const stopOptimization = async () => {
  if (!currentTaskId.value) return;
  message.loading("正在向后台发送急停指令...");
  try {
    const res = await axios.post(
      `${API_BASE}/stop_optimization/${currentTaskId.value}`,
    );
    if (res.data.status === "success") {
      message.success("急停指令已下发！等待底层 CST 释放...");
      logs.value.push(
        "<span style='color:#ef4444;'>[SYSTEM] 收到强制终止指令，引擎将在当前点算完后安全退出...</span>",
      );
      scrollToBottom();
    } else {
      message.error(res.data.message);
    }
  } catch (e) {
    message.error("急停指令下发失败，请检查网络或后台状态");
  }
};

const sortParamsList = () => {
  config.paramsList.sort((a, b) => {
    if (a.isSweep === b.isSweep) return 0;
    return a.isSweep ? -1 : 1; // true 排在 false 前面
  });
};

// === 辅助函数 ===
const addVariable = () => {
  config.paramsList.push({
    id: Date.now().toString(),
    name: "new_var",
    min: 0,
    max: 1,
    val: 0.5,
    points: 5,
    isSweep: false,
  });
};
const removeVariable = (id) => {
  const idx = config.paramsList.findIndex((p) => p.id === id);
  if (idx !== -1) config.paramsList.splice(idx, 1);
};
const scrollToBottom = async () => {
  await nextTick();
  if (logWindowRef.value)
    logWindowRef.value.scrollTop = logWindowRef.value.scrollHeight;
};
const toggleFullscreen = (e) => {
  const card = e.currentTarget.closest(".chart-card");
  if (document.fullscreenElement) document.exitFullscreen();
  else card.requestFullscreen();
};

const handleResize = () => {
  if (inspectorChart) inspectorChart.resize();
  if (scatterChart) scatterChart.resize();
};

const handleFullscreenChange = () => {
  const isFullscreen = !!document.fullscreenElement;

  // 设定全屏和非全屏的字号大小
  const axisFontSize = isFullscreen ? 16 : 12;
  const tooltipFontSize = isFullscreen ? 18 : 13;

  const tc = getThemeColor();
  const gc = getGridColor();
  const dashStyle = { lineStyle: { color: gc, type: "dashed" } };

  const fontUpdateOption = {
    tooltip: { textStyle: { fontSize: tooltipFontSize } },
    xAxis: {
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle,
    },
    yAxis: {
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle,
    },
  };

  // 1. 更新波形图字号
  if (inspectorChart) inspectorChart.setOption(fontUpdateOption);

  // 2. 更新散点图字号及散点大小
  if (scatterChart) {
    scatterChart.setOption({
      ...fontUpdateOption,
      series: [{ symbolSize: isFullscreen ? 16 : 10 }], // 全屏散点变大
    });
  }

  // 触发重绘
  handleResize();
  setTimeout(handleResize, 100);
  setTimeout(handleResize, 300);
  setTimeout(handleResize, 600);
};

onMounted(async () => {
  fetchHistoryTasks();
  initCharts();
  window.addEventListener("resize", handleResize);
  document.addEventListener("fullscreenchange", handleFullscreenChange);

  try {
    const resTask = await axios.get(`${API_BASE}/get_running_task`);
    if (resTask.data.status === "success") {
      const activeTaskId = resTask.data.task_id;

      //只认 sweep_ 开头的任务
      if (activeTaskId.startsWith("sweep_")) {
        dialog.warning({
          title: "发现运行中的扫描任务",
          content: `系统检测到后台正在运行网格扫描 [${activeTaskId}]。您是要接管该任务的监控台，还是强制终止它？`,
          positiveText: "接管监控台",
          negativeText: "强制终止它",
          onPositiveClick: async () => {
            currentTaskId.value = activeTaskId; // 需要在顶层 ref 声明一个 currentTaskId
            isRunning.value = true;
            connectWebSocket(activeTaskId);

            // 接管任务时，同步通知外层 App.vue 唤醒灵动岛
            if (islandState) {
              islandState.CstSweep.isRunning = true;
              islandState.CstSweep.taskName = activeTaskId;
              islandState.CstSweep.filePath = config.cstPath || "恢复中...";
              islandState.CstSweep.progress = 0;
              islandState.CstSweep.abortFn = stopOptimization;
            }

            message.loading("🔄 正在恢复扫描进度与图表...");
            const resData = await axios.get(
              `${API_BASE}/get_task_data/${activeTaskId}`,
            );
            if (resData.data.status === "success") {
              const d = resData.data;

              if (d.config_json) Object.assign(config, d.config_json);

              // 1. 清空旧数据并解包
              Object.keys(allDataPool).forEach(k => delete allDataPool[k]);
              if (d.all_data_pool) {
                if (d.all_data_pool["1"] && !d.all_data_pool["1"].params && !d.all_data_pool["1"].metrics) {
                  Object.assign(allDataPool, d.all_data_pool["1"]);
                } else {
                  Object.assign(allDataPool, d.all_data_pool);
                }
              }

              // 2. 更新最高扫参进度索引
              const keys = Object.keys(allDataPool);
              if (keys.length > 0) {
                currentSweepIdx.value = Math.max(...keys.map(Number));
                inspectIdx.value = currentSweepIdx.value;
              }

              // 3. 推迟重绘
              await nextTick();
              refreshScatterChart();
              updateInspectorChart();
              message.success("✅ 扫描进度与波形已从数据库无损恢复！");
            }
          },
          onNegativeClick: async () => {
            message.loading("正在强制终止...");
            try {
              await axios.post(`${API_BASE}/stop_optimization/${activeTaskId}`);
              message.success("✅ 任务已清理");
            } catch (e) {
              message.error("清理失败");
            }
            isRunning.value = false;
          },
        });
      }
    }
  } catch (err) {}
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  
  if (inspectorResizeObserver) inspectorResizeObserver.disconnect();
  if (scatterResizeObserver) scatterResizeObserver.disconnect();
  
  if (inspectorChart) inspectorChart.dispose();
  if (scatterChart) scatterChart.dispose();
});
</script>

<style scoped>
/* ===== 基础容器与布局 ===== */
.cst-container {
  display: flex;
  height: 100vh;
  background-color: var(--n-body-color);
  color: var(--n-text-color);
}

/* 左侧控制台 (3比例) */
.sidebar {
  flex: 3;
  min-width: 350px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--n-border-color);
  background-color: var(--n-color);
  z-index: 10;
}
.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.vertical-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

/* 右侧主布局 (7比例) */
.main-content {
  flex: 7;
  padding: 24px;
  display: flex;
  flex-direction: column;
  background-color: var(--n-body-color);
  overflow: hidden;
}
.middle-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex: 1;
  min-height: 0;
}
.bottom-row {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* ===== 现代卡片质感 (发光/玻璃拟态) ===== */
.modern-card,
.metric-card,
.chart-card {
  border-radius: 8px;
  background-color: var(--n-card-color);
  /* 统一的光影风格 */
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
}
.modern-card {
  margin-bottom: 20px;
}

.card-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--n-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--n-action-color);
  border-radius: 8px 8px 0 0;
}
.card-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--n-text-color);
}

/* ===== 侧边栏表单细节 ===== */
.var-item {
  padding: 16px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  margin-bottom: 12px;
  background-color: var(--n-color);
}
.inner-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  font-weight: bold;
}
.sweep-row {
  padding-top: 12px;
  border-top: 1px dashed var(--n-border-color);
}
.step-hint {
  font-size: 11px;
  color: #3b82f6;
  text-align: right;
  margin-top: 6px;
  font-weight: bold;
}
.var-fix-row {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--n-border-color);
}
.inner-panel {
  padding: 16px;
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  margin-top: 8px;
}
.total-count-tag {
  margin-top: 12px;
  padding: 8px;
  text-align: center;
  background: rgba(59, 130, 246, 0.1);
  border: 1px dashed #3b82f6;
  border-radius: 4px;
}
.action-area {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid var(--n-border-color);
  background: transparent;
}
.start-btn {
  width: 100%;
  font-size: 16px;
  font-weight: bold;
  letter-spacing: 2px;
  border-radius: 8px;
  height: 50px;
}

/* ===== 右侧图表与字体细节 ===== */
.text-sub {
  color: var(--n-text-color-3);
}
.text-neon-blue {
  color: #3b82f6;
  font-weight: bold;
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-size: 20px;
  font-variant-numeric: tabular-nums;
}
.n-config-provider:not([theme="light"]) .text-neon-blue {
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}

/* 模型预览区 */
.model-preview-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--n-code-color);
  position: relative;
  overflow: hidden;
  min-height: 0;
  border-radius: 0 0 8px 8px;
}
.model-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.hologram-scanner {
  text-align: center;
  font-family: monospace;
  color: var(--n-text-color-3);
}

/* 波形参数标签区 */
.param-tags-container {
  display: flex;
  align-items: flex-start;
  width: 100%;
}
.param-tags-wrapper {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 52px;
  overflow-y: auto;
}

/* 日志终端区 */
.terminal-card {
  border-color: rgba(16, 185, 129, 0.3) !important;
}
.log-window {
  position: absolute;
  inset: 0;
  background-color: var(--n-code-color);
  padding: 12px;
  overflow-y: auto;
  font-family: "Consolas", monospace;
  font-size: 12px;
  color: var(--n-text-color);
  border-radius: 0 0 8px 8px;
  word-break: break-all;
  white-space: pre-wrap;
}
.log-window::-webkit-scrollbar {
  width: 6px;
}
.log-window::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.4);
  border-radius: 3px;
}
.log-item {
  margin-bottom: 6px;
  line-height: 1.4;
}
.log-prefix {
  color: #3b82f6;
  font-weight: bold;
  margin-right: 8px;
}

/* ===== 全屏亚克力拟态 ===== */
.chart-card:fullscreen {
  width: 100vw;
  height: 100vh !important;
  margin: 0 !important;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  z-index: 9999;
  padding: 16px;
  overflow: hidden;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}
.chart-card.light-mode:fullscreen {
  background-color: rgba(255, 255, 255, 0.4) !important;
}
.chart-card.dark-mode:fullscreen {
  background-color: rgba(24, 24, 28, 0.4) !important;
}
.chart-card:fullscreen::backdrop {
  background-color: transparent !important;
}

/* 打断内部组件的死锁限制 */
.chart-card,
:deep(.n-card__content) {
  min-width: 0 !important;
  min-height: 0 !important;
}

:deep(.n-form-item) {
  margin-bottom: 16px;
}
:deep(.n-form-item .n-form-item-label) {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 6px;
}
.chart-card:fullscreen .card-title {
  font-size: 20px !important;
}
.chart-card:fullscreen .text-sub {
  font-size: 16px !important;
}
.chart-card:fullscreen .n-radio-button {
  font-size: 16px !important;
}
.chart-card:fullscreen .n-select {
  font-size: 16px !important;
}
.chart-card:fullscreen .n-input-group-label {
  font-size: 16px !important;
}
.chart-card:fullscreen .param-tags-wrapper .n-tag {
  font-size: 16px !important;
  padding: 0 16px !important;
  height: auto !important;
  line-height: 1.5 !important;
}
.params-list-container {
  position: relative;
}

/* 确立移动过程中的过渡曲线 */
.list-anim-move,
.list-anim-enter-active,
.list-anim-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.list-anim-enter-from,
.list-anim-leave-to {
  opacity: 0;
  transform: translateY(15px) scale(0.98);
}

/* 确保离开的元素被移出文档流，这样其他元素才能顺滑补位 */
.list-anim-leave-active {
  position: absolute;
  width: 100%;
}
</style>
