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
                  <span v-if="selectedTask?.config_json?.targets?.eff?.enable" class="text-neon-green">
                    Eff: {{ selectedTaskStats.topEff.toFixed(2) }}%
                  </span>
                  <span v-if="selectedTask?.config_json?.targets?.power?.enable" class="text-neon-orange">
                    P: {{ (selectedTaskStats.topPower / 1e6).toFixed(2) }}MW
                  </span>
                  <span v-if="selectedTask?.config_json?.targets?.freq?.enable" class="text-neon-blue">
                    F: {{ selectedTaskStats.topFreq.toFixed(3) }}G
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
// ✨ 引入 nextTick 用于等待弹窗渲染完成
import { NIcon, useMessage, NButton, NTag } from 'naive-ui' // ✨ 修复 1：必须导入 NTag
import { ref, onMounted, reactive, h, nextTick, onUnmounted } from 'vue' // ✨ 修复 2：导入 onUnmounted
import { Database, RefreshCw, Download, Trash2, Activity } from 'lucide-vue-next'
import axios from 'axios'
import * as echarts from 'echarts'

const message = useMessage()
const API_BASE = '/api';
const tooltipFrostedGlass = {
  backgroundColor: 'rgba(15, 23, 42, 0.65)', // 深色半透明背景
  borderColor: 'rgba(255, 255, 255, 0.15)',  // 极细的高光边框
  borderWidth: 1,
  textStyle: { color: '#e2e8f0' }, // 柔和的文字颜色
  // 核心：CSS 滤镜实现毛玻璃模糊效果 + 悬浮阴影
  extraCssText: 'backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); box-shadow: 0 8px 16px rgba(0, 0, 0, 0.5); border-radius: 8px;'
};
// 状态
const tasks = ref([])
const selectedTaskId = ref(null)
const selectedTask = ref(null)
const individualData = ref([])
const selectedTaskStats = reactive({ 
  totalGens: 0, 
  topScore: 0, 
  topEff: 0, 
  topPower: 0, 
  topFreq: 0, 
  totalInds: 0, 
  storage: 0 
})

// ✨ 原生图表引用
const showWaveformModal = ref(false)
const waveformChartRef = ref(null)
const currentViewingInd = ref(null) // 追踪当前查看的个体
let waveformChart = null

const fetchedWaves = ref({}) // 动态存储后端返回的所有波形
const activeWaveTab = ref('') // 当前选中的波形 Tab

// 表格配置
// 表格配置 (✨ 包含全列动态排序与全维数据展示)
const columns = [
  { title: '代数 (Gen)', key: 'gen_index', width: 90, sorter: 'default' },
  { title: '编号 (No.)', key: 'ind_index', width: 90 },
  
  // 物理参数组合 (带防空校验)
  {
    title: '物理参数组合 (Params)',
    key: 'params_json',
    width: 240,
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
    // ✨ 增加 (row.score || 0) 防空保护，防止旧数据 null 导致表格崩溃
    render: (row) => (row.score || 0).toExponential(2),
    sorter: (row1, row2) => (row1.score || 0) - (row2.score || 0) 
  },
  { 
    title: '效率 (%)', key: 'eff_val', width: 100, 
    render: (row) => (row.eff_val || 0).toFixed(2),
    sorter: (row1, row2) => (row1.eff_val || 0) - (row2.eff_val || 0) 
  },
  { 
    title: '功率 (MW)', key: 'power_val', width: 110, 
    render: (row) => ((row.power_val || 0) / 1e6).toFixed(2),
    sorter: (row1, row2) => (row1.power_val || 0) - (row2.power_val || 0) 
  },
  { 
    title: '频率 (GHz)', key: 'freq_val', width: 110, 
    render: (row) => (row.freq_val || 0).toFixed(3),
    sorter: (row1, row2) => (row1.freq_val || 0) - (row2.freq_val || 0) 
  },

  {
    title: '操作',
    key: 'actions',
    width: 100,
    fixed: 'right',
    render(row) {
      return h(NButton, {
        size: 'small',
        type: 'primary',
        secondary: true,
        onClick: () => {
          currentViewingInd.value = row;
          fetchAndShowWaveform(row.id);
        }
      }, { default: () => '查看波形' })
    }
  }
]
const pagination = { pageSize: 15 }

// 方法
const fetchAndShowWaveform = async (individualId) => {
  try {
    message.loading("正在解析物理波形序列...", { duration: 800 })
    const res = await axios.get(`${API_BASE}/individuals/${individualId}/waveform`)
    
    if (res.data.status === 'success') {
      fetchedWaves.value = {}
      const backendWaves = res.data.waveforms || {}
      
      // 动态映射数据库字段：只要后端有，前端就显示
      if (backendWaves.power_wave) fetchedWaves.value.power = backendWaves.power_wave
      if (backendWaves.eff_wave) fetchedWaves.value.eff = backendWaves.eff_wave
      if (backendWaves.main_mode_wave) fetchedWaves.value.mode = backendWaves.main_mode_wave
      if (backendWaves.fft_wave) fetchedWaves.value.fft = backendWaves.fft_wave
      
      // 单波形兼容逻辑 (兼容旧版数据)
      if (res.data.time_series && !backendWaves.power_wave) fetchedWaves.value.power = res.data.time_series

      // 默认激活第一个存在的波形
      const availableKeys = Object.keys(fetchedWaves.value)
      if (availableKeys.length > 0) activeWaveTab.value = availableKeys[0]

      showWaveformModal.value = true
      
      nextTick(() => {
        if (waveformChartRef.value) {
          if (waveformChart != null) waveformChart.dispose() // 彻底销毁旧实例，解决白屏 Bug
          waveformChart = echarts.init(waveformChartRef.value)
          if (availableKeys.length > 0) renderSelectedWave(activeWaveTab.value)
        }
      })
    }
  } catch (e) { message.error("波形库调取失败") }
}

