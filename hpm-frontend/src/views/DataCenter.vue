<template>
  <div class="data-center-container">

    <div class="sidebar">
      <div class="sider-header">
        <n-h3 style="margin: 0; display: flex; align-items: center; gap: 8px;">
          <n-icon color="#3b82f6"><Database /></n-icon> 任务归档
        </n-h3>
        <n-button quaternary circle size="small" @click="fetchTasks">
          <n-icon><RefreshCw /></n-icon>
        </n-button>
      </div>

      <n-scrollbar style="flex: 1; min-height: 0;">
        <n-list hoverable clickable class="task-list">
          <n-list-item
            v-for="task in tasks"
            :key="task.id"
            :class="{ 'active-task': selectedTaskId === task.id }"
            @click="selectTask(task)"
          >
            <n-thing :title="task.name" :description="task.id">
              <template #suffix>
                <n-tag :type="getStatusType(task.status)" size="tiny" bordered="false">
                  {{ task.status }}
                </n-tag>
              </template>
              <div class="task-meta">
                <n-text depth="3" style="font-size: 12px;">{{ formatDate(task.created_at) }}</n-text>
              </div>
            </n-thing>
          </n-list-item>
        </n-list>
      </n-scrollbar>
    </div>

    <div class="main-content">
      <div v-if="selectedTask" class="detail-container">
        <div class="detail-header">
          <div>
            <n-h1 style="margin: 0;">{{ selectedTask.name }}</n-h1>
            <n-text depth="3">项目路径: {{ selectedTask.cst_path }}</n-text>
          </div>
          <n-space>
            <n-button type="primary" secondary @click="exportToExcel(selectedTask.id)">
              <template #icon><n-icon><Download /></n-icon></template> 导出 Excel
            </n-button>
            <n-popconfirm @positive-click="deleteTask(selectedTask.id)">
              <template #trigger>
                <n-button type="error" ghost>
                  <template #icon><n-icon><Trash2 /></n-icon></template> 彻底删除
                </n-button>
              </template>
              确定要删除该任务及其所有波形数据吗？此操作不可逆，将释放大量磁盘空间。
            </n-popconfirm>
          </n-space>
        </div>

        <n-grid :x-gap="16" :cols="4" style="margin: 24px 0;">
          <n-gi>
            <n-card size="small" title="总迭代代数" class="stat-card">
              <span class="stat-value">{{ selectedTaskStats.totalGens }}</span>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card size="small" title="历史冠军 (Top Score)" class="stat-card" style="padding-bottom: 4px;">
              <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; line-height: 1.2;">
                <span class="stat-value text-neon-white" style="font-size: 22px;">
                  {{ selectedTaskStats.topScore.toExponential(2) }}
                </span>
                <div style="display: flex; gap: 10px; font-size: 12px; margin-top: 6px; font-family: monospace; font-weight: bold; flex-wrap: wrap; justify-content: center;">
                  <span v-for="(val, key) in selectedTaskStats.bestMetrics" :key="key" class="text-neon-green">
                    {{ key }}: {{ typeof val === 'number' ? (val > 1000 ? val.toExponential(2) : val.toFixed(3)) : val }}
                  </span>
                </div>
              </div>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card size="small" title="样本总数" class="stat-card">
              <span class="stat-value">{{ selectedTaskStats.totalInds }}</span>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card size="small" title="数据库占用" class="stat-card">
              <span class="stat-value">{{ selectedTaskStats.storage }} MB</span>
            </n-card>
          </n-gi>
        </n-grid>

        <n-tabs type="card" animated style="background: var(--n-card-color); border: 1px solid var(--n-border-color); border-radius: 8px;">
          <n-tab-pane name="data" tab="详细数据列表" display-directive="show">
            <n-data-table
              :columns="columns"
              :data="individualData"
              :pagination="pagination"
              :bordered="false"
              striped
              style="padding: 0 16px 16px 16px;"
            />
          </n-tab-pane>
          <n-tab-pane name="config" tab="原始配置快照 (JSON)">
            <div class="json-code">
              <pre>{{ JSON.stringify(selectedTask.config_json, null, 2) }}</pre>
            </div>
          </n-tab-pane>
        </n-tabs>

        <n-drawer v-model:show="showWaveformModal" :width="720" placement="right" class="cyber-drawer">
          <n-drawer-content closable>
            <template #header>
              <div style="display: flex; align-items: center; gap: 12px;">
                <n-icon size="24" color="#10b981"><Activity /></n-icon>
                <span>个体 #{{ currentViewingInd?.ind_index }} 深度仿真档案</span>
              </div>
            </template>

            <n-card size="small" title="优化案例结构参数 (Params)" style="margin-bottom: 16px;">
              <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                <n-tag v-for="(v, k) in currentViewingInd?.params_json" :key="k" type="info" bordered="false">
                  {{ k }}: <span style="font-weight: bold; margin-left: 4px;">{{ v }}</span>
                </n-tag>
              </div>
            </n-card>

            <n-card size="small" title="📈 时频域联合分析">
              <n-tabs 
                v-if="Object.keys(fetchedWaves).length > 0" 
                v-model:value="activeWaveTab" 
                type="segment" 
                animated 
                @update:value="renderSelectedWave"
              >
                <n-tab-pane v-if="fetchedWaves.power" name="power" tab="输出功率 (Power)"></n-tab-pane>
                <n-tab-pane v-if="fetchedWaves.eff" name="eff" tab="转换效率 (Efficiency)"></n-tab-pane>
                <n-tab-pane v-if="fetchedWaves.mode" name="mode" tab="主模包络 (Main Mode)"></n-tab-pane>
                <n-tab-pane v-if="fetchedWaves.fft" name="fft" tab="频谱分析 (FFT)"></n-tab-pane>
              </n-tabs>
              
              <div v-else style="padding: 40px; text-align: center; color: gray;">该个体未记录任何波形数据</div>

              <div ref="waveformChartRef" style="height: 400px; width: 100%; margin-top: 16px;" v-show="Object.keys(fetchedWaves).length > 0"></div>
            </n-card>

            <template #footer>
              <n-text depth="3" style="font-size: 12px;">数据库 ID: {{ currentViewingInd?.id }} | 提取自 waveforms 表</n-text>
            </template>
          </n-drawer-content>
        </n-drawer>

      </div>

      <div v-else class="empty-placeholder">
        <n-empty description="请在左侧选择一个任务以查阅历史数据">
          <template #icon><n-icon><Database /></n-icon></template>
        </n-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { NIcon, useMessage, NButton, NTag } from 'naive-ui'
import { ref, onMounted, reactive, h, nextTick, onUnmounted } from 'vue'
import { Database, RefreshCw, Download, Trash2, Activity } from 'lucide-vue-next'
import axios from 'axios'
import * as echarts from 'echarts'

const message = useMessage()
const API_BASE = '/api';
const tooltipFrostedGlass = {
  backgroundColor: 'rgba(15, 23, 42, 0.65)',
  borderColor: 'rgba(255, 255, 255, 0.15)',
  borderWidth: 1,
  textStyle: { color: '#e2e8f0' },
  extraCssText: 'backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5); border-radius: 8px;'
};

const tasks = ref([])
const selectedTaskId = ref(null)
const selectedTask = ref(null)
const individualData = ref([])
const selectedTaskStats = reactive({ 
  totalGens: 0, 
  topScore: 0, 
  bestMetrics: {}, // ✨ 替代以前写死的 topEff 等
  totalInds: 0, 
  storage: 0 
})

const showWaveformModal = ref(false)
const waveformChartRef = ref(null)
const currentViewingInd = ref(null)
let waveformChart = null

const fetchedWaves = ref({}) 
const activeWaveTab = ref('') 

// ✨ 将 columns 改为响应式，实现动态表头
const columns = ref([])

const fetchAndShowWaveform = async (individualId) => {
  try {
    message.loading("正在解析物理波形序列...", { duration: 800 })
    const res = await axios.get(`${API_BASE}/individuals/${individualId}/waveform`)
    
    if (res.data.status === 'success') {
      fetchedWaves.value = res.data.waveforms || {} // ✨ 直接收纳后端的全量动态字典
      const availableKeys = Object.keys(fetchedWaves.value)
      if (availableKeys.length > 0) activeWaveTab.value = availableKeys[0]

      showWaveformModal.value = true
      
      nextTick(() => {
        if (waveformChartRef.value) {
          if (waveformChart != null) waveformChart.dispose()
          waveformChart = echarts.init(waveformChartRef.value)
          if (availableKeys.length > 0) renderSelectedWave(activeWaveTab.value)
        }
      })
    }
  } catch (e) { message.error("波形库调取失败 (可能未起振或提取异常)") }
}

const renderSelectedWave = (type) => {
  if (!waveformChart || !fetchedWaves.value[type]) return

  const data = fetchedWaves.value[type]
  let timeData = []
  let valueData = []

  // 泛化解析 {x: [...], y: [...]}
  if (data && data.x && data.y && Array.isArray(data.x)) {
    timeData = data.x
    valueData = data.y
  } 

  waveformChart.clear();
  waveformChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, ...tooltipFrostedGlass },
    grid: { left: '8%', right: '5%', bottom: '12%', top: '15%', containLabel: true },
    dataZoom: [{ type: 'inside' }],
    xAxis: { type: 'category', name: '自变量', nameLocation: 'middle', nameGap: 25, data: timeData },
    yAxis: { type: 'value', name: type, splitLine: { lineStyle: { type: 'dashed', color: '#333' } }, scale: true },
    series: [{
      type: 'line', data: valueData, smooth: true, showSymbol: false,
      lineStyle: { width: 2, color: '#10b981' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#10b98160' },
          { offset: 1, color: '#10b98100' }
        ])
      }
    }]
  }, true)
}

const fetchTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/tasks`);
    tasks.value = res.data.tasks ? res.data.tasks : res.data;
  } catch (e) {
    message.error(`数据获取失败`);
  }
}

const selectTask = async (task) => {
  selectedTaskId.value = task.id
  selectedTask.value = task
  try {
    const res = await axios.get(`${API_BASE}/tasks/${task.id}/individuals`)
    const inds = Array.isArray(res.data) ? res.data : (res.data.individuals || [])
    individualData.value = inds

    if (res.data.stats) {
      selectedTaskStats.totalGens = res.data.stats.totalGens
      selectedTaskStats.totalInds = res.data.stats.totalInds
      selectedTaskStats.storage = res.data.stats.storage
    }

    // ✨ 动态生成表格的列 (Base Columns + Dynamic Metrics)
    const baseCols = [
      { title: '代数', key: 'gen_index', width: 80, sorter: 'default' },
      { title: '编号', key: 'ind_index', width: 80 },
      {
        title: '物理参数 (Params)', key: 'params_json', width: 220,
        render(row) {
          if (!row.params_json) return h('span', { style: 'color: gray' }, '--')
          return h('div', { style: 'display: flex; gap: 4px; flex-wrap: wrap;' },
            Object.entries(row.params_json).map(([k, v]) =>
              h(NTag, { size: 'small', type: 'info', bordered: false }, { default: () => `${k}: ${v}` })
            )
          )
        }
      },
      { 
        title: '综合得分', key: 'score', width: 110, 
        render: (row) => (row.score || 0).toExponential(2),
        sorter: (row1, row2) => (row1.score || 0) - (row2.score || 0) 
      }
    ];

    let dynamicCols = [];
    if (inds.length > 0) {
      // 找出当前任务里 Metrics 最全的个体作为模板（防空）
      const sampleInd = inds.find(i => i.metrics_json && Object.keys(i.metrics_json).length > 0) || inds[0];
      const metrics = sampleInd.metrics_json || {};
      
      dynamicCols = Object.keys(metrics).map(k => ({
        title: k,
        key: `metrics_json.${k}`,
        width: 100,
        render: (row) => {
           const val = row.metrics_json?.[k];
           return val !== undefined ? (val > 1000 ? Number(val).toExponential(2) : Number(val).toFixed(2)) : '--';
        },
        sorter: (a, b) => (a.metrics_json?.[k] || 0) - (b.metrics_json?.[k] || 0)
      }));

      // 提取最佳分数和最佳指标
      const bestInd = inds.reduce((prev, current) => ((prev.score || -1e12) > (current.score || -1e12)) ? prev : current);
      selectedTaskStats.topScore = bestInd.score || 0;
      selectedTaskStats.bestMetrics = bestInd.metrics_json || {};
    } else {
      selectedTaskStats.topScore = 0; selectedTaskStats.bestMetrics = {};
    }

    const actionCol = {
      title: '操作', key: 'actions', width: 90, fixed: 'right',
      render(row) {
        return h(NButton, {
          size: 'small', type: 'primary', secondary: true,
          onClick: () => { currentViewingInd.value = row; fetchAndShowWaveform(row.id); }
        }, { default: () => '看波形' })
      }
    };

    columns.value = [...baseCols, ...dynamicCols, actionCol];

  } catch (e) {
    message.error("无法读取任务明细数据")
  }
}

onUnmounted(() => {
  if (waveformChart) { waveformChart.dispose(); waveformChart = null }
})

const deleteTask = async (id) => {
  try {
    await axios.delete(`${API_BASE}/tasks/${id}`)
    message.success("任务已永久删除")
    selectedTask.value = null
    fetchTasks()
  } catch (e) { message.error("删除失败") }
}

const exportToExcel = (id) => {
  message.info("准备导出...");
  window.open(`${API_BASE}/tasks/${id}/export`)
}

const getStatusType = (s) => s === 'completed' ? 'success' : (s === 'error' ? 'error' : 'info')
const formatDate = (d) => new Date(d).toLocaleString()

onMounted(() => { fetchTasks() })
</script>

<style scoped>
.data-center-container {
  display: flex;
  height: calc(100vh - 60px);
  background-color: var(--n-body-color);
  color: var(--n-text-color);
}

.sidebar {
  width: 320px;
  flex-shrink: 0;
  border-right: 1px solid var(--n-border-color);
  background-color: var(--n-color);
  display: flex;
  flex-direction: column;
}
.sider-header {
  padding: 20px;
  border-bottom: 1px solid var(--n-border-color);
  display: flex; justify-content: space-between; align-items: center;
}
.task-list { padding: 12px; background: transparent; }
.active-task { background-color: var(--n-action-color) !important; border-radius: 8px; }
.task-meta { margin-top: 6px; }

.main-content {
  flex: 1;
  padding: 32px;
  overflow-y: auto;
  min-width: 0;
}

.detail-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.stat-card { 
  border-radius: 8px; 
  text-align: center; 
  background-color: var(--n-card-color); 
  /* 👇 质感升级 */
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
}
.stat-value, .text-neon-white, .text-neon-green, .text-neon-orange, .text-neon-blue {
  font-family: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', Consolas, monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}

.stat-value { font-size: 28px; font-weight: 800; }
.text-neon-green { color: #10b981; }

.json-code {
  background: var(--n-code-color);
  padding: 16px;
  border-radius: 0 0 8px 8px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Roboto Mono', Consolas, monospace;
  color: var(--n-text-color);
  overflow-x: auto;
}
.empty-placeholder { height: 100%; display: flex; align-items: center; justify-content: center; }
.text-neon-white { color: var(--n-text-color); font-weight: 900; }
.text-neon-orange { color: #f59e0b; }
.text-neon-blue { color: #3b82f6; }

</style>
<style>
/* 1. 抽屉主体 */
.cyber-drawer.n-drawer {
  background-color: rgba(10, 12, 16, 0.85) !important;
  border-left: 1px solid rgba(16, 185, 129, 0.4) !important; 
  box-shadow: -15px 0 40px rgba(0, 0, 0, 0.6), inset 0 0 80px rgba(16, 185, 129, 0.05) !important;
}

/* 2. 抽屉内容区去色 */
.cyber-drawer .n-drawer-content {
  background: transparent !important;
}

/* 3. 头部去色与分割线弱化 */
.cyber-drawer .n-drawer-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
  background: transparent !important;
}

/* 4. 抽屉内部的卡片组件幽灵化 */
.cyber-drawer .n-card {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.5) !important;
}
</style>