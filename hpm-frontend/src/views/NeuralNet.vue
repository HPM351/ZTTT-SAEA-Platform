<template>
  <div class="cst-container" :class="isDarkMode ? 'dark-mode' : 'light-mode'">
    <div class="sidebar">
      <div class="sidebar-header">
        <n-space align="center">
          <h2
            style="
              margin: 0;
              font-weight: 700;
              letter-spacing: 1px;
              display: flex;
              align-items: center;
              gap: 8px;
            "
          >
            <n-icon color="#10b981"><BrainCircuit /></n-icon>
            代理辅助平台
          </h2>
        </n-space>
        <n-space align="center">
          <n-tag
            :type="isRunning ? 'primary' : 'default'"
            round
            :bordered="false"
            size="large"
          >
            {{ isRunning ? "AI 引擎运转中" : "系统空闲" }}
          </n-tag>
        </n-space>
      </div>

      <n-scrollbar style="flex: 1; min-height: 0; padding-right: 16px">
        <n-form label-placement="top" :show-feedback="false">
          <n-card class="modern-card" size="small">
            <template #header>
              <span
                class="card-title"
                style="display: flex; align-items: center; gap: 6px"
              >
                <n-icon><Network /></n-icon> 在线微调 (Online Learning)
              </span>
            </template>
            <template #header-extra
              ><n-switch v-model:value="config.online.enable" size="small"
            /></template>
            <div v-if="config.online.enable" class="inner-panel">
              <div
                style="
                  font-size: 12px;
                  color: var(--n-text-color-3);
                  margin-bottom: 12px;
                "
              >
                <b>Top-K 强验证策略</b>:
                强制验证高分个体，并结合经验回放机制微调网络。
              </div>
              <n-form-item label="每代验证样本数 (K)"
                ><n-input-number
                  v-model:value="config.online.kSamples"
                  :min="1"
                  :max="100"
              /></n-form-item>
              <n-form-item label="📂 CST 项目路径"
                ><n-input
                  v-model:value="config.online.cstPath"
                  placeholder="请输入完整的 .cst 路径"
              /></n-form-item>

              <n-form-item
                v-if="optimizableTargets.some((t) => t.name === 'Efficiency')"
                label="效率结果路径 (EFF Path)"
              >
                <n-input v-model:value="config.online.effPath" />
              </n-form-item>
              <n-form-item
                v-if="optimizableTargets.some((t) => t.name === 'Power')"
                label="功率结果路径 (Power Path)"
              >
                <n-input v-model:value="config.online.powerPath" />
              </n-form-item>
              <n-form-item
                v-if="hasFrequencyTarget"
                label="频率结果路径 (FFT Path)"
              >
                <n-input v-model:value="config.online.freqPath" />
              </n-form-item>
            </div>
            <div
              v-else
              style="
                padding: 12px;
                text-align: center;
                color: var(--n-text-color-3);
                font-size: 13px;
              "
            >
              纯离线预测模式 (高速探索)
            </div>
          </n-card>

          <n-card class="modern-card" size="small" style="margin-top: 16px">
            <template #header>
              <span
                class="card-title"
                style="display: flex; align-items: center; gap: 6px"
              >
                <n-icon><Settings2 /></n-icon> 进化策略 (Evolution Strategy)
              </span>
            </template>
            <n-form-item>
              <template #label
                >自适应变异机制
                <n-tooltip trigger="hover"
                  ><template #trigger
                    ><span style="cursor: help; margin-left: 4px"
                      >❔</span
                    ></template
                  >均匀(探索) -> 布雷德(局部) -> 降低变异率(微调)</n-tooltip
                ></template
              >
              <n-switch v-model:value="config.algo.useAdaptiveMut">
                <template #checked>自适应阶段切换: 开</template>
                <template #unchecked>自适应阶段切换: 关</template>
              </n-switch>
            </n-form-item>
            <div
              v-if="config.algo.useAdaptiveMut"
              style="
                padding: 12px;
                background: rgba(0, 0, 0, 0.15);
                border-radius: 8px;
                border: 1px dashed var(--n-border-color);
              "
            >
              <div
                style="
                  display: flex;
                  justify-content: space-between;
                  font-size: 12px;
                  margin-bottom: 8px;
                "
              >
                <div style="color: #3b82f6; font-weight: bold">
                  探索 ({{ Math.round(config.algo.mutPhases[0] * 100) }}%)
                </div>
                <div style="color: #10b981; font-weight: bold">收敛</div>
                <div style="color: #f59e0b; font-weight: bold">
                  微调 ({{ Math.round(100 - config.algo.mutPhases[1] * 100) }}%)
                </div>
              </div>
              <n-slider
                v-model:value="config.algo.mutPhases"
                range
                :step="0.05"
                :min="0"
                :max="1"
              />
            </div>
            <n-collapse style="margin-top: 16px">
              <n-collapse-item title="基础遗传算子配置" name="basic">
                <n-grid :x-gap="12" :y-gap="4" :cols="2">
                  <n-gi
                    ><n-form-item label="种群大小 (Pop)"
                      ><n-input-number
                        v-model:value="config.algo.popSize"
                        :min="5"
                        :max="500" /></n-form-item
                  ></n-gi>
                  <n-gi
                    ><n-form-item label="进化代数 (Gen)"
                      ><n-input-number
                        v-model:value="config.algo.nGen"
                        :min="1"
                        :max="500" /></n-form-item
                  ></n-gi>
                  <n-gi
                    ><n-form-item label="交叉率 (PC)"
                      ><n-input-number
                        v-model:value="config.algo.pc"
                        :step="0.05"
                        :min="0"
                        :max="1"
                        :show-button="false" /></n-form-item
                  ></n-gi>
                  <n-gi
                    ><n-form-item label="变异率 (PM)"
                      ><n-input-number
                        v-model:value="config.algo.pm"
                        :step="0.05"
                        :min="0"
                        :max="1"
                        :show-button="false" /></n-form-item
                  ></n-gi>
                </n-grid>
              </n-collapse-item>
            </n-collapse>
          </n-card>
        </n-form>
        <n-card
          v-if="isModelLoaded"
          class="modern-card"
          size="small"
          style="margin-bottom: 16px"
        >
          <template #header>
            <span
              class="card-title"
              style="display: flex; align-items: center; gap: 6px"
            >
              <n-icon><Cpu /></n-icon> 模型结构与精度
            </span>
          </template>
          <n-descriptions
            label-placement="top"
            size="small"
            :column="2"
            bordered
          >
            <n-descriptions-item label="拓扑结构" :span="2">
              <div
                v-if="currentModelConfig?.meta?.topology?.includes('Shared')"
                style="display: flex; flex-direction: column"
              >
                <div
                  style="
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    background: rgba(255, 255, 255, 0.05);
                    padding: 8px;
                    border-radius: 6px;
                  "
                >
                  <n-tag type="info" size="small" :bordered="false" strong>
                    输入 ({{
                      currentModelConfig.meta.topology.split("-")[0]
                    }}维)
                  </n-tag>
                  <span style="color: var(--n-text-color-3); font-weight: bold"
                    >➔</span
                  >
                  <n-tag type="success" size="small" :bordered="false" strong>
                    主干:
                    {{
                      currentModelConfig.meta.topology.match(
                        /\((.*?)\)/,
                      )?.[1] || "..."
                    }}
                  </n-tag>
                </div>

                <div style="display: flex; align-items: flex-start; gap: 8px">
                  <div
                    style="
                      width: 20px;
                      height: 25px;
                      border-left: 2px solid var(--n-border-color);
                      border-bottom: 2px solid var(--n-border-color);
                      border-bottom-left-radius: 6px;
                      margin-left: 16px;
                      margin-top: -4px;
                    "
                  ></div>
                  <div
                    style="
                      display: flex;
                      flex-wrap: wrap;
                      gap: 6px;
                      padding-top: 10px;
                      flex: 1;
                    "
                  >
                    <n-tag size="tiny" type="warning" :bordered="false"
                      >分类头</n-tag
                    >
                    <n-tag
                      v-for="out in currentModelConfig.outputs"
                      :key="out.name"
                      size="tiny"
                      type="primary"
                      :bordered="false"
                    >
                      回归 ({{ out.display.split("(")[0] }})
                    </n-tag>
                  </div>
                </div>
              </div>
              <span v-else>{{
                currentModelConfig?.meta?.topology ?? "--"
              }}</span>
            </n-descriptions-item>

            <n-descriptions-item label="激活函数" :span="2">
              <div
                v-if="currentModelConfig?.meta?.activation?.includes('/')"
                style="
                  display: flex;
                  gap: 8px;
                  align-items: center;
                  justify-content: center;
                "
              >
                <n-tag size="small" type="default" :bordered="false">
                  主干:
                  {{ currentModelConfig.meta.activation.split("/")[0].trim() }}
                </n-tag>
                <span style="color: var(--n-text-color-3); font-size: 14px"
                  >+</span
                >
                <n-tag size="small" type="error" :bordered="false">
                  输出:
                  {{ currentModelConfig.meta.activation.split("/")[1].trim() }}
                </n-tag>
              </div>
              <span v-else>{{
                currentModelConfig?.meta?.activation ?? "--"
              }}</span>
            </n-descriptions-item>

            <n-descriptions-item label="训练损失 (Loss)" :span="1">
              <span style="font-family: monospace; font-size: 14px">
                {{ currentModelConfig?.meta?.train_loss ?? "--" }}
              </span>
            </n-descriptions-item>

            <n-descriptions-item
              :label="
                '评估 (' + (currentModelConfig?.meta?.metric_name ?? 'R²') + ')'
              "
              :span="1"
            >
              <span
                class="text-neon-green"
                style="
                  font-weight: bold;
                  font-size: 18px;
                  font-family: monospace;
                "
              >
                {{
                  currentModelConfig?.meta?.metric_value ??
                  currentModelConfig?.meta?.r2 ??
                  "--"
                }}
              </span>
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <n-card
          v-if="isModelLoaded"
          class="modern-card"
          size="small"
          style="margin-top: 16px"
        >
          <template #header>
            <div
              style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                width: 100%;
              "
            >
              <span
                class="card-title"
                style="display: flex; align-items: center; gap: 6px"
              >
                全局参数敏感度 (Gradient Sensitivity)
              </span>
              <n-button
                quaternary
                circle
                size="small"
                @click="toggleFullscreen"
                title="全屏查看"
                ><n-icon><Maximize /></n-icon
              ></n-button>
            </div>
          </template>
          <div
            ref="globalImportanceChartRef"
            class="echarts-container"
            style="width: 100%; height: 320px"
          >
            <span style="color: gray; font-size: 12px"
              >图表占位区：等待 ECharts 渲染</span
            >
          </div>
        </n-card>

        <n-card
          v-if="optimizableTargets.length > 0"
          class="modern-card"
          size="small"
          style="margin-top: 16px"
        >
          <template #header>
            <span
              class="card-title"
              style="display: flex; align-items: center; gap: 6px"
            >
              <n-icon><Target /></n-icon> 演化寻优目标 (自适应)
            </span>
          </template>

          <div
            v-if="hasFrequencyTarget"
            style="
              margin-bottom: 16px;
              padding: 12px;
              background: rgba(16, 185, 129, 0.1);
              border-radius: 8px;
              border: 1px solid rgba(16, 185, 129, 0.3);
            "
          >
            <div
              style="
                font-size: 13px;
                font-weight: bold;
                color: #10b981;
                margin-bottom: 8px;
                display: flex;
                justify-content: space-between;
              "
            >
              <span>频点锁定 (Target)</span>
            </div>
            <n-input-number
              v-model:value="config.algo.targetFreq"
              :step="0.01"
              size="small"
            >
              <template #suffix>GHz</template>
            </n-input-number>
          </div>

          <div
            v-for="(out, index) in optimizableTargets"
            :key="index"
            style="margin-bottom: 16px"
          >
            <div
              style="
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                margin-bottom: 4px;
              "
            >
              <span>
                {{ out.display }}
                <span
                  v-if="out.name.toLowerCase().includes('freq')"
                  style="color: var(--n-text-color-3)"
                  >(逼近权重)</span
                >
                <span v-else style="color: var(--n-text-color-3)"
                  >(最大化权重)</span
                >
              </span>
              <span
                :style="{
                  color:
                    index === 0
                      ? '#10b981'
                      : index === 1
                        ? '#3b82f6'
                        : '#f59e0b',
                  fontWeight: 'bold',
                }"
              >
                {{ config.algo.weights[out.name] || 0 }}%
              </span>
            </div>
            <n-slider
              v-model:value="config.algo.weights[out.name]"
              :step="5"
              :min="0"
              :max="100"
              :disabled="optimizableTargets.length === 1"
            />
          </div>
        </n-card>
      </n-scrollbar>

      <div class="action-area" style="display: flex; gap: 12px">
        <n-button
          v-if="!isRunning"
          type="primary"
          size="large"
          class="start-btn"
          @click="startOptimization"
          style="flex: 1"
        >
          <template #icon
            ><n-icon><Play /></n-icon
          ></template>
          启动神经网络反向演化
        </n-button>
        <n-button
          v-else
          type="error"
          size="large"
          class="start-btn"
          @click="stopOptimization"
          style="flex: 1"
        >
          <template #icon
            ><n-icon><StopCircle /></n-icon
          ></template>
          强制终止 (Kill)
        </n-button>

        <n-button
          v-if="!isRunning"
          type="default"
          size="large"
          @click="clearAllData"
          title="清空图表数据"
          style="height: 50px"
        >
          <template #icon
            ><n-icon><Trash2 /></n-icon
          ></template>
        </n-button>
      </div>
    </div>

    <div class="main-content">
      <n-card
        class="modern-card"
        size="small"
        style="margin-bottom: 12px; flex-shrink: 0"
      >
        <div
          style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
          "
        >
          <n-select
            v-model:value="currentModelKey"
            :options="modelOptions"
            size="large"
            placeholder="请选择预训练的神经网络模型"
            style="flex: 1"
          />
          <n-button type="primary" secondary size="large" @click="loadModel"
            >📂 加载 / 切换模型</n-button
          >
        </div>
      </n-card>

      <div v-if="!isModelLoaded" class="empty-state">
        <n-icon size="60" color="var(--n-text-color-3)"><Box /></n-icon>
        <p>请先从上方选择并加载一个预训练的神经网络代理模型</p>
      </div>

      <n-tabs
        v-else
        v-model:value="activeTab"
        type="segment"
        animated
        style="flex: 1; display: flex; flex-direction: column; min-height: 0"
      >
        <n-tab-pane
          name="inverse"
          tab=" 反向演化 (GA Inverse)"
          display-directive="show"
        >
          <div
            style="
              display: flex;
              flex-direction: column;
              gap: 12px;
              padding-right: 8px;
              padding-bottom: 24px;
            "
          >
            <n-grid :x-gap="12" :cols="4">
              <n-gi :span="3">
                <n-card
                  class="modern-card"
                  size="small"
                  title="物理参数边界 (Bounds)"
                >
                  <n-grid :x-gap="12" :y-gap="8" :cols="4">
                    <n-gi v-for="(param, index) in currentParams" :key="index">
                      <div class="param-bound-box">
                        <div class="param-name">{{ param.name }}</div>
                        <n-grid :x-gap="8" :cols="2">
                          <n-gi>
                            <n-input-number
                              v-model:value="param.min"
                              :show-button="false"
                              size="small"
                            >
                              <template #prefix>
                                <span
                                  style="
                                    color: var(--n-text-color-3);
                                    font-size: 12px;
                                    margin-right: 4px;
                                  "
                                  >Min</span
                                >
                              </template>
                            </n-input-number>
                          </n-gi>
                          <n-gi>
                            <n-input-number
                              v-model:value="param.max"
                              :show-button="false"
                              size="small"
                            >
                              <template #prefix>
                                <span
                                  style="
                                    color: var(--n-text-color-3);
                                    font-size: 12px;
                                    margin-right: 4px;
                                  "
                                  >Max</span
                                >
                              </template>
                            </n-input-number>
                          </n-gi>
                        </n-grid>
                      </div>
                    </n-gi>
                  </n-grid>
                </n-card>
              </n-gi>
              <n-gi :span="1">
                <n-card
                  class="modern-card"
                  size="small"
                  title="实时演化状态"
                  style="height: 100%; display: flex; flex-direction: column"
                >
                  <n-statistic label="进化进度 (Gen)">
                    <n-progress
                      type="line"
                      :percentage="
                        Math.round((currentGen / config.algo.nGen) * 100)
                      "
                      :height="8"
                      status="success"
                      style="margin-top: 4px"
                    >
                      <span class="text-neon-white" style="font-size: 16px"
                        >{{ currentGen }} / {{ config.algo.nGen }}</span
                      >
                    </n-progress>
                  </n-statistic>
                  <n-statistic
                    label="全局最优解 (最高综合得分)"
                    style="margin-top: 8px"
                  >
                    <div
                      style="
                        display: flex;
                        flex-direction: column;
                        gap: 4px;
                        margin-top: 6px;
                      "
                    >
                      <div
                        v-if="bestGlobalMetrics.eff !== null"
                        style="display: flex; align-items: baseline; gap: 8px"
                      >
                        <span
                          style="
                            font-size: 13px;
                            color: var(--n-text-color-3);
                            width: 36px;
                          "
                          >效率</span
                        >
                        <span class="text-neon-green" style="font-size: 20px"
                          >{{ bestGlobalMetrics.eff.toFixed(2) }} %</span
                        >
                      </div>

                      <div
                        v-if="bestGlobalMetrics.power !== null"
                        style="display: flex; align-items: baseline; gap: 8px"
                      >
                        <span
                          style="
                            font-size: 13px;
                            color: var(--n-text-color-3);
                            width: 36px;
                          "
                          >功率</span
                        >
                        <span
                          class="text-neon-orange"
                          style="font-size: 20px"
                          >{{ formatPower(bestGlobalMetrics.power) }}</span
                        >
                      </div>

                      <div
                        v-if="bestGlobalMetrics.freq !== null"
                        style="display: flex; align-items: baseline; gap: 8px"
                      >
                        <span
                          style="
                            font-size: 13px;
                            color: var(--n-text-color-3);
                            width: 36px;
                          "
                          >频率</span
                        >
                        <span class="text-neon-blue" style="font-size: 20px"
                          >{{ bestGlobalMetrics.freq.toFixed(3) }} GHz</span
                        >
                      </div>

                      <div
                        v-if="
                          bestGlobalMetrics.eff === null &&
                          bestGlobalMetrics.power === null &&
                          bestGlobalMetrics.freq === null
                        "
                      >
                        <span class="text-neon-green" style="font-size: 20px"
                          >--</span
                        >
                      </div>

                      <div
                        v-if="
                          bestGlobalMetrics.eff === null &&
                          bestGlobalMetrics.power === null &&
                          bestGlobalMetrics.freq === null
                        "
                      >
                        <span class="text-neon-green" style="font-size: 20px"
                          >--</span
                        >
                      </div>

                      <div
                        v-if="bestGlobalMetrics.params"
                        style="
                          margin-top: 14px;
                          padding-top: 12px;
                          border-top: 1px dashed var(--n-border-color);
                        "
                      >
                        <div
                          style="
                            font-size: 12px;
                            color: var(--n-text-color-3);
                            margin-bottom: 8px;
                            font-weight: bold;
                          "
                        >
                          🎯 最优参数组合 (Opt Params)
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px">
                          <n-tag
                            v-for="(val, key) in bestGlobalMetrics.params"
                            :key="key"
                            size="small"
                            type="primary"
                            :bordered="false"
                            style="font-family: monospace"
                          >
                            {{
                              currentParams.find((p) => p.cstName === key)
                                ?.name || key
                            }}:
                            <span style="font-weight: bold; margin-left: 4px">
                              {{ val % 1 === 0 ? val : val.toFixed(3) }}
                            </span>
                          </n-tag>
                        </div>
                      </div>
                    </div>
                  </n-statistic>

                  <div
                    v-if="config.online.enable"
                    style="
                      margin-top: auto;
                      padding-top: 12px;
                      border-top: 1px dashed var(--n-border-color);
                    "
                  >
                    <div
                      style="
                        font-size: 12px;
                        color: var(--n-text-color-3);
                        margin-bottom: 4px;
                        font-weight: bold;
                      "
                    >
                      微调终端 (Online Logs)
                    </div>
                    <div
                      style="
                        background: var(--n-code-color);
                        border-radius: 4px;
                        padding: 6px;
                        height: 90px;
                        overflow-y: hidden;
                        display: flex;
                        flex-direction: column;
                        justify-content: flex-end;
                      "
                    >
                      <div
                        v-for="(log, idx) in onlineLogs"
                        :key="idx"
                        style="
                          font-size: 11px;
                          font-family: monospace;
                          color: #10b981;
                          line-height: 1.5;
                          white-space: nowrap;
                          overflow: hidden;
                          text-overflow: ellipsis;
                        "
                      >
                        > {{ log }}
                      </div>
                      <div
                        v-if="onlineLogs.length === 0"
                        style="
                          font-size: 11px;
                          color: var(--n-text-color-3);
                          font-family: monospace;
                        "
                      >
                        Awaiting Engine Instructions...
                      </div>
                    </div>
                  </div>
                </n-card>
              </n-gi>
            </n-grid>

            <n-grid
              :x-gap="12"
              :cols="2"
              style="height: 500px; flex-shrink: 0; margin-bottom: 12px"
            >
              <n-gi>
                <n-card
                  class="chart-card"
                  content-style="padding: 0; display: flex; flex-direction: column;"
                  style="height: 100%"
                >
                  <div class="card-header" style="flex-wrap: wrap; gap: 8px">
                    <span class="card-title"
                      ><n-icon><Network /></n-icon> 平行坐标系
                      (多维参数耦合分析)</span
                    >
                    <n-space align="center" :size="6">
                      <n-popselect
                        v-model:value="selectedParallelInputs"
                        multiple
                        :options="
                          currentParams.map((p) => ({
                            label: p.name,
                            value: p.cstName,
                          }))
                        "
                        @update:value="updateParallelChartAxes"
                      >
                        <n-button size="tiny" secondary type="info"
                          >选择变量 ({{
                            selectedParallelInputs.length
                          }})</n-button
                        >
                      </n-popselect>
                      <n-popselect
                        v-model:value="selectedParallelOutputs"
                        multiple
                        :options="parallelOutputOptions"
                        @update:value="updateParallelChartAxes"
                      >
                        <n-button size="tiny" secondary type="success"
                          >选择目标 ({{
                            selectedParallelOutputs.length
                          }})</n-button
                        >
                      </n-popselect>
                      <n-button
                        size="tiny"
                        type="warning"
                        secondary
                        @click="clearParallelBrush"
                        >清除框选</n-button
                      >
                      <n-button
                        quaternary
                        circle
                        size="small"
                        @click="toggleFullscreen"
                        title="全屏查看"
                        ><n-icon><Maximize /></n-icon
                      ></n-button>
                    </n-space>
                  </div>
                  <div
                    ref="parallelChartRef"
                    :class="'echarts-container'"
                  ></div>
                </n-card>
              </n-gi>

              <n-gi>
                <n-card
                  class="chart-card"
                  content-style="padding: 0; display: flex; flex-direction: column;"
                  style="height: 100%"
                >
                  <div class="card-header">
                    <span class="card-title"
                      ><n-icon><Grid /></n-icon> 优胜个体相关性热力图
                      (Pearson)</span
                    >
                    <n-button
                      quaternary
                      circle
                      size="small"
                      @click="toggleFullscreen"
                      title="全屏查看"
                      ><n-icon><Maximize /></n-icon
                    ></n-button>
                  </div>
                  <div
                    style="
                      flex: 1;
                      position: relative;
                      min-width: 0;
                      min-height: 0;
                    "
                  >
                    <div
                      ref="correlationHeatmapRef"
                      style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        width: 100%;
                        height: 100%;
                        background: var(--n-code-color);
                        border-radius: 0 0 8px 8px;
                        overflow: hidden;
                      "
                    >
                      <span
                        style="
                          color: gray;
                          font-size: 12px;
                          display: inline-block;
                          padding: 12px;
                        "
                        >图表占位区：等待 ECharts 渲染</span
                      >
                    </div>
                  </div>
                </n-card>
              </n-gi>
            </n-grid>

            <n-grid :x-gap="12" :cols="2" style="height: 500px; flex-shrink: 0">
              <n-gi>
                <n-card
                  class="chart-card"
                  content-style="padding: 0; display: flex; flex-direction: column;"
                  style="height: 100%"
                >
                  <div class="card-header">
                    <span class="card-title"
                      ><n-icon><ScatterChart /></n-icon> 帕累托参数前沿图</span
                    >
                    <n-space align="center" :size="6">
                      <n-select
                        v-model:value="scatterX"
                        :options="scatterAxisOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="X轴"
                        @update:value="updateScatterChart"
                      />
                      <n-icon size="14" color="var(--n-text-color-3)"
                        ><Repeat
                      /></n-icon>
                      <n-select
                        v-model:value="scatterY"
                        :options="scatterAxisOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="Y轴"
                        @update:value="updateScatterChart"
                      />
                      <n-button
                        quaternary
                        circle
                        size="small"
                        @click="toggleFullscreen"
                        title="全屏查看"
                        ><n-icon><Maximize /></n-icon
                      ></n-button>
                    </n-space>
                  </div>
                  <div ref="paretoChartRef" :class="'echarts-container'"></div>
                </n-card>
              </n-gi>
              <n-gi>
                <n-card
                  class="chart-card"
                  content-style="padding: 0; display: flex; flex-direction: column;"
                  style="height: 100%"
                >
                  <div class="card-header">
                    <span class="card-title"
                      ><n-icon><BarChart2 /></n-icon> 代际收敛箱线图</span
                    >
                    <n-space align="center" :size="6">
                      <n-select
                        v-model:value="boxplotTarget"
                        :options="outputOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="分析目标"
                        @update:value="updateBoxplotChart"
                      />
                      <n-button
                        quaternary
                        circle
                        size="small"
                        @click="toggleFullscreen"
                        title="全屏查看"
                        ><n-icon><Maximize /></n-icon
                      ></n-button>
                    </n-space>
                  </div>
                  <div ref="boxplotChartRef" :class="'echarts-container'"></div>
                </n-card>
              </n-gi>
            </n-grid>
          </div>
        </n-tab-pane>

        <n-tab-pane
          name="forward"
          tab="正向预测 (Prediction)"
          display-directive="show"
        >
          <div style="display: flex; height: 100%; gap: 16px">
            <n-card
              class="modern-card"
              size="small"
              style="
                width: 280px;
                display: flex;
                flex-direction: column;
                flex-shrink: 0;
                height: calc(100vh - 180px);
              "
              content-style="display: flex; flex-direction: column; padding: 12px; overflow: hidden;"
            >
              <template #header
                ><span class="card-title">快速参数验证</span></template
              >

              <n-scrollbar style="flex: 1; padding-right: 12px">
                <n-form label-placement="top" size="small">
                  <n-form-item
                    v-for="(param, index) in currentParams"
                    :key="index"
                    :label="param.name"
                    style="margin-bottom: 12px"
                  >
                    <n-input-number
                      v-model:value="param.predValue"
                      :step="0.5"
                      style="width: 100%"
                    />
                  </n-form-item>
                </n-form>
              </n-scrollbar>

              <div style="flex-shrink: 0; margin-top: 12px">
                <n-button
                  type="primary"
                  size="large"
                  block
                  style="font-weight: bold"
                  @click="predictSingle"
                >
                  <template #icon
                    ><n-icon><BrainCircuit /></n-icon
                  ></template>
                  执行预测
                </n-button>
              </div>
            </n-card>

            <div
              style="
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 16px;
                min-width: 0;
                height: calc(100vh - 180px);
              "
            >
              <n-card
                class="chart-card"
                size="small"
                style="flex-shrink: 0"
                content-style="padding: 16px;"
              >
                <div
                  style="
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    margin-bottom: 16px;
                    font-weight: bold;
                  "
                >
                  <n-icon size="18" color="#10b981"><Activity /></n-icon>
                  实时推演结果
                </div>

                <n-grid
                  :cols="currentModelConfig?.outputs?.length || 1"
                  :x-gap="16"
                >
                  <n-gi
                    v-for="(out, index) in currentModelConfig?.outputs"
                    :key="index"
                  >
                    <div
                      style="
                        background: rgba(0, 0, 0, 0.15);
                        border: 1px dashed var(--n-border-color);
                        border-radius: 8px;
                        padding: 16px;
                        text-align: center;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        height: 100%;
                      "
                    >
                      <div
                        style="
                          font-size: 13px;
                          color: var(--n-text-color-3);
                          margin-bottom: 8px;
                        "
                      >
                        {{
                          out.name === "Power"
                            ? out.display.replace("(W)", "")
                            : out.display
                        }}
                      </div>

                      <div
                        :style="{
                          color:
                            index === 0
                              ? '#10b981'
                              : index === 1
                                ? '#f59e0b'
                                : '#3b82f6',
                        }"
                        style="
                          font-size: 32px;
                          font-weight: 900;
                          font-family: monospace;
                          line-height: 1;
                        "
                      >
                        {{ predictionResults[out.name.toLowerCase()] || "--" }}
                      </div>

                      <div
                        v-if="out.name === 'Frequency' && freqDeltaText"
                        :class="freqStatusClass"
                        style="font-size: 12px; margin-top: 8px"
                      >
                        {{ freqDeltaText }}
                      </div>
                    </div>
                  </n-gi>
                </n-grid>
              </n-card>

              <div style="flex: 1; display: flex; gap: 16px; min-height: 0">
                <n-card
                  class="chart-card"
                  size="small"
                  style="
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    min-height: 0;
                    min-width: 0;
                  "
                  content-style="padding: 16px; display: flex; flex-direction: column;"
                >
                  <div
                    style="
                      display: flex;
                      align-items: center;
                      justify-content: space-between;
                      margin-bottom: 12px;
                      flex-shrink: 0;
                    "
                  >
                    <span style="font-weight: bold">📉 局部参数贡献解构</span>
                    <n-space align="center" :size="6">
                      <n-select
                        v-model:value="localShapTarget"
                        :options="outputOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="分析目标"
                        @update:value="predictSingle"
                      />
                      <n-button
                        quaternary
                        circle
                        size="small"
                        @click="toggleFullscreen"
                        title="全屏查看"
                        ><n-icon><Maximize /></n-icon
                      ></n-button>
                    </n-space>
                  </div>
                  <div
                    ref="shapWaterfallChartRef"
                    class="echarts-container"
                    style="width: 100%; flex: 1"
                  >
                    <span style="color: gray; font-size: 12px"
                      >图表占位区：等待 ECharts 渲染</span
                    >
                  </div>
                </n-card>

                <n-card
                  class="chart-card"
                  size="small"
                  style="
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                    min-height: 0;
                    min-width: 0;
                  "
                  content-style="padding: 0; display: flex; flex-direction: column;"
                >
                  <div class="card-header" style="flex-shrink: 0">
                    <span class="card-title"
                      ><n-icon><Box /></n-icon> 3D 参数地形扫描</span
                    >
                    <n-space align="center" :size="6">
                      <n-select
                        v-model:value="scanZ"
                        :options="outputOptions"
                        size="small"
                        style="width: 140px"
                        placeholder="Z轴(输出)"
                      />
                      <n-select
                        v-model:value="scanX"
                        :options="paramOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="X轴(输入)"
                      />
                      <n-select
                        v-model:value="scanY"
                        :options="paramOptions"
                        size="small"
                        style="width: 130px"
                        placeholder="Y轴(输入)"
                      />
                      <n-button
                        type="info"
                        secondary
                        size="small"
                        @click="generate3DScan"
                        >渲染</n-button
                      >
                      <n-button
                        quaternary
                        circle
                        size="small"
                        @click="toggleFullscreen"
                        title="全屏查看"
                        ><n-icon><Maximize /></n-icon
                      ></n-button>
                    </n-space>
                  </div>
                  <div
                    ref="surfaceChartRef"
                    :class="'echarts-container'"
                    style="flex: 1; background: var(--n-code-color)"
                  ></div>
                </n-card>
              </div>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>
  </div>
</template>

<script setup>
import {
  ref,
  reactive,
  computed,
  onMounted,
  onUnmounted,
  nextTick,
  watch,
  inject,
} from "vue";
import { useMessage } from "naive-ui";
import {
  BrainCircuit,
  Activity,
  Network,
  Settings2,
  Play,
  StopCircle,
  Box,
  BarChart2,
  ScatterChart,
  Trash2,
  Cpu,
  Target,
  Repeat,
  Grid,
  Maximize,
} from "lucide-vue-next";
import * as echarts from "echarts";
import "echarts-gl";
const predictionResults = ref({});
const message = useMessage();
const isDarkMode = inject("globalTheme", ref(true));
const islandState = inject("islandState");
const currentModelMeta = ref({
  targetFreq: 2.4, // 目标靶心频率
  freqSpan: 0.2, // 仪表盘左右显示的跨度 (±0.2)
  safeZone: 0.05, // 绿色的合格安全区 (±0.05)
  powerMax: 1000, // 功率表盘的初始最大刻度
});
const freqStatusClass = ref("text-neon-white");
const freqDeltaText = ref("");
// ================= 状态数据 =================
const modelRegistry = ref({});
// 当前选中模型的完整 JSON 配置
const currentModelConfig = ref(null);

const modelOptions = computed(() => {
  return Object.keys(modelRegistry.value).map((key) => ({
    label: modelRegistry.value[key].display_name || key,
    value: key,
  }));
});

// 新代码
const getTooltipStyle = () => ({
  // ✨ 移除了 trigger 和 show，让它变成纯粹的“样式提供者”，绝不干涉原有图表的触发逻辑
  backgroundColor: isDarkMode.value
    ? "rgba(15, 23, 42, 0.45)"
    : "rgba(255, 255, 255, 0.60)",
  borderColor: isDarkMode.value
    ? "rgba(255, 255, 255, 0.2)"
    : "rgba(0, 0, 0, 0.1)",
  borderWidth: 1,
  padding: 12,
  textStyle: { color: isDarkMode.value ? "#e2e8f0" : "#333333", fontSize: 13 },
  // ✨ 核心修复：为滤镜加上 !important，强行击穿浏览器在全屏 #top-layer 的渲染降级限制；去掉了冲突的 border
  extraCssText:
    "backdrop-filter: blur(14px) !important; -webkit-backdrop-filter: blur(14px) !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important; border-radius: 10px !important;",
});

const isRunning = ref(false);
const isModelLoaded = ref(false);
const currentModelKey = ref(null);
const API_BASE = "/api";
const WS_BASE = `ws://${window.location.host}/api/nn/ws`;
const onlineLogs = ref([]);
const config = reactive({
  online: {
    enable: false,
    kSamples: 5,
    cstPath: "F:\\cst files\\ACO for report\\ACO FR.cst",
    effPath: "Tables\\1D Results\\EFF",
    powerPath: "Tables\\1D Results\\AVGpower",
    freqPath: "Tables\\1D Results\\FFT",
  },
  algo: {
    popSize: 20,
    nGen: 30,
    pc: 0.7,
    pm: 0.2,
    targetFreq: 6.0,
    weights: {},
    useAdaptiveMut: false,
    mutPhases: [0.3, 0.7],
  },
});
const currentParams = ref([]);
const scanX = ref(null);
const scanY = ref(null);
const scanZ = ref(null);
const selectedParallelInputs = ref([]);
const selectedParallelOutputs = ref(["primary", "secondary"]);
watch(
  () => currentParams.value,
  (newVal) => {
    if (newVal.length > 0 && selectedParallelInputs.value.length === 0) {
      selectedParallelInputs.value = newVal.slice(0, 4).map((p) => p.cstName);
    }
  },
  { immediate: true },
);

const scatterX = ref("Gen");
const scatterY = ref("Efficiency");

// 动态生成下拉选项：所有模型输出头 + "代数(Gen)"

// 动态重绘散点图函数
const updateScatterChart = () => {
  if (!paretoChart) return;

  const xOption = scatterAxisOptions.value.find(
    (o) => o.value === scatterX.value,
  );
  const yOption = scatterAxisOptions.value.find(
    (o) => o.value === scatterY.value,
  );
  const xName = xOption ? xOption.label : scatterX.value;
  const yName = yOption ? yOption.label : scatterY.value;

  // ✨ 核心修复：获取 JSON 里的 scale_factor (例如 1e-6 把 W 转为 MW)
  const xConf = outputOptions.value.find((o) => o.value === scatterX.value);
  const yConf = outputOptions.value.find((o) => o.value === scatterY.value);
  const xScale = xConf?.scale_factor || 1;
  const yScale = yConf?.scale_factor || 1;

  // 将后端传来的对象数组，映射成 ECharts 需要的二维数组
  const plotData = paretoData.map((d) => {
    // 防御性校验：如果后端漏传某个指标，用 0 兜底，防止 undefined 导致图表白屏崩溃
    let xVal = d[scatterX.value] !== undefined ? d[scatterX.value] : 0;
    let yVal = d[scatterY.value] !== undefined ? d[scatterY.value] : 0;

    // 根据配置自动缩放 (避开 Gen 轴)
    if (scatterX.value !== "Gen") xVal = xVal * xScale;
    if (scatterY.value !== "Gen") yVal = yVal * yScale;

    // 如果 X 轴是代数(Gen)，加一点横向随机抖动防止点重叠成一条竖线
    if (scatterX.value === "Gen") xVal += (Math.random() - 0.5) * 0.5;

    // 数组格式: [X, Y, Gen] (第三个参数留给 VisualMap 做颜色深浅映射)
    return [xVal, yVal, d.Gen];
  });

  paretoChart.setOption({
    xAxis: { name: xName },
    yAxis: { name: yName },
    series: [{ data: plotData }],
  });
};

const updateBoxplotChart = () => {
  if (!boxplotChart || !boxplotTarget.value) return;

  const targetKey = boxplotTarget.value;
  const opt = outputOptions.value.find((o) => o.value === targetKey);
  const yName = opt ? opt.label : targetKey;
  const scale = opt?.scale_factor || 1;

  // 1. 从存满字典的 boxplotData 中，提取用户当前选中指标的历代数据，并执行缩放 (如 W 转 MW)
  const seriesData = boxplotData.map((genDict) => {
    const rawBox = genDict[targetKey];
    if (!rawBox) return [0, 0, 0, 0, 0]; // 防御性校验
    return rawBox.map((val) => val * scale);
  });

  const xAxisData = Array.from(
    { length: seriesData.length },
    (_, i) => `G${i + 1}`,
  );

  // 2. 特例判断：如果当前看的是频率(Frequency)，画一条耀眼的绿色目标基准线
  let markLineOpt = null;
  if (targetKey.toLowerCase().includes("freq")) {
    const targetVal = config.algo.targetFreq;
    markLineOpt = {
      symbol: ["none", "none"],
      data: [
        {
          yAxis: targetVal,
          name: "Target",
          lineStyle: { color: "#10b981", type: "dashed", width: 2 },
          label: {
            show: true,
            position: "end",
            formatter: `靶心: ${targetVal} GHz`,
            color: "#10b981",
          },
        },
      ],
    };
  }

  // 3. 注入配置，ECharts 会自动处理动画过渡
  boxplotChart.setOption({
    xAxis: { data: xAxisData },
    yAxis: { name: yName },
    series: [
      {
        data: seriesData,
        markLine: markLineOpt, // 巧妙之处：如果是 null，ECharts会自动忽略，不画线
      },
    ],
  });
};

// 动态解析 JSON，生成 Z 轴下拉框的选项
const optimizableTargets = computed(() => {
  if (!currentModelConfig.value?.outputs) return [];
  return currentModelConfig.value.outputs.filter((out) => {
    const name = out.name.toLowerCase();
    // 只要名字里带 logit 或 class 就不在 UI 上显示
    return !name.includes("logit") && !name.includes("class");
  });
});

// 2. 动态生成 Z 轴下拉框的选项（满足 n-select 需要的 label 和 value 格式）
const outputOptions = computed(() => {
  if (!currentModelConfig.value?.outputs) return [];
  // 先映射出原始索引，再过滤，保证索引的绝对正确
  return currentModelConfig.value.outputs
    .map((out, originalIndex) => ({ out, originalIndex }))
    .filter(
      ({ out }) =>
        !out.name.toLowerCase().includes("logit") &&
        !out.name.toLowerCase().includes("class"),
    )
    .map(({ out, originalIndex }) => ({
      label: out.display,
      value: out.name,
      // ✨ 核心修复：如果 JSON 里没写 model_index，使用它的原生数组索引，防止后端回退到默认 0
      model_index:
        out.model_index !== undefined ? out.model_index : originalIndex,
      needs_inverse: out.needs_inverse,
      scale_factor: out.scale_factor,
    }));
});

const scatterAxisOptions = computed(() => {
  const opts = [{ label: "代数 (Gen)", value: "Gen" }];
  outputOptions.value.forEach((o) => {
    opts.push({ label: o.label, value: o.value }); // 例如: value: 'Power', label: '功率(W)'
  });
  return opts;
});

// 当模型加载完成后，自动分配合理的初始 X 和 Y
watch(
  () => outputOptions.value,
  (newVal) => {
    if (newVal.length >= 2) {
      scatterX.value = newVal[1].value; // 默认X: 比如 Frequency 或 Power
      scatterY.value = newVal[0].value; // 默认Y: 比如 Efficiency
    } else if (newVal.length === 1) {
      scatterX.value = "Gen";
      scatterY.value = newVal[0].value;
    }
  },
);

// 3. 判断是否包含需要靶向逼近的指标（比如频率）
const hasFrequencyTarget = computed(() => {
  return optimizableTargets.value.some((out) =>
    out.name.toLowerCase().includes("freq"),
  );
});
const paramOptions = computed(() =>
  currentParams.value.map((p) => ({ label: p.name, value: p.cstName })),
);

const parallelOutputOptions = computed(() => {
  const outputs = optimizableTargets.value;
  const primaryDisplay = outputs[0]?.display || "首要目标";
  const secondaryDisplay = outputs.length > 1 ? outputs[1].display : "";
  const opts = [{ label: primaryDisplay, value: "primary" }];
  if (secondaryDisplay)
    opts.push({ label: secondaryDisplay, value: "secondary" });
  return opts;
});

// 根据用户的勾选，动态重绘平行坐标系的轴
const updateParallelChartAxes = () => {
  if (!parallelChart) return;
  const tc = getThemeColor();
  const gc = getGridColor();
  const parallelAxes = [];

  // 1. 添加选中的输入参数轴
  selectedParallelInputs.value.forEach((cstName) => {
    // 通过 dim 完美映射到数组的真实索引位置
    const dimIndex = currentParams.value.findIndex(
      (p) => p.cstName === cstName,
    );
    if (dimIndex !== -1) {
      parallelAxes.push({
        dim: dimIndex,
        name: currentParams.value[dimIndex].name,
        type: "value",
        nameTextStyle: { color: tc },
        axisLine: { lineStyle: { color: gc } },
        axisLabel: { color: tc, formatter: axisFormatter },
      });
    }
  });

  // 2. 添加选中的输出目标轴
  const nParams = currentParams.value.length;
  const outputs = optimizableTargets.value;
  const primaryDisplay = outputs[0]?.display || "首要目标";
  const secondaryDisplay = outputs.length > 1 ? outputs[1].display : "";

  // 后端传来的数组最后两位固定是: [..., secondaryValue, primaryValue]
  if (selectedParallelOutputs.value.includes("secondary") && secondaryDisplay) {
    parallelAxes.push({
      dim: nParams,
      name: secondaryDisplay,
      type: "value",
      nameTextStyle: { color: tc },
      axisLine: { lineStyle: { color: gc } },
      axisLabel: { color: tc, formatter: axisFormatter },
    });
  }
  if (selectedParallelOutputs.value.includes("primary")) {
    parallelAxes.push({
      dim: nParams + 1,
      name: primaryDisplay,
      type: "value",
      nameTextStyle: { color: tc },
      axisLine: { lineStyle: { color: gc } },
      axisLabel: { color: tc, formatter: axisFormatter },
    });
  }

  // 触发 ECharts 更新，使用 replaceMerge 彻底替换旧的轴配置
  const currentData = parallelChart.getOption()?.series?.[0]?.data || [];

  // 触发 ECharts 更新，使用 replaceMerge 彻底替换旧的轴配置
  parallelChart.setOption(
    {
      backgroundColor: "transparent",
      tooltip: { ...getTooltipStyle() },
      parallelAxis: parallelAxes, // 👈 核心修复：必须把拼装好的坐标轴数组传给 ECharts！
      parallel: {
        left: "5%",
        right: "8%",
        bottom: "15%",
        top: "20%",
        parallelAxisDefault: {
          type: "value",
          nameTextStyle: { color: tc },
          axisLine: { lineStyle: { color: gc } },
          axisLabel: { color: tc, formatter: axisFormatter },
        },
      },
      series: [
        {
          name: "个体",
          type: "parallel",
          lineStyle: { width: 1.5, opacity: 0.15 },
          data: currentData, // 👈 替换原来的 []，保护演化状态
          emphasis: {
            lineStyle: { width: 3, opacity: 1, color: "#10b981" },
          },
        },
      ],
    },
    true,
  );
};

// 演化数据
const currentGen = ref(0);
const bestGlobalMetrics = ref({ power: null, eff: null, freq: null });
const parallelData = []; // 平行坐标系数据
const paretoData = []; // 帕累托散点数据
const boxplotData = []; // 箱线图数据 (现在存储的是包含多个指标的字典数组)
const boxplotTarget = ref(null); // 箱线图当前选中的下拉目标
const localShapTarget = ref(null);

// 监听 outputOptions 自动为箱线图赋个合理的初始值
watch(
  () => outputOptions.value,
  (newVal) => {
    if (newVal.length > 0) {
      const defaultOpt =
        newVal.find((o) => !o.value.toLowerCase().includes("freq")) ||
        newVal[0];
      if (!boxplotTarget.value) boxplotTarget.value = defaultOpt.value;
      if (!localShapTarget.value) localShapTarget.value = defaultOpt.value; // ✨ 初始化给局部 SHAP 赋值
    }
  },
  { immediate: true },
);
let wsClient = null;
// 预测数据

// 确保整个文件里下面这行代码只出现一次！
const activeTab = ref("inverse");

watch(activeTab, (newVal) => {
  // 因为 Naive UI 的 Tabs 有动画，延迟 300ms 等动画结束、容器彻底展开后再 resize
  setTimeout(() => {
    if (newVal === "forward") {
      if (gaugeChart) gaugeChart.resize();
      if (surfaceChart) surfaceChart.resize();
    } else {
      if (parallelChart) parallelChart.resize();
      if (paretoChart) paretoChart.resize();
      if (boxplotChart) boxplotChart.resize();
    }
  }, 300);
});
// 图表 Refs 和 实例
const parallelChartRef = ref(null);
const paretoChartRef = ref(null);
const boxplotChartRef = ref(null);
const surfaceChartRef = ref(null);
const gaugeChartRef = ref(null);
const globalImportanceChartRef = ref(null);
const shapWaterfallChartRef = ref(null);
const correlationHeatmapRef = ref(null);
let parallelChart,
  paretoChart,
  boxplotChart,
  surfaceChart,
  gaugeChart,
  globalImportanceChart,
  shapWaterfallChart,
  correlationHeatmapChart;

// ================= 基础逻辑 =================
const getThemeColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.65)" : "rgba(0, 0, 0, 0.65)";
const getGridColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.08)";
const renderGlobalShap = (realData) => {
  // 👈 修复: 补上了缺失的 realData 参数
  if (!globalImportanceChartRef.value) return;
  if (!globalImportanceChart)
    globalImportanceChart = echarts.init(globalImportanceChartRef.value);
  const params = currentParams.value.map((p) => p.name).reverse();

  // 👈 修复: 删除了 Math.random，换成真实的后端数组，并反转以匹配 Y 轴顺序
  const data = realData ? [...realData].reverse() : [];

  globalImportanceChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      valueFormatter: (val) => parseFloat(val).toFixed(2) + "%",
      ...getTooltipStyle(),
    }, // 👈 替换
    grid: { top: 10, right: 40, bottom: 20, left: 90 }, // 👈 调大 left 避免参数名被遮挡
    xAxis: {
      type: "value",
      max: 100,
      axisLabel: { color: getThemeColor(), formatter: "{value}%" },
      splitLine: { lineStyle: { color: getGridColor() } },
    },
    yAxis: {
      type: "category",
      data: params,
      axisLabel: {
        color: getThemeColor(),
        fontSize: 11,
        width: 80,
        overflow: "truncate",
      },
    },
    series: [
      {
        name: "贡献度",
        type: "bar",
        data: data,
        // 👈 修复 formatter，只显示2位小数，防止像图1那样爆炸
        label: {
          show: true,
          position: "right",
          formatter: (p) => parseFloat(p.value).toFixed(2) + "%",
          color: getThemeColor(),
          fontSize: 10,
        },
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: "#313695" },
            { offset: 1, color: "#3b82f6" },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      },
    ],
  });
};

// 📉 2. 渲染局部参数贡献瀑布图 (Local SHAP)
const renderLocalShap = (realShap) => {
  // 👈 修复: 补上了缺失的 realShap 参数
  if (!shapWaterfallChartRef.value) return;
  if (!shapWaterfallChart)
    shapWaterfallChart = echarts.init(shapWaterfallChartRef.value);
  const params = currentParams.value.map((p) => p.name).reverse();

  // 正常接收参数后，这里就不会报 undefined 错误了
  const data = realShap ? [...realShap].reverse() : [];

  shapWaterfallChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      ...getTooltipStyle(),
    }, // 👈 替换
    grid: { top: 20, right: 30, bottom: 20, left: 70 },
    xAxis: {
      type: "value",
      axisLabel: { color: getThemeColor() },
      splitLine: { lineStyle: { color: getGridColor() } },
    },
    yAxis: {
      type: "category",
      data: params,
      axisLabel: {
        color: getThemeColor(),
        fontSize: 11,
        width: 60,
        overflow: "truncate",
      },
    },
    series: [
      {
        name: "局部贡献",
        type: "bar",
        data: data.map((v) => ({
          value: v,
          itemStyle: { color: v > 0 ? "#ef4444" : "#10b981", borderRadius: 2 },
        })),
        label: {
          show: true,
          position: "inside",
          formatter: "{c}",
          color: "#fff",
          fontSize: 10,
        },
      },
    ],
  });
};

// 🔲 3. 渲染相关性热力图 (Pearson)
const renderCorrelationHeatmap = (realData) => {
  // 👈 修复: 补上了缺失的 realData 参数
  if (!correlationHeatmapRef.value) return;
  if (!correlationHeatmapChart)
    correlationHeatmapChart = echarts.init(correlationHeatmapRef.value);
  const params = currentParams.value.map((p) => p.name);

  // 👈 修复了引发崩溃的语法错误：你原代码里直接悬空写了个 "series: [{...}]"，会导致 Vue 编译彻底失败
  correlationHeatmapChart.setOption({
    backgroundColor: "transparent",
    tooltip: {
      position: "top",
      formatter: (p) =>
        `${params[p.data[0]]} & ${params[p.data[1]]}<br/>相关性: ${p.data[2]}`,
      ...getTooltipStyle(),
    }, // 👈 替换
    grid: { top: 20, right: 30, bottom: 80, left: 80 },
    xAxis: {
      type: "category",
      data: params,
      axisLabel: {
        color: getThemeColor(),
        interval: 0,
        rotate: 45,
        fontSize: 10,
      },
      splitArea: { show: true },
    },
    yAxis: {
      type: "category",
      data: params,
      axisLabel: { color: getThemeColor(), fontSize: 10 },
      splitArea: { show: true },
    },
    visualMap: {
      show: false,
      min: -1,
      max: 1,
      inRange: { color: ["#313695", "#e0f3f8", "#a50026"] },
    },
    series: [
      {
        type: "heatmap",
        data: realData || [], // 👈 把传入的数据直接放到这里
        label: { show: true, fontSize: 11, color: "#000", fontWeight: "bold" },
        itemStyle: { borderColor: getGridColor(), borderWidth: 1 },
      },
    ],
  });
};

const fetchModelsList = async () => {
  try {
    const res = await fetch(`${API_BASE}/nn/models_list`);
    const data = await res.json();
    if (res.ok) {
      const registry = {};
      data.models.forEach((model) => {
        registry[model.model_id] = model;
      });
      modelRegistry.value = registry;
    } else {
      message.error("无法获取模型列表");
    }
  } catch (error) {
    message.error("模型服务连接失败，请检查后端运行状态");
  }
};

// 确保在页面加载时调用
onMounted(() => {
  window.addEventListener("resize", handleResize);
  fetchModelsList();
});

const loadModel = async () => {
  if (!currentModelKey.value) return message.warning("请选择模型！");
  message.loading("正在从服务器加载模型与预处理张量...");

  try {
    const res = await fetch(`${API_BASE}/nn/load`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_name: currentModelKey.value }),
    });
    const data = await res.json();

    if (res.ok) {
      // 🌟 核心修改：从获取到的注册表中读取
      const configObj = modelRegistry.value[currentModelKey.value];
      currentModelConfig.value = configObj; // 存入全局，供图表和预测使用

      const outputs = configObj.outputs || [];
      config.algo.weights = {}; // 清空上一个模型的权重

      config.algo.targetFreq = configObj.meta?.target_freq || 6.0;

      const optTargets =
        configObj.outputs?.filter(
          (out) => !out.name.toLowerCase().includes("logit"),
        ) || [];
      if (optTargets.length > 0) {
        const avg = Math.floor(100 / optTargets.length);
        optTargets.forEach((out, i) => {
          config.algo.weights[out.name] =
            i === optTargets.length - 1
              ? 100 - avg * (optTargets.length - 1)
              : avg;
        });
      }

      // 深拷贝 input_features
      // 把后端 JSON 里的 default 映射给前端的 predValue
      currentParams.value = configObj.input_features.map((p) => ({
        ...p,
        cstName: p.cst_name,
        predValue: p.default || (p.min + p.max) / 2, // 如果没写 default 就取中间值
      }));

      // 更新仪表盘的元数据
      currentModelMeta.value.targetFreq = configObj.meta.target_freq || 0;
      currentModelMeta.value.powerMax = configObj.meta.power_max || 1000;

      if (currentParams.value.length >= 2) {
        scanX.value = currentParams.value[0].cstName;
        scanY.value = currentParams.value[1].cstName;
      }

      if (configObj.outputs && configObj.outputs.length > 0) {
        scanZ.value = configObj.outputs[0].name;
      }

      isModelLoaded.value = true;
      message.success(`模型载入完毕: 识别到 ${data.input_dim} 维输入特征`);
      fetch(`${API_BASE}/nn/global_importance`)
        .then((r) => r.json())
        .then((res) => {
          nextTick(() => {
            initAllCharts();
            renderGlobalShap(res.importance);
          });
        });
    } else {
      message.error(data.detail);
    }
  } catch (err) {
    message.error("网络请求失败");
  }
};

const formatPower = (val) => {
  const num = parseFloat(val);
  if (isNaN(num)) return "--";
  if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(2) + " MW";
  if (Math.abs(num) >= 1e3) return (num / 1e3).toFixed(2) + " kW";
  return num.toFixed(2) + " W";
};

// 🌟 新增：ECharts 专用的坐标轴缩写格式化工具
const axisFormatter = (value) => {
  if (Math.abs(value) >= 1e6) return (value / 1e6).toFixed(1) + "M";
  if (Math.abs(value) >= 1e3) return (value / 1e3).toFixed(1) + "k";
  return value;
};

const clearParallelBrush = () => {
  if (!parallelChart) return;
  // ECharts 官方 API: 遍历所有可能的轴（0到5），将它们的刷选区间强制置空
  for (let i = 0; i <= 5; i++) {
    parallelChart.dispatchAction({
      type: "axisAreaSelect",
      parallelAxisIndex: i,
      intervals: [],
    });
  }
  message.success("已清除框选过滤");
};

// 2. 全局清空所有图表数据
const clearAllData = () => {
  // 清空 Vue 响应式数组
  currentGen.value = 0;
  bestGlobalMetrics.value = {
    power: null,
    eff: null,
    freq: null,
    params: null,
  };
  parallelData.length = 0;
  paretoData.length = 0;
  boxplotData.length = 0;

  // 强制向 ECharts 注入空数组，覆盖残留的画面
  if (parallelChart) parallelChart.setOption({ series: [{ data: [] }] });
  if (paretoChart)
    paretoChart.setOption({
      xAxis: { name: "功率 (MW)" },
      series: [{ data: [] }],
    });
  if (boxplotChart)
    boxplotChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] });
};

// 模拟演化流式数据生成
const startOptimization = () => {
  if (!isModelLoaded.value) return message.warning("请先加载模型！");

  // 1. 初始化界面状态
  isRunning.value = true;
  isRunning.value = true;
  if (islandState) {
    islandState.NeuralNet.isRunning = true;
    // 使用当前已加载配置的显示名称
    islandState.NeuralNet.modelName = currentModelConfig.value?.display_name || '未命名模型';
    // 对应 config.online.enable
    islandState.NeuralNet.isOnlineLearning = config.online.enable;
    // 对应 config.online.cstPath
    islandState.NeuralNet.filePath = config.online.enable ? config.online.cstPath : "";
    islandState.NeuralNet.progress = 0;
    islandState.NeuralNet.abortFn = stopOptimization;
  }
  currentGen.value = 0;
  bestGlobalMetrics.value = { power: null, eff: null, freq: null };
  parallelData.length = 0;
  paretoData.length = 0;
  boxplotData.length = 0;

  // 清空上一次的箱线图
  if (boxplotChart)
    boxplotChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] });

  message.success("反向演化引擎已启动...");

  // 2. 提取配置与物理边界
  const bounds = currentParams.value.map((p) => [p.min, p.max]);
  const wsConfig = {
    bounds: bounds,
    param_names: currentParams.value.map((p) => p.cstName), // ✨ 必须传给后端查 CST 字典
    pop_size: config.algo.popSize || 20,
    n_gen: config.algo.nGen || 20,
    pc: config.algo.pc || 0.7,
    pm: config.algo.pm || 0.2,
    target_freq: config.algo.targetFreq,
    weights: config.algo.weights,
    use_adaptive_mut: config.algo.useAdaptiveMut,
    mut_phases: config.algo.mutPhases,
    online: config.online, // ✨ 透传完整的在线学习配置给后端
  };

  // 3. 建立 WebSocket 连接
  // 注意：如果是线上环境，这里需要改成 wss:// 并且动态获取域名
  wsClient = new WebSocket(`${WS_BASE}/evolve`);

  wsClient.onopen = () => {
    onlineLogs.value = []; // ✨ 每次启动时清空历史日志
    wsClient.send(JSON.stringify(wsConfig));
  };

  wsClient.onmessage = (event) => {
    const data = JSON.parse(event.data);

    // ✨ 拦截后端的实时终端日志
    if (data.type === "info") {
      onlineLogs.value.push(data.message);
      // 保持只显示最新的 5 条，形成滚动效果
      if (onlineLogs.value.length > 5) onlineLogs.value.shift();
      return;
    }

    if (data.error) {
      message.error("演化出错: " + data.error);
      stopOptimization();
      return;
    }
    if (data.status === "complete") {
      message.success("🧬 演化完成！");
      isRunning.value = false;
      if (islandState) islandState.NeuralNet.isRunning = false; // ✨ 修复结束状态
      return;
    }

    // 更新状态文本
    currentGen.value = data.gen;
    
    // ✨ 驱动灵动岛进度条
    if (islandState && islandState.NeuralNet.isRunning) {
      islandState.NeuralNet.progress = Math.round((currentGen.value / config.algo.nGen) * 100);
    }
    
    if (data.best_global_metrics) {
      bestGlobalMetrics.value = data.best_global_metrics;
    }

    // ================= 图表更新 =================
    // 1. 平行坐标系：只显示当前代，产生流动的视觉效果
    if (parallelChart) {
      parallelChart.setOption({ series: [{ data: data.parallel_data }] });
    }

    // 2. 帕累托散点 / 代际群体云图
    paretoData.push(...data.pareto_data);
    if (paretoChart) {
      updateScatterChart();
    }

    // 3. 收敛箱线图
    boxplotData.push(data.boxplot_data);
    if (boxplotChart) {
      updateBoxplotChart(); // 交给独立的函数处理
    }

    // 4. 相关性热力图
    renderCorrelationHeatmap(data.heatmap_data); // 👈 每一代更新热力图
  };

  wsClient.onclose = () => {
    isRunning.value = false;
    if (islandState) islandState.NeuralNet.isRunning = false;
  };
};

// 新代码
const stopOptimization = () => {
  if (wsClient) {
    wsClient.close();
    wsClient = null;
  }
  isRunning.value = false;
  if (islandState) islandState.NeuralNet.isRunning = false; // ✨ 修复中断状态
  message.info("已手动终止演化");
};

// ================= 图表初始化区 =================
const initAllCharts = () => {
  const tc = getThemeColor();
  const gc = getGridColor();

  // 安全检查：确保 JSON 配置已加载
  if (!currentModelConfig.value) return;

  const outputs = optimizableTargets.value;
  // 获取首要指标和次要指标（如果没有次要指标，默认用首要指标占位防止报错）
  const primaryDisplay = outputs[0]?.display || "目标 1";
  const secondaryDisplay =
    outputs.length > 1 ? outputs[1].display : primaryDisplay;

  // 1. 平行坐标系 (动态生成坐标轴)
  if (parallelChartRef.value) {
    parallelChart = echarts.init(parallelChartRef.value);

    // 仅仅注入底层公共样式、全局边距和数据系列的占位符
    // ⚠️ 注意：这里故意不写 visualMap 和 parallelAxis，把它们交给动态函数生成
    parallelChart.setOption(
      {
        backgroundColor: "transparent",
        tooltip: { padding: 10, ...getTooltipStyle() },
        parallel: {
          left: "5%",
          right: "8%",
          bottom: "15%",
          top: "20%",
          // 提取公共的坐标轴文本和线条样式，这样生成的每一根轴都不用重复写样式了
          parallelAxisDefault: {
            type: "value",
            nameTextStyle: { color: tc },
            axisLine: { lineStyle: { color: gc } },
            axisLabel: { color: tc, formatter: axisFormatter },
          },
        },
        series: [
          {
            name: "个体",
            type: "parallel",
            lineStyle: { width: 1.5, opacity: 0.15 },
            data: [],
          },
        ],
      },
      true,
    );

    // ✨ 核心：图表架子搭好后，立刻调用动态函数，根据当前的下拉框默认值去生成具体的轴
    updateParallelChartAxes();
  }

  // 2. 帕累托散点
  if (paretoChartRef.value) {
    paretoChart = echarts.init(paretoChartRef.value);
    paretoChart.setOption(
      {
        backgroundColor: "transparent",
        grid: { top: 30, right: 30, bottom: 40, left: 50 },
        xAxis: {
          name: "",
          type: "value",
          splitLine: { lineStyle: { color: gc } },
          axisLabel: { color: tc, formatter: axisFormatter },
        },
        yAxis: {
          name: "",
          type: "value",
          splitLine: { lineStyle: { color: gc } },
          axisLabel: { color: tc, formatter: axisFormatter },
        },
        visualMap: {
          show: false,
          dimension: 2,
          min: 1,
          max: 50,
          inRange: { color: ["#313695", "#e0f3f8", "#a50026"] },
        },
        tooltip: {
          trigger: "item",
          ...getTooltipStyle(),
          formatter: (p) =>
            `<div style="font-family: monospace;">Gen: ${Math.round(p.data[2])}<br/>X: ${p.data[0].toFixed(3)}<br/>Y: ${p.data[1].toFixed(3)}</div>`,
        },
        series: [
          {
            type: "scatter",
            symbolSize: 6,
            itemStyle: { opacity: 0.7 },
            data: [],
          },
        ],
      },
      true,
    );
  }

  // 3. 箱线图
  if (boxplotChartRef.value) {
    boxplotChart = echarts.init(boxplotChartRef.value);
    boxplotChart.setOption(
      {
        backgroundColor: "transparent",
        grid: { top: 30, right: 80, bottom: 40, left: 50 },
        tooltip: {
          ...getTooltipStyle(),
          formatter: (param) => {
            if (param.componentSubType === "boxplot") {
              const v = param.data; // v 结构为 [index, min, Q1, median, Q3, max]
              return `
              <div style="font-family: monospace;">
                <b style="color: #10b981; font-size: 14px;">${param.name} 统计分布</b><hr style="opacity: 0.1; margin: 8px 0;"/>
                <div style="display: grid; grid-template-columns: 60px 1fr; gap: 4px;">
                  <span>最大值:</span> <b>${v[5].toFixed(3)}</b>
                  <span>Q3:</span> <b>${v[4].toFixed(3)}</b>
                  <span style="color: #10b981">中位数:</span> <b style="color: #10b981">${v[3].toFixed(3)}</b>
                  <span>Q1:</span> <b>${v[2].toFixed(3)}</b>
                  <span>最小值:</span> <b>${v[1].toFixed(3)}</b>
                </div>
              </div>
            `;
            }
          },
        },
        xAxis: {
          type: "category",
          data: [],
          splitLine: { show: false },
          axisLabel: { color: tc },
        },
        yAxis: {
          type: "value",
          name: primaryDisplay,
          scale: true,
          boundaryGap: ["5%", "5%"],
          splitLine: { lineStyle: { color: gc } },
          axisLabel: { color: tc, formatter: axisFormatter },
        },
        series: [
          {
            name: "boxplot",
            type: "boxplot",
            itemStyle: {
              color: isDarkMode.value ? "#3b82f6" : "#2563eb",
              borderColor: "#10b981",
              borderWidth: 1.5,
            },
            data: [],
          },
        ],
      },
      true,
    );
  }

  // 4. 正向预测仪表盘 (动态渲染多表)
  if (gaugeChartRef.value) {
    gaugeChart = echarts.init(gaugeChartRef.value);

    const gaugeSeries = outputs.map((out, index) => {
      const total = outputs.length;
      const centerX =
        total === 1 ? "50%" : `${((index + 1) * 100) / (total + 1)}%`;
      const radius = total >= 3 ? "55%" : "70%";
      const colorTheme =
        index === 0 ? "#10b981" : index === 1 ? "#f59e0b" : "#3b82f6";

      // 读取配置的最大值，如果没有则给一个默认值
      let gaugeMax = 100;
      if (out.name === "Power") gaugeMax = currentModelMeta.value.powerMax;
      else if (out.name === "Frequency")
        gaugeMax = currentModelMeta.value.targetFreq * 2;

      return {
        name: out.display,
        type: "gauge",
        center: [centerX, "50%"],
        radius: radius,
        min: 0,
        max: gaugeMax,
        progress: { show: true, width: 10, itemStyle: { color: colorTheme } },
        axisLine: { lineStyle: { width: 10, color: [[1, gc]] } },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { distance: 12, color: tc, fontSize: 10 },
        pointer: { width: 4 },
        detail: {
          valueAnimation: true,
          formatter: "{value}",
          fontSize: 18,
          color: colorTheme,
          offsetCenter: [0, "40%"],
        },
        title: { offsetCenter: [0, "85%"], color: tc, fontSize: 13 },
        data: [{ value: 0, name: out.display }],
      };
    });

    gaugeChart.setOption(
      { backgroundColor: "transparent", series: gaugeSeries },
      true,
    );
  }

  // 6. 3D 曲面
  if (surfaceChartRef.value) {
    surfaceChart = echarts.init(surfaceChartRef.value);
    surfaceChart.setOption({
      title: {
        text: "点击渲染生成参数地形",
        left: "center",
        top: "center",
        textStyle: { color: tc, fontSize: 14, fontWeight: "normal" },
      },
    });
  }
};

// 预测执行
// 预测执行
// 预测执行
const predictSingle = async () => {
  message.loading("Neural Network Inference...");
  try {
    const selectedOpt =
      outputOptions.value.find((o) => o.value === localShapTarget.value) ||
      outputOptions.value[0];
    const targetIdx = selectedOpt
      ? selectedOpt.model_index !== undefined
        ? selectedOpt.model_index
        : 0
      : -1;
    const payload = {
      features: currentParams.value.map((p) => p.predValue),
      target_index: targetIdx, // ✨ 把索引发给后端
    };

    const res = await fetch(`${API_BASE}/nn/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await res.json();

    if (res.ok && result.raw_predictions) {
      if (currentModelConfig.value) {
        const newResults = {};

        currentModelConfig.value.outputs.forEach((out, loopIndex) => {
          // 👉 核心修复：优先读取 JSON 里的 model_index，让数据绝对对齐！
          const idx =
            out.model_index !== undefined ? out.model_index : loopIndex;
          let val = result.raw_predictions[idx];

          // 如果 JSON 里配置了 scale_factor (比如 0.000001 转 MW)，自动换算
          if (out.scale_factor !== undefined) {
            val = val * out.scale_factor;
          } else if (out.name === "Efficiency" && val <= 1.05) {
            val = val * 100;
          }

          const backendKey = out.name.toLowerCase();
          if (val !== undefined && val !== null && !isNaN(val)) {
            // ✨ 修复：如果是功率，直接使用自带的 formatPower 自动加上 MW / kW 单位
            if (out.name === "Power") {
              newResults[backendKey] = formatPower(val);
            } else if (out.name === "Frequency") {
              newResults[backendKey] = val.toFixed(3);
            } else {
              newResults[backendKey] = val.toFixed(2);
            }
          } else {
            newResults[backendKey] = "--";
          }

          // 处理频率提示
          if (out.name === "Frequency") {
            const target = currentModelMeta.value.targetFreq || 0;
            const diff = Math.abs(val - target);
            if (diff <= 0.05) {
              freqStatusClass.value = "text-neon-green";
              freqDeltaText.value = `✓ 偏离靶心 ${diff.toFixed(3)} GHz`;
            } else {
              freqStatusClass.value = "text-neon-orange";
              freqDeltaText.value = `⚠️ 偏离靶心 ${diff.toFixed(3)} GHz`;
            }
          }
        });

        predictionResults.value = newResults;
      }
      message.success("推演完成");
      nextTick(() => {
        renderLocalShap(result.local_shap);
      }); // 👈 触发局部特征瀑布图
    } else {
      message.error(result.detail || "后端未返回有效的预测数据");
    }
  } catch (error) {
    message.error("推演失败，检查后端连接");
  }
};

// 生成 3D 曲面
const generate3DScan = async () => {
  if (scanX.value === scanY.value) return message.error("X和Y轴变量不能相同！");
  if (!scanZ.value) return message.error("请选择Z轴目标！");
  if (!surfaceChart) return;
  message.loading("正在下发矩阵计算任务...");

  try {
    const baseParams = {};
    currentParams.value.forEach((p) => (baseParams[p.cstName] = p.predValue));

    const xParam = currentParams.value.find((p) => p.cstName === scanX.value);
    const yParam = currentParams.value.find((p) => p.cstName === scanY.value);

    const selectedOutput = outputOptions.value.find(
      (o) => o.value === scanZ.value,
    );

    // ✨✨ 核心修复：硬核对齐 PyTorch 后端顺序与反归一化标志 ✨✨
    let realIndex =
      selectedOutput.model_index !== undefined ? selectedOutput.model_index : 1;
    let needsInv = selectedOutput.needs_inverse === true;

    const lowerName = selectedOutput.value.toLowerCase();
    if (lowerName.includes("power")) {
      realIndex = 1; // 功率头固定是 1
      if (selectedOutput.needs_inverse === undefined) needsInv = true; // 功率必须反归一化
    } else if (lowerName.includes("freq")) {
      realIndex = 2; // 频率头固定是 2
      if (selectedOutput.needs_inverse === undefined) needsInv = false;
    }

    const payload = {
      scan_x: scanX.value,
      scan_y: scanY.value,
      base_params: baseParams,
      x_min: xParam.min,
      x_max: xParam.max,
      y_min: yParam.min,
      y_max: yParam.max,
      grid_size: 30,

      // 发送硬核校准过的靶向信息给后端
      target_index: realIndex,
      target_name: selectedOutput.value,
      needs_inverse: needsInv,
    };

    const res = await fetch(`${API_BASE}/nn/scan3d`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();

    if (res.ok) {
      let zScale = selectedOutput.scale_factor || 1;
      let axisName = selectedOutput.label || scanZ.value;

      // ✨✨ 核心修复：自动转换地形图为 MW 显示 ✨✨
      if (lowerName.includes("power") && zScale === 1) {
        zScale = 1e-6; // 缩小 10^6 倍转为 MW
        axisName = axisName.replace("(W)", "(MW)");
        if (!axisName.includes("(MW)")) axisName += " (MW)";
      }

      const scaledSurfaceData = result.surface_data.map((point) => [
        point[0],
        point[1],
        point[2] * zScale,
      ]);

      const zValues = scaledSurfaceData.map((point) => point[2]);
      const minZ = Math.min(...zValues);
      const maxZ = Math.max(...zValues);

      const vMin = minZ === maxZ ? minZ - 1 : minZ - Math.abs(minZ * 0.05);
      const vMax = minZ === maxZ ? maxZ + 1 : maxZ + Math.abs(maxZ * 0.05);

      surfaceChart.setOption(
        {
          tooltip: { ...getTooltipStyle() },
          visualMap: {
            show: true,
            dimension: 2,
            min: vMin,
            max: vMax,
            inRange: {
              color: [
                "#313695",
                "#74add1",
                "#e0f3f8",
                "#fdae61",
                "#f46d43",
                "#a50026",
              ],
            },
          },
          xAxis3D: {
            type: "value",
            name: scanX.value,
            min: "dataMin",
            max: "dataMax",
          },
          yAxis3D: {
            type: "value",
            name: scanY.value,
            min: "dataMin",
            max: "dataMax",
          },

          // 使用处理好的轴名称 (MW)
          zAxis3D: {
            type: "value",
            name: axisName,
            min: "dataMin",
            max: "dataMax",
          },

          grid3D: {
            viewControl: { projection: "perspective" },
            boxWidth: 100,
            boxDepth: 100,
            boxHeight: 80,
          },
          series: [
            {
              type: "surface",
              data: scaledSurfaceData,
              wireframe: { show: false },
            },
          ],
        },
        true,
      );

      message.success("空间矩阵渲染完毕");
    } else {
      message.error(result.detail);
    }
  } catch (error) {
    message.error("计算异常或超时");
  }
};

const handleResize = () => {
  [
    parallelChart,
    paretoChart,
    boxplotChart,
    surfaceChart,
    gaugeChart,
    globalImportanceChart,
    shapWaterfallChart,
    correlationHeatmapChart,
  ].forEach((c) => c && c.resize());
};

// ✨ 新增：通用全屏切换函数
const toggleFullscreen = (e) => {
  const card = e.currentTarget.closest(".modern-card, .chart-card");
  if (!card) return;

  if (!document.fullscreenElement) {
    // 核心修复：在进入全屏前，强制赋予当前的主题 Class，打破 #top-layer 导致的 CSS 变量失效
    card.classList.remove("light-mode", "dark-mode");
    card.classList.add(isDarkMode.value ? "dark-mode" : "light-mode");

    card.requestFullscreen().catch((err) => {
      message.error(`无法进入全屏: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
};

// ✨ 新增：全屏动画需要时间，延迟 100ms 重绘图表防错位
const handleFullscreenChange = () => {
  handleResize(); // 立即触发
  setTimeout(handleResize, 100); // 动画早期
  setTimeout(handleResize, 300); // 动画晚期
  setTimeout(handleResize, 600); // 动画彻底结束后兜底
};

onMounted(() => {
  window.addEventListener("resize", handleResize);
  document.addEventListener("fullscreenchange", handleFullscreenChange); // 👈 监听全屏动作
});
onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
  [
    parallelChart,
    paretoChart,
    boxplotChart,
    surfaceChart,
    gaugeChart,
    globalImportanceChart,
    shapWaterfallChart,
    correlationHeatmapChart,
  ].forEach((c) => c && c.dispose());
});

watch(isDarkMode, () => {
  const tc = getThemeColor();
  const gc = getGridColor();
  const tooltip = getTooltipStyle();

  if (parallelChart) {
    updateParallelChartAxes();
    parallelChart.setOption({ tooltip: getTooltipStyle() }); // 显式更新 tooltip
  }
  if (paretoChart) {
    paretoChart.setOption({
      xAxis: {
        axisLabel: { color: tc },
        splitLine: { lineStyle: { color: gc } },
      },
      yAxis: {
        axisLabel: { color: tc },
        splitLine: { lineStyle: { color: gc } },
      },
      tooltip,
    });
  }
  if (boxplotChart) {
    // 箱线图也需要显式更新 tooltip 样式，防止文字在白底上看不见
    boxplotChart.setOption({
      xAxis: { axisLabel: { color: tc } },
      yAxis: {
        axisLabel: { color: tc },
        splitLine: { lineStyle: { color: gc } },
      },
      tooltip: getTooltipStyle(),
    });
  }
  if (gaugeChart) {
    const opts = gaugeChart.getOption();
    if (opts.series) {
      opts.series.forEach((s) => {
        if (s.title) s.title.color = tc;
        if (s.axisLabel) s.axisLabel.color = tc;
      });
      gaugeChart.setOption(opts);
    }
  }
  if (surfaceChart)
    surfaceChart.setOption({ title: { textStyle: { color: tc } }, tooltip });

  if (globalImportanceChart) {
    globalImportanceChart.setOption({
      xAxis: {
        axisLabel: { color: tc },
        splitLine: { lineStyle: { color: gc } },
      },
      yAxis: { axisLabel: { color: tc } },
      series: [{ label: { color: tc } }],
      tooltip,
    });
  }
  if (shapWaterfallChart) {
    shapWaterfallChart.setOption({
      xAxis: {
        axisLabel: { color: tc },
        splitLine: { lineStyle: { color: gc } },
      },
      yAxis: { axisLabel: { color: tc } },
      tooltip,
    });
  }
  if (correlationHeatmapChart) {
    correlationHeatmapChart.setOption({
      xAxis: { axisLabel: { color: tc } },
      yAxis: { axisLabel: { color: tc } },
      series: [{ itemStyle: { borderColor: gc } }],
      tooltip,
    });
  }
});
</script>

<style scoped>
.cst-container {
  display: flex;
  min-height: 100vh;
  background-color: var(--n-body-color);
  color: var(--n-text-color);
}
.sidebar {
  position: sticky;
  /* 如果你的顶部导航栏是 fixed 固定悬浮的，这里需要写上顶栏的高度，比如 top: 64px;
     如果顶栏是随页面滚动的，保持 top: 0; 即可 */
  top: 0;

  /* 关键修改：减去顶部导航栏的高度（请根据你的实际情况微调 64px 这个数值）*/
  height: calc(100vh - 64px);

  box-sizing: border-box;
  flex: 0 0 350px;
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
.modern-card,
.chart-card {
  border-radius: 8px;
  background-color: var(--n-card-color);
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
}
.card-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--n-text-color);
}
.inner-panel {
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.1);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  margin-top: 8px;
}
.action-area {
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid var(--n-border-color);
  background: transparent;
}
.start-btn {
  width: 100%;
  font-size: 15px;
  font-weight: bold;
  letter-spacing: 1px;
  border-radius: 8px;
  height: 50px;
}

:deep(.n-form-item) {
  margin-bottom: 12px;
}
:deep(.n-form-item .n-form-item-label) {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 6px;
}

.main-content {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  background-color: var(--n-body-color);
  min-width: 0;
}
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed var(--n-border-color);
  border-radius: 12px;
  color: var(--n-text-color-3);
  font-size: 16px;
  margin-top: 10px;
}

.param-bound-box {
  padding: 8px 12px;
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  background-color: var(--n-color);
}
.param-name {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 6px;
  color: var(--n-text-color-2);
}

.card-header {
  padding: 10px 14px;
  border-bottom: 1px solid var(--n-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--n-action-color);
  border-radius: 8px 8px 0 0;
}
.echarts-container {
  position: relative !important;
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0 !important;
  min-width: 0 !important;
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

/* 2. 🚀 终极防撑破大法：强制 ECharts 注入的真实画布容器绝对定位，彻底脱离文档流 */
.chart-card,
.modern-card {
  min-width: 0 !important;
  min-height: 0 !important;
}

/* 穿透修改 Naive UI 卡片内置的内容层，强制允许无底线缩小 */
:deep(.n-card__content) {
  min-width: 0 !important;
  min-height: 0 !important;
}

/* 🚀 修复全屏黑底问题：强制指定明暗模式的物理颜色，杜绝变量失效 */
/* 🚀 修复全屏背景：引入通透的亚克力毛玻璃质感，杜绝变量失效 */
.modern-card.light-mode:fullscreen,
.chart-card.light-mode:fullscreen {
  /* ✨ 浅色模式：半透明背景 */
  background-color: rgba(255, 255, 255, 0.8) !important;
}

.modern-card.dark-mode:fullscreen,
.chart-card.dark-mode:fullscreen {
  /* ✨ 深色模式：半透明背景 */
  background-color: rgba(24, 24, 28, 0.8) !important;
}

/* 🚀 干掉浏览器原生的全屏纯黑幕布 */
.modern-card:fullscreen::backdrop,
.chart-card:fullscreen::backdrop {
  background-color: transparent !important;
}

/* 原有的全屏基础布局属性 + 亚克力滤镜 */
.modern-card:fullscreen,
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
  /* ✨ 核心：为全屏卡片添加全局模糊滤镜 */
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

/* 确保全屏时 ECharts 容器能自动撑满剩余空间 */
.modern-card:fullscreen .echarts-container,
.chart-card:fullscreen .echarts-container {
  flex: 1 !important;
  height: 100% !important;
  min-height: 0;
}

.text-sub {
  color: var(--n-text-color-3);
}
.text-neon-white,
.text-neon-green,
.text-neon-orange,
.text-neon-blue {
  font-size: 28px;
  font-weight: bold;
  font-family:
    "JetBrains Mono", "Fira Code", "Roboto Mono", Consolas, monospace;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
}
.text-neon-white {
  color: var(--n-text-color);
}
.text-neon-green {
  color: #10b981;
}
.text-neon-orange {
  color: #f59e0b;
}
.text-neon-blue {
  color: #3b82f6;
}
</style>