// ✨ 画布渲染引擎：根据选择的数据类型自动调整视觉样式
const renderSelectedWave = (type) => {
  if (!waveformChart || !fetchedWaves.value[type]) return

  const data = fetchedWaves.value[type]
  let timeData = []
  let valueData = []

  // 👇👇👇 核心修复：解析对象格式 {x: [...], y: [...]} 以及物理量级转换 👇👇👇
  if (data && data.x && data.y && Array.isArray(data.x)) {
    timeData = data.x
    
    // 物理单位转换：与 Y 轴单位匹配
    if (type === 'power') {
      // 数据库存的是 W，图表需要 MW
      valueData = data.y.map(v => v / 1e6) 
    } else if (type === 'eff') {
      // 数据库存的是小数，图表需要百分比 (%)
      valueData = data.y.map(v => v * 100) 
    } else {
      valueData = data.y
    }
  } 
  // 兼容极早期的旧版数据格式 (二维数组或对象数组)
  else if (Array.isArray(data) && data.length > 0) {
    if (data[0].name !== undefined) {
      timeData = data.map(item => item.name)
      valueData = data.map(item => item.value)
    } else if (Array.isArray(data[0])) {
      timeData = data.map(item => item[0])
      valueData = data.map(item => item[1])
    }
  }

  // 物理量视觉映射方案
  const themes = {
    power: { name: '功率 (MW)', color: '#10b981', x: '时间 (ns)' },
    eff: { name: '转换效率 (%)', color: '#f59e0b', x: '时间 (ns)' },
    mode: { name: '场强幅度', color: '#8b5cf6', x: '时间 (ns)' },
    fft: { name: '谱线强度', color: '#3b82f6', x: '频率 (GHz)' }
  }
  const config = themes[type] || themes.power

  waveformChart.clear(); // 切换时先清空画板
  waveformChart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' }, ...tooltipFrostedGlass },
    grid: { left: '8%', right: '5%', bottom: '12%', top: '15%', containLabel: true },
    dataZoom: [{ type: 'inside' }],
    xAxis: { type: 'category', name: config.x, nameLocation: 'middle', nameGap: 25, data: timeData },
    yAxis: { type: 'value', name: config.name, splitLine: { lineStyle: { type: 'dashed', color: '#333' } }, scale: true },
    series: [{
      type: 'line', data: valueData, smooth: true, showSymbol: false,
      lineStyle: { width: 2, color: config.color },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: config.color + '60' },
          { offset: 1, color: config.color + '00' }
        ])
      }
    }]
  }, true)
}

const fetchTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/tasks`);
    // ✨ 修复：兼容 FastAPI 返回的 {"status": "success", "tasks": [...]} 结构
    tasks.value = res.data.tasks ? res.data.tasks : res.data;
  } catch (e) {
    console.error("【后端接口报错】获取任务列表失败:", e);
    
    if (e.response && e.response.status === 404) {
      message.warning("未找到 /tasks 接口，正在自动回退到 /recent_tasks...");
      // 🚀 自动回退方案：如果后端还没写 /tasks，自动用主页的 /recent_tasks 顶上
      try {
        const fallback = await axios.get(`${API_BASE}/recent_tasks`);
        tasks.value = fallback.data.tasks ? fallback.data.tasks : fallback.data;
      } catch (err) {
        message.error("备用接口也失败了，请检查后端 FastAPI 是否正常运行。");
      }
    } else {
      // 真实显示究竟是什么错（跨域被拦截？断网？500？）
      message.error(`数据获取失败: ${e.message}`);
    }
  }
}

const selectTask = async (task) => {
  selectedTaskId.value = task.id
  selectedTask.value = task
  try {
    const res = await axios.get(`${API_BASE}/tasks/${task.id}/individuals`)
    
    // 兼容可能存在的不同数据结构包装
    const inds = Array.isArray(res.data) ? res.data : (res.data.individuals || [])
    individualData.value = inds

    if (res.data.stats) {
      selectedTaskStats.totalGens = res.data.stats.totalGens
      selectedTaskStats.totalInds = res.data.stats.totalInds
      selectedTaskStats.storage = res.data.stats.storage
    }

    // ✨ 核心逻辑：从本任务所有个体中，揪出综合得分 (Score) 最高的王者
    if (inds.length > 0) {
      const bestInd = inds.reduce((prev, current) => 
        ((prev.score || -1e7) > (current.score || -1e7)) ? prev : current
      );
      
      selectedTaskStats.topScore = bestInd.score || 0;
      selectedTaskStats.topEff = bestInd.eff_val || 0;
      selectedTaskStats.topPower = bestInd.power_val || 0;
      selectedTaskStats.topFreq = bestInd.freq_val || 0;
    } else {
      selectedTaskStats.topScore = 0; selectedTaskStats.topEff = 0;
      selectedTaskStats.topPower = 0; selectedTaskStats.topFreq = 0;
    }
  } catch (e) {
    message.error("无法读取任务明细数据")
  }
}

onUnmounted(() => {
  if (waveformChart) {
    waveformChart.dispose()
    waveformChart = null
  }
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

onMounted(() => {
  fetchTasks()
})
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