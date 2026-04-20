<template>
  <div class="cst-container" :class="isDarkMode ? 'dark-mode' : 'light-mode'">
    <div class="sidebar">
      <div class="sidebar-header">
        <n-space align="center">
          <h2 style="margin: 0; font-weight: 700; letter-spacing: 1px">
            联合仿真配置
          </h2>
        </n-space>
        <n-space align="center">
          <n-tag
            :type="isRunning ? 'primary' : 'default'"
            round
            :bordered="false"
            size="large"
          >
            {{ isRunning ? "引擎运转中" : "系统空闲" }}
          </n-tag>
        </n-space>
      </div>

      <n-scrollbar style="max-height: calc(100vh - 180px); padding-right: 16px">
        <n-form label-placement="top" :show-feedback="false">
          <n-card class="modern-card" size="small">
            <template #header
              ><span class="card-title">📂 项目与任务</span></template
            >
            <n-form-item label="快速回顾历史优化">
              <n-select
                v-model:value="config.selectedHistoryTask"
                :options="historyTaskOptions"
                placeholder="选择一个已完成的任务..."
                @update:value="loadHistoricalTask"
              />
            </n-form-item>
            <n-form-item label="CST 项目路径">
              <div class="vertical-group">
                <n-select
                  v-model:value="config.selectedHistoryPath"
                  :options="historyPathOptions"
                  placeholder="从历史记录快速选择"
                  @update:value="syncPath"
                />
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
                  <n-button type="primary" secondary @click="triggerFileInput">
                    📁 本地浏览
                  </n-button>
                </n-input-group>
              </div>
            </n-form-item>
            <n-form-item label="当前优化任务名称" style="margin-top: 16px">
              <div class="vertical-group">
                <n-select
                  v-model:value="config.selectedHistoryTask"
                  :options="historyTaskOptions"
                  placeholder="覆盖历史任务"
                  @update:value="syncTask"
                />
                <n-input
                  v-model:value="config.taskName"
                  placeholder="例如: Run_001"
                  clearable
                />
              </div>
            </n-form-item>
          </n-card>

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
              >+ 新增优化变量</n-button
            >

            <div
              v-for="(item, index) in config.paramsList"
              :key="item.id"
              class="var-item"
            >
              <n-grid
                :x-gap="12"
                :y-gap="12"
                :cols="24"
                style="align-items: center"
              >
                <n-gi :span="7"
                  ><n-input
                    v-model:value="item.name"
                    placeholder="变量名"
                    clearable
                /></n-gi>
                <n-gi :span="5"
                  ><n-input-number v-model:value="item.min" :show-button="false"
                    ><template #prefix
                      ><span class="inner-label">Min</span></template
                    ></n-input-number
                  ></n-gi
                >
                <n-gi :span="5"
                  ><n-input-number v-model:value="item.max" :show-button="false"
                    ><template #prefix
                      ><span class="inner-label">Max</span></template
                    ></n-input-number
                  ></n-gi
                >
                <n-gi :span="5" style="display: flex; justify-content: center">
                  <n-switch
                    v-model:value="item.opt"
                    size="medium"
                    @update:value="sortVariables"
                  >
                    <template #checked>Opt (优化)</template>
                    <template #unchecked>Fix (固定)</template>
                  </n-switch>
                </n-gi>
                <n-gi :span="2" style="text-align: right"
                  ><n-button
                    type="error"
                    quaternary
                    circle
                    size="small"
                    @click="removeVariable(index)"
                    >🗑️</n-button
                  ></n-gi
                >
              </n-grid>
              <div v-if="!item.opt" class="var-fix-row">
                <span class="fix-label">固定调节:</span>
                <n-slider
                  v-model:value="item.val"
                  :min="item.min"
                  :max="item.max"
                  :step="0.01"
                  style="flex: 1; margin: 0 20px"
                />
                <n-input-number
                  v-model:value="item.val"
                  style="width: 100px"
                  :show-button="false"
                  size="small"
                />
              </div>
            </div>
          </n-card>

          <n-collapse
            :default-expanded-names="['env', 'paths', 'freq', 'power', 'eff']"
          >
            <n-collapse-item title="全局环境设置" name="env">
              <n-form-item label="稳态起始时间 (ns)"
                ><n-input-number
                  v-model:value="config.env.stableTime"
                  :step="1.0"
                  style="width: 50%"
              /></n-form-item>
            </n-collapse-item>

            <n-collapse-item title="📂 CST 结果树路径 (全局读取)" name="paths">
              <div class="inner-panel">
                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item label="功率 (AVGpower) 路径">
                      <n-input v-model:value="config.targets.power.path" />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item label="效率 (EFF) 路径">
                      <n-input v-model:value="config.targets.eff.path" />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label>频谱 (FFT) 路径 </template>
                      <n-input v-model:value="config.targets.freq.path" />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >主模端口路径
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >非优化项，仅作波形审查台读取</n-tooltip
                        ></template
                      >
                      <n-input-group>
                        <n-input v-model:value="config.targets.mainMode.path" />
                        <n-button
                          :type="
                            config.targets.mainMode.enable
                              ? 'primary'
                              : 'default'
                          "
                          @click="
                            config.targets.mainMode.enable =
                              !config.targets.mainMode.enable
                          "
                        >
                          {{
                            config.targets.mainMode.enable
                              ? "读取: 开"
                              : "读取: 关"
                          }}
                        </n-button>
                      </n-input-group>
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>

            <n-collapse-item title="频率 (线性梯度机制)" name="freq">
              <template #header-extra>
                <n-switch
                  v-model:value="config.targets.freq.enable"
                  @click.stop
                  size="small"
                />
              </template>
              <div v-if="config.targets.freq.enable" class="inner-panel">
                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >目标频率 (GHz)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >期望的工作频率</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.freq.target"
                        :step="0.01"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >盲区半径 ±(GHz)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >在此半径内不进行梯度惩罚</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.freq.blindGap"
                        :step="0.01"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                </n-grid>

                <n-divider
                  title-placement="left"
                  dashed
                  style="
                    margin: 8px 0;
                    font-size: 13px;
                    color: var(--n-text-color-3);
                  "
                  >判据与惩罚设置</n-divider
                >

                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >杂波罚分系数
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >抑制无用杂波的系数</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.freq.clutterPenalty"
                        :step="100"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >频率偏移梯度 k
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >偏离盲区后的线性惩罚斜率</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.freq.decayK"
                        :step="1"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >频率错误重罚
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >未找到有效频率峰值时的基础惩罚</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.freq.penaltyBase"
                        :step="1000"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>

            <n-collapse-item title="功率目标门控" name="power">
              <template #header-extra>
                <n-switch
                  v-model:value="config.targets.power.enable"
                  @click.stop
                  size="small"
                />
              </template>
              <div v-if="config.targets.power.enable" class="inner-panel">
                <n-tabs
                  type="segment"
                  v-model:value="config.targets.power.mode"
                  style="width: 260px; margin-bottom: 16px"
                >
                  <n-tab-pane name="max" tab="最大化"></n-tab-pane>
                  <n-tab-pane name="target" tab="逼近定值"></n-tab-pane>
                </n-tabs>

                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label>
                        {{
                          config.targets.power.mode === "target"
                            ? "目标功率 (MW)"
                            : "功率归一化基准 (MW)"
                        }}
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >{{
                            config.targets.power.mode === "target"
                              ? "算法将尝试锁定在此功率"
                              : "用于多目标权重平衡，请填写该波段的期望峰值"
                          }}</n-tooltip
                        >
                      </template>
                      <n-input-number
                        v-model:value="config.targets.power.target"
                        :step="10"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >功率淘汰死区阈值 (MW)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >低于此值的波形将被直接淘汰</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.power.deadThresh"
                        :step="1.0"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >功率振荡误差 (%)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >波形稳态后的最大允许波动率</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.power.fluc"
                        :min="0"
                        :max="50"
                        :step="1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.power.fluc"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>

                  <n-gi v-if="config.targets.power.mode === 'target'">
                    <n-form-item>
                      <template #label
                        >目标逼近容差 (%)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >在此误差范围内不扣分 (形成平顶区)</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.power.tolerance"
                        :min="0"
                        :max="50"
                        :step="1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.power.tolerance"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >权重
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >适应度计算时的权重分配</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.power.weight"
                        :min="0.1"
                        :max="10"
                        :step="0.1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.power.weight"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>

            <n-collapse-item title="效率目标门控" name="eff">
              <template #header-extra>
                <n-switch
                  v-model:value="config.targets.eff.enable"
                  @click.stop
                  size="small"
                />
              </template>
              <div v-if="config.targets.eff.enable" class="inner-panel">
                <n-space align="center" style="margin-bottom: 16px" :size="24">
                  <n-tabs
                    type="segment"
                    v-model:value="config.targets.eff.mode"
                    style="width: 260px"
                  >
                    <n-tab-pane name="max" tab="最大化"></n-tab-pane>
                    <n-tab-pane name="target" tab="逼近定值"></n-tab-pane>
                  </n-tabs>

                  <n-switch v-model:value="config.targets.eff.checkPhys">
                    <template #checked>物理合理性判决: 开启</template>
                    <template #unchecked>物理合理性判决: 关闭</template>
                  </n-switch>
                </n-space>

                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label>
                        {{
                          config.targets.eff.mode === "target"
                            ? "目标效率 (%)"
                            : "效率归一化基准 (%)"
                        }}
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >{{
                            config.targets.eff.mode === "target"
                              ? "算法将尝试锁定在此效率"
                              : "用于平衡权重，通常设为 100 即可"
                          }}</n-tooltip
                        >
                      </template>
                      <n-input-number
                        v-model:value="config.targets.eff.target"
                        :step="1"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >效率淘汰死区阈值 (%)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >低于此效率的波形将被直接淘汰</n-tooltip
                        ></template
                      >
                      <n-input-number
                        v-model:value="config.targets.eff.deadThresh"
                        :step="1.0"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>

                  <n-gi>
                    <n-form-item>
                      <template #label
                        >效率振荡误差 (%)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >波形稳态后的最大允许波动率</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.eff.fluc"
                        :min="0"
                        :max="50"
                        :step="1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.eff.fluc"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>

                  <n-gi v-if="config.targets.eff.mode === 'target'">
                    <n-form-item>
                      <template #label
                        >目标逼近容差 (%)
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >在此误差范围内不扣分 (形成平顶区)</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.eff.tolerance"
                        :min="0"
                        :max="50"
                        :step="1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.eff.tolerance"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label
                        >权重
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >适应度计算时的权重分配</n-tooltip
                        ></template
                      >
                      <n-slider
                        v-model:value="config.targets.eff.weight"
                        :min="0.1"
                        :max="10"
                        :step="0.1"
                        style="flex: 1; margin-right: 12px"
                      />
                      <n-input-number
                        v-model:value="config.targets.eff.weight"
                        size="small"
                        style="width: 70px"
                        :show-button="false"
                      />
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>

            <n-collapse-item title="核心优化引擎设置" name="algo">
              <div class="inner-panel">
                <n-form-item label="驱动算法 (Optimizer)">
                  <n-select
                    v-model:value="config.algo.type"
                    :options="[
                      {
                        label: '遗传算法 (SAEA-GA) - 全局推演',
                        value: 'SAEA-GA',
                      },
                      { label: '粒子群优化 (PSO) - 极速微调', value: 'PSO' },
                      {
                        label: '贝叶斯优化 (BO) - 高效少样本探索',
                        value: 'BO',
                      },
                    ]"
                  />
                </n-form-item>

                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label>
                        {{
                          config.algo.type === "BO"
                            ? "单次评估批次 (Batch)"
                            : "种群/粒子规模 (Pop)"
                        }}
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >每一代/批包含的仿真个体数</n-tooltip
                        >
                      </template>
                      <n-input-number
                        v-model:value="config.algo.nPop"
                        :min="1"
                        :max="200"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item>
                      <template #label>
                        {{
                          config.algo.type === "BO"
                            ? "优化总轮次 (Rounds)"
                            : "迭代代数 (Gen)"
                        }}
                        <n-tooltip trigger="hover"
                          ><template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >总共进行的代数/轮次</n-tooltip
                        >
                      </template>
                      <n-input-number
                        v-model:value="config.algo.nGen"
                        :min="1"
                        :max="200"
                        style="width: 100%"
                      />
                    </n-form-item>
                  </n-gi>
                </n-grid>

                <div
                  style="
                    font-size: 12px;
                    color: #10b981;
                    margin-top: -8px;
                    margin-bottom: 12px;
                    text-align: right;
                    font-weight: bold;
                  "
                >
                  预计总共将调用 CST 仿真
                  {{ config.algo.nPop * config.algo.nGen }} 次
                </div>

                <n-collapse style="margin-top: 8px">
                  <n-collapse-item title="算法超参数微调" name="algo-advanced">
                    <div v-if="config.algo.type === 'SAEA-GA'">
                      <n-grid :x-gap="24" :cols="2">
                        <n-gi>
                          <n-form-item label="交叉率 (Pc)">
                            <n-slider
                              v-model:value="config.algo.ga.pc"
                              :min="0"
                              :max="1"
                              :step="0.01"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.ga.pc"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                          <n-form-item label="变异率 (Pm)">
                            <n-slider
                              v-model:value="config.algo.ga.pm"
                              :min="0"
                              :max="1"
                              :step="0.01"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.ga.pm"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                        </n-gi>
                        <n-gi>
                          <n-form-item label="交叉算子">
                            <n-tabs
                              type="segment"
                              v-model:value="config.algo.ga.recCode"
                              size="small"
                            >
                              <n-tab-pane name="xovdp" tab="两点"></n-tab-pane>
                              <n-tab-pane name="xovud" tab="均匀"></n-tab-pane>
                              <n-tab-pane name="xovsp" tab="单点"></n-tab-pane>
                            </n-tabs>
                          </n-form-item>
                          <n-form-item label="变异策略">
                            <div
                              style="
                                display: flex;
                                flex-direction: column;
                                width: 100%;
                                gap: 12px;
                              "
                            >
                              <n-radio-group
                                v-model:value="config.algo.ga.useAutoMut"
                                size="small"
                              >
                                <n-radio-button :value="true"
                                  >自适应</n-radio-button
                                >
                                <n-radio-button :value="false"
                                  >固定</n-radio-button
                                >
                              </n-radio-group>
                              <div
                                v-if="config.algo.ga.useAutoMut"
                                style="
                                  padding: 12px 14px 10px 14px;
                                  background: rgba(0, 0, 0, 0.15);
                                  border-radius: 8px;
                                  border: 1px dashed var(--n-border-color);
                                "
                              >
                                <n-slider
                                  v-model:value="config.algo.ga.autoMutRange"
                                  range
                                  :step="1"
                                  :min="0"
                                  :max="100"
                                />
                              </div>
                              <n-tabs
                                v-else
                                type="segment"
                                v-model:value="config.algo.ga.mutCode"
                                size="small"
                              >
                                <n-tab-pane
                                  name="mutuni"
                                  tab="均匀"
                                ></n-tab-pane>
                                <n-tab-pane
                                  name="mutgau"
                                  tab="高斯"
                                ></n-tab-pane>
                                <n-tab-pane
                                  name="mutbga"
                                  tab="布列德"
                                ></n-tab-pane>
                              </n-tabs>
                            </div>
                          </n-form-item>
                        </n-gi>
                      </n-grid>
                    </div>

                    <div v-if="config.algo.type === 'PSO'">
                      <n-grid :x-gap="24" :cols="1">
                        <n-gi>
                          <n-form-item label="惯性权重 (Inertia Weight, w)">
                            <n-slider
                              v-model:value="config.algo.pso.w"
                              :min="0.1"
                              :max="1.5"
                              :step="0.05"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.pso.w"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                          <n-form-item label="自我认知因子 (Cognitive, c1)">
                            <n-slider
                              v-model:value="config.algo.pso.c1"
                              :min="0.1"
                              :max="3.0"
                              :step="0.1"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.pso.c1"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                          <n-form-item label="社会认知因子 (Social, c2)">
                            <n-slider
                              v-model:value="config.algo.pso.c2"
                              :min="0.1"
                              :max="3.0"
                              :step="0.1"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.pso.c2"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                        </n-gi>
                      </n-grid>
                    </div>

                    <div v-if="config.algo.type === 'BO'">
                      <n-grid :x-gap="24" :cols="2">
                        <n-gi>
                          <n-form-item>
                            <template #label>
                              采集函数策略 (Acq Function)
                              <n-tooltip trigger="hover"
                                ><template #trigger
                                  ><span style="cursor: help; margin-left: 4px"
                                    >❔</span
                                  ></template
                                >决定探索与开发的侧重</n-tooltip
                              >
                            </template>
                            <div
                              style="
                                display: flex;
                                flex-direction: column;
                                width: 100%;
                                gap: 12px;
                              "
                            >
                              <n-radio-group
                                v-model:value="config.algo.bo.useAutoAcq"
                                size="small"
                              >
                                <n-radio-button :value="true"
                                  >自适应切换 (推荐)</n-radio-button
                                >
                                <n-radio-button :value="false"
                                  >固定策略</n-radio-button
                                >
                              </n-radio-group>

                              <div
                                v-if="config.algo.bo.useAutoAcq"
                                style="
                                  padding: 10px 12px;
                                  background: rgba(16, 185, 129, 0.1);
                                  border-radius: 8px;
                                  border: 1px dashed #10b981;
                                  font-size: 12px;
                                  color: var(--n-text-color-3);
                                "
                              >
                                <b>智能两段式:</b> 前 50% 强制使用 LCB(高kappa)
                                全图拓荒，后 50% 自动切换为 EI(低xi) 极限收敛。
                              </div>

                              <n-tabs
                                v-else
                                type="segment"
                                v-model:value="config.algo.bo.acqFunc"
                                size="small"
                              >
                                <n-tab-pane
                                  name="EI"
                                  tab="EI (精准榨取)"
                                ></n-tab-pane>
                                <n-tab-pane
                                  name="LCB"
                                  tab="LCB (全图探索)"
                                ></n-tab-pane>
                              </n-tabs>
                            </div>
                          </n-form-item>
                        </n-gi>
                        <n-gi>
                          <n-form-item label="探索系数 (LCB Kappa)">
                            <n-slider
                              v-model:value="config.algo.bo.kappa"
                              :min="0.1"
                              :max="5.0"
                              :step="0.1"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.bo.kappa"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                          <n-form-item label="提升门槛 (EI Xi)">
                            <n-slider
                              v-model:value="config.algo.bo.xi"
                              :min="0.0"
                              :max="0.5"
                              :step="0.01"
                              style="flex: 1; margin-right: 12px"
                            />
                            <n-input-number
                              v-model:value="config.algo.bo.xi"
                              size="small"
                              style="width: 70px"
                              :show-button="false"
                            />
                          </n-form-item>
                        </n-gi>
                      </n-grid>
                    </div>
                  </n-collapse-item>

                  <n-collapse-item
                    v-if="config.algo.type !== 'BO'"
                    title="初始优良基因注入 (先验知识)"
                    name="algo-inject"
                  >
                    <div
                      style="
                        font-size: 13px;
                        color: var(--n-text-color-3);
                        margin-bottom: 12px;
                        line-height: 1.5;
                      "
                    >
                      在此处粘贴已知较好的参数组
                      (JSON格式)，将强制作为第1代的一个个体，加速收敛。
                    </div>
                    <n-button
                      secondary
                      type="default"
                      size="small"
                      style="margin-bottom: 16px"
                      @click="generateInjectTemplate"
                    >
                      📄 生成当前变量模板
                    </n-button>
                    <n-form-item label="粘贴参数 JSON">
                      <n-input
                        v-model:value="config.algo.injectJson"
                        type="textarea"
                        placeholder='例如: {"radius_a": 50.0}'
                        :autosize="{ minRows: 4, maxRows: 8 }"
                        style="font-family: monospace"
                      />
                    </n-form-item>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-collapse-item>
          </n-collapse>
        </n-form>
        <div style="height: 40px"></div>
      </n-scrollbar>

      <div class="action-area" style="display: flex; gap: 16px">
        <n-button
          v-if="!isRunning"
          type="primary"
          size="large"
          class="start-btn"
          style="flex: 1"
          @click="startOptimization"
        >
          启动联合优化
        </n-button>
        <n-button
          v-else
          type="error"
          size="large"
          class="start-btn"
          style="flex: 1"
          @click="stopOptimization"
        >
          强制终止运转 (Kill)
        </n-button>
      </div>
    </div>

    <div class="main-content">
      <n-grid :x-gap="16" :cols="4" style="margin-bottom: 16px">
        <n-gi>
          <n-card class="metric-card" size="small">
            <n-statistic label="优化进度 (Gen)">
              <div style="display: flex; align-items: center; min-height: 45px">
                <n-progress
                  type="line"
                  :percentage="
                    config.algo.nGen
                      ? Math.round((currentGen / config.algo.nGen) * 100)
                      : 0
                  "
                  :height="12"
                  status="info"
                  style="width: 100%"
                >
                  <span
                    style="
                      font-weight: 800;
                      font-size: 24px;
                      color: var(--n-text-color);
                      white-space: nowrap;
                      margin-left: 14px;
                    "
                  >
                    {{ currentGen }}
                    <span
                      class="text-sub"
                      style="font-size: 24px; font-weight: 600"
                      >/ {{ config.algo.nGen }}</span
                    >
                  </span>
                </n-progress>
              </div>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi
          ><n-card class="metric-card" size="small"
            ><n-statistic label="最优个体效率 (Top Score)"
              ><span class="text-neon-green">{{ bestEff }}</span>
              <span class="text-sub">%</span></n-statistic
            ></n-card
          ></n-gi
        >
        <n-gi
          ><n-card class="metric-card" size="small"
            ><n-statistic label="最优个体功率 (Top Score)"
              ><span class="text-neon-orange">{{ bestPower }}</span>
              <span class="text-sub">MW</span></n-statistic
            ></n-card
          ></n-gi
        >
        <n-gi
          ><n-card class="metric-card" size="small"
            ><n-statistic label="最优个体频率 (Top Score)"
              ><span class="text-neon-blue">{{ bestFreq }}</span>
              <span class="text-sub">GHz</span></n-statistic
            ></n-card
          ></n-gi
        >
      </n-grid>
      <div class="middle-row">
        <n-card
          class="chart-card model-card"
          style="flex: 25"
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
            <div
              class="hologram-scanner"
              v-if="!modelImageUrl && !isFetchingImage"
            >
              <span class="placeholder-text">AWAITING .dib ...</span>
            </div>
            <div class="hologram-scanner" v-else-if="isFetchingImage">
              <div class="scanner-line"></div>
              <span class="placeholder-text" style="color: #3b82f6"
                >CONNECTING...</span
              >
            </div>
            <img v-else :src="modelImageUrl" class="model-image" />
          </div>
        </n-card>

        <n-card
          class="chart-card wave-card"
          style="flex: 50"
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
                    >| Gen: {{ inspectGen }} - No.{{ inspectInd }}</span
                  ></span
                >

                <n-radio-group
                  v-model:value="activeWaveTab"
                  size="small"
                  @update:value="updateInspectorChart"
                >
                  <n-radio-button value="power">功率</n-radio-button>
                  <n-radio-button value="eff">效率</n-radio-button>
                  <n-radio-button value="mainMode">主模波形</n-radio-button>
                  <n-radio-button value="fft">频谱 (FFT)</n-radio-button>
                </n-radio-group>
              </n-space>

              <n-space align="center" :size="12" wrap style="margin-left: auto">
                <n-switch
                  v-model:value="autoTrackLatest"
                  size="small"
                  @update:value="handleAutoTrackChange"
                >
                  <template #checked>自动追踪</template>
                  <template #unchecked>停留当前</template>
                </n-switch>

                <n-input-group style="width: auto">
                  <n-input-group-label size="small" style="padding: 0 8px"
                    >Gen</n-input-group-label
                  >
                  <n-select
                    v-model:value="inspectGen"
                    :options="genOptions"
                    size="small"
                    style="width: 100px"
                    @update:value="manualSelectWave"
                    :disabled="autoTrackLatest"
                  />
                </n-input-group>

                <n-input-group style="width: auto">
                  <n-input-group-label size="small" style="padding: 0 8px"
                    >No.</n-input-group-label
                  >
                  <n-select
                    v-model:value="inspectInd"
                    :options="indOptions"
                    size="small"
                    style="width: 100px"
                    @update:value="manualSelectWave"
                    :disabled="autoTrackLatest"
                  />
                </n-input-group>
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
                  bordered="false"
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

        <n-card
          class="chart-card terminal-card"
          style="flex: 25; display: flex; flex-direction: column"
          content-style="padding: 0; display: flex; flex-direction: column; flex: 1; min-height: 0;"
        >
          <div class="card-header">
            <span class="card-title">Engine Log</span>
          </div>
          <div class="log-window" ref="logWindowRef">
            <div v-for="(log, index) in logs" :key="index" class="log-item">
              <span class="log-prefix">root@saea:~$</span>
              <span v-html="log"></span>
            </div>
          </div>
        </n-card>
      </div>

      <div class="bottom-row">
        <n-card
          class="chart-card trend-card"
          style="flex: 1"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div class="card-header">
            <span class="card-title">📈 迭代最优收敛趋势</span>
            <n-space align="center" :size="12">
              <n-checkbox-group
                v-model:value="selectedTrendLines"
                @update:value="updateTrendVisibility"
              >
                <n-space :size="8">
                  <n-checkbox value="eff" label="效率" />
                  <n-checkbox value="power" label="功率" />
                  <n-checkbox value="freq" label="频率" />
                </n-space>
              </n-checkbox-group>
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
          <div style="flex: 1; position: relative; min-width: 0; min-height: 0">
            <div
              ref="trendChartRef"
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

        <n-card
          class="chart-card scatter-card"
          style="flex: 1"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div class="card-header">
            <span class="card-title"
              >帕累托散点云图
              <span style="font-size: 12px" class="text-sub"
                >(红:高分 | 蓝:低分)</span
              ></span
            >
            <n-space align="center">
              <n-slider
                v-model:value="scatterFilterEff"
                :min="0"
                :max="100"
                :step="1"
                style="width: 80px"
                @update:value="refreshScatterFilter"
              />
              <span
                style="font-size: 12px; font-weight: bold"
                class="text-neon-green"
                >{{ scatterFilterEff }}%</span
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
          <div style="flex: 1; position: relative; min-width: 0; min-height: 0">
            <div
              ref="scatterChartRef"
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
    </div>
  </div>
</template>

<script setup>
import {
  NIcon,
  useMessage,
  useDialog,
  NCheckboxGroup,
  NCheckbox,
  NNumberAnimation,
} from "naive-ui";
import {
  ref,
  reactive,
  onMounted,
  onUnmounted,
  nextTick,
  computed,
  watch,
  inject,
} from "vue";
import { Maximize } from "lucide-vue-next";
import * as echarts from "echarts";
import axios from "axios";

const getThemeColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.65)" : "rgba(0, 0, 0, 0.65)";
const getGridColor = () =>
  isDarkMode.value ? "rgba(255, 255, 255, 0.04)" : "rgba(0, 0, 0, 0.08)";

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

const API_BASE = "/api"; // HTTP 走 Vite 代理
// ✨ 原生 WebSocket 必须用动态地址。这里修复了原先 WS_BASE 未定义的 Bug！
const WS_BASE = `ws://${window.location.host}/ws`;
const message = useMessage();
const dialog = useDialog();
const currentTaskId = ref(null);
const generateId = () => Math.random().toString(36).substr(2, 9);
const stopOptimization = async () => {
  if (!currentTaskId.value) return;
  try {
    logs.value.push(
      "<span style='color:#ef4444;'>[INFO]</span> 正在发送强制终止指令...",
    );
    scrollToBottom();

    // 🌟 修复：替换为真实的后端硬编码地址
    const res = await axios.post(
      `${API_BASE}/stop_optimization/${currentTaskId.value}`,
    );

    if (res.data.status === "success") {
      message.success("🛑 终止指令已下发，将在当前个体算完后安全退出...");
    } else {
      message.error(res.data.message);
    }
  } catch (e) {
    console.error(e);
    message.error("发送终止指令失败，请检查后端是否连接正常");
  }
};
const isDarkMode = inject("globalTheme", ref(true));
const islandState = inject("islandState");
const activeWaveTab = ref("power");
const historyPathOptions = [
  {
    label: "F:\\cst files\\ACO for report\\ACO FR.cst",
    value: "F:\\cst files\\ACO for report\\ACO FR.cst",
  },
];
const historyTaskOptions = ref([]);
const config = reactive({
  selectedHistoryPath: null,
  cstPath: "F:\\cst files\\ACO for report\\ACO FR.cst",
  selectedHistoryTask: null,
  taskName: "Run_001",
  env: { stableTime: 20.0 },
  paramsList: [
    {
      id: generateId(),
      name: "cathode_r",
      min: 6.0,
      max: 10.0,
      val: 10.0,
      opt: true,
    },
    {
      id: generateId(),
      name: "Va",
      min: 150000,
      max: 250000,
      val: 200000,
      opt: true,
    },
    {
      id: generateId(),
      name: "anode_r",
      min: 20.0,
      max: 30.0,
      val: 25.0,
      opt: true,
    },
    {
      id: generateId(),
      name: "cavity_d",
      min: 2.0,
      max: 5.0,
      val: 3.5,
      opt: true,
    },
  ],
  targets: {
    freq: {
      enable: true,
      path: "Tables\\1D Results\\FFT",
      target: 2.4,
      blindGap: 0.05,
      clutterPenalty: -3000,
      decayK: 10.0,
      penaltyBase: -10000,
    },
    power: {
      enable: true,
      mode: "max",
      path: "Tables\\1D Results\\AVGpower",
      target: 800,
      deadThresh: 1.0,
      weight: 1.0,
      fluc: 10,
      tolerance: 10,
    },
    eff: {
      enable: true,
      mode: "max",
      path: "Tables\\1D Results\\EFF",
      checkPhys: true,
      target: 50.0,
      deadThresh: 1.0,
      weight: 6.0,
      fluc: 15,
      tolerance: 10,
    },
    mainMode: { enable: true, path: "1D Results\\Port signals\\o2(1),pic" },
  },
  algo: {
    type: "SAEA-GA", // 新增：默认选中的核心算法
    nPop: 10, // 公共：种群规模 / BO的伪批次大小
    nGen: 50, // 公共：进化代数 / BO的伪迭代数
    injectJson: "", // 公共：基因注入

    // GA 专属参数
    ga: {
      recCode: "xovdp",
      pc: 0.7,
      mutCode: "mutuni",
      pm: 0.25,
      useAutoMut: false,
      autoMutRange: [30, 70],
    },

    // PSO 专属参数
    pso: {
      w: 0.8, // 惯性权重
      c1: 1.5, // 自我认知
      c2: 1.5, // 社会认知
    },

    // BO 专属参数
    bo: {
      acqFunc: "EI", // 采集函数
      useAutoAcq: true, // ✨ 新增：默认开启你的天才双段式策略
      kappa: 2.5, // 探索系数 (LCB)
      xi: 0.01, // 期望提升阈值 (EI)
    },
  },
});

const generateInjectTemplate = () => {
  const template = {};
  // 提取当前勾选了 Opt 的变量
  config.paramsList.forEach((p) => {
    if (p.opt) {
      template[p.name] = Number(p.val.toFixed(2));
    }
  });
  // 格式化为 JSON 字符串并写入输入框
  config.algo.injectJson = JSON.stringify(template, null, 2);
  message.success("✅ 变量模板已生成，请在此基础上修改数值");
};

const tryLoadConfig = async (path) => {
  if (!path) return;
  try {
    const res = await axios.post(`${API_BASE}/load_config`, { cstPath: path });
    if (res.data.status === "success") {
      const saved = res.data.config;

      // ⚠️ 修复点：使用对象展开语法进行浅层或深层合并，防止抹杀前端新增的默认字段
      if (saved.taskName) config.taskName = saved.taskName;
      if (saved.paramsList) config.paramsList = saved.paramsList;

      // 合并全局环境设置
      if (saved.env) {
        config.env = { ...config.env, ...saved.env };
      }

      // 深度合并 Targets（如果后期有加新的目标参数，旧配置也不会把它们搞丢）
      if (saved.targets) {
        if (saved.targets.freq)
          config.targets.freq = {
            ...config.targets.freq,
            ...saved.targets.freq,
          };
        if (saved.targets.power)
          config.targets.power = {
            ...config.targets.power,
            ...saved.targets.power,
          };
        if (saved.targets.eff)
          config.targets.eff = { ...config.targets.eff, ...saved.targets.eff };
        if (saved.targets.mainMode)
          config.targets.mainMode = {
            ...config.targets.mainMode,
            ...saved.targets.mainMode,
          };
      }

      // ✨ 最关键的修复点：合并算法配置
      if (saved.algo) {
        // 如果旧配置中没有 useAutoMut 等字段，就会原封不动保留前端 config.algo 中的默认值 [30, 70]
        config.algo = { ...config.algo, ...saved.algo };
      }

      message.success(`📂 已自动加载专属配置`);
      sortVariables(); // 重新把优化变量排在前面
    }
  } catch (err) {
    console.error("加载配置请求失败", err);
  }
};

// ====== 修改：触发路径变化时，调用加载函数 ======
const syncPath = (val) => {
  if (val) {
    config.cstPath = val;
    tryLoadConfig(val); // ✨ 新增了这行
    fetchModelPreview();
  }
};
const syncTask = (val) => {
  if (val) config.taskName = val;
};
const addVariable = () => {
  config.paramsList.push({
    id: generateId(),
    name: "new_var",
    min: 0.0,
    max: 10.0,
    val: 5.0,
    opt: false,
  });
};
const removeVariable = (index) => {
  config.paramsList.splice(index, 1);
};
const sortVariables = () => {
  config.paramsList.sort((a, b) => {
    if (a.opt === b.opt) return 0;
    return a.opt ? -1 : 1;
  });
};

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
        // 自动推算一个合理的 min max 范围
        let p_min = p_val === 0 ? -10.0 : p_val > 0 ? p_val * 0.5 : p_val * 1.5;
        let p_max = p_val === 0 ? 10.0 : p_val > 0 ? p_val * 1.5 : p_val * 0.5;

        config.paramsList.push({
          id: Math.random().toString(36).substr(2, 9),
          name: p_name,
          min: Number(p_min.toFixed(2)),
          max: Number(p_max.toFixed(2)),
          val: p_val,
          opt: false, // 默认不优化，由用户手动勾选
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

// ====== 修改：真正的保存配置逻辑 ======
const saveConfig = async () => {
  if (!config.cstPath) {
    message.warning("请先填写 CST 路径再保存！");
    return;
  }
  try {
    const res = await axios.post(`${API_BASE}/save_config`, config);
    if (res.data.status === "success") {
      message.success("该配置已保存！");
    }
  } catch (err) {
    message.error("保存失败，请检查后端状态。");
  }
};

// ✅ 粘贴这段全新的联动逻辑
const triggerFileInput = async () => {
  message.loading("正在唤起系统资源管理器，请在弹窗中选择...");
  try {
    // 发送 GET 请求，让后端的 Python 帮我们弹窗
    const res = await axios.get(`${API_BASE}/browse_cst`);

    if (res.data.status === "success") {
      // 完美拿到包含盘符的绝对路径！
      config.cstPath = res.data.path;

      // 触发后续联动（尝试加载该路径的历史配置，并刷新模型图）
      tryLoadConfig(config.cstPath);
      fetchModelPreview();
      message.success("✅ 已成功获取路径！");
    } else if (res.data.status === "cancelled") {
      message.info("已取消选择");
    } else {
      message.error("提取路径失败: " + res.data.message);
    }
  } catch (err) {
    console.error(err);
    message.error("无法唤起资源管理器，请检查后台 Python 是否报错！");
  }
};

const isRunning = ref(false);
const currentGen = ref(0);
const bestEff = ref("0.00");
const bestPower = ref("0.00");
const bestFreq = ref("--");
const logs = ref(["[SYSTEM] WAITING FOR SAEA TASKS."]);
const logWindowRef = ref(null);

const modelImageUrl = ref("");
const isFetchingImage = ref(false);

const allDataPool = reactive({});
const scatterDataArrayRaw = reactive([]);
const scatterFilterEff = ref(0);

const autoTrackLatest = ref(true);
const inspectGen = ref(1);
const inspectInd = ref(1);

const genOptions = computed(() =>
  Object.keys(allDataPool).map((g) => ({
    label: `Gen ${g}`,
    value: parseInt(g),
  })),
);
const indOptions = computed(() => {
  if (!allDataPool[inspectGen.value]) return [];
  return Object.keys(allDataPool[inspectGen.value]).map((i) => ({
    label: `No.${i}`,
    value: parseInt(i),
  }));
});

// 提取当前正在查看的参数组
const inspectedParams = computed(() => {
  if (
    allDataPool[inspectGen.value] &&
    allDataPool[inspectGen.value][inspectInd.value]
  ) {
    return allDataPool[inspectGen.value][inspectInd.value].params;
  }
  return null;
});

// ========================================================
// ECharts 初始化与渲染
// ========================================================
const inspectorChartRef = ref(null);
const scatterChartRef = ref(null);
const trendChartRef = ref(null);

let inspectorChart = null;
let scatterChart = null;
let trendChart = null;

const initCharts = () => {
  // ✨ 直接使用响应式的主题颜色函数
  const textColor = getThemeColor();
  const gridLineColor = getGridColor();

  const echartsGridConfig = { top: 40, right: 40, bottom: 40, left: 60 };
  const axisLineStyle = { lineStyle: { color: gridLineColor, type: "dashed" } };
  const axisLabelStyle = { color: textColor, fontFamily: "monospace" };

  // 1. 波形审查台
  if (inspectorChartRef.value) {
    inspectorChart = echarts.init(inspectorChartRef.value);
  }
  // 2. 帕累托散点云图
  if (scatterChartRef.value) {
    scatterChart = echarts.init(scatterChartRef.value);
    scatterChart.setOption({
      backgroundColor: "transparent",
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: "none",
            title: { zoom: "区域缩放", back: "还原" },
          },
          restore: { title: "还原" },
        },
        right: 15,
        top: 10,
        iconStyle: { borderColor: textColor },
      },
      dataZoom: [
        { type: "inside", xAxisIndex: 0, yAxisIndex: 0 },
        {
          type: "slider",
          xAxisIndex: 0,
          height: 15,
          bottom: 5,
          textStyle: { color: textColor },
        },
        {
          type: "slider",
          yAxisIndex: 0,
          width: 15,
          right: 5,
          textStyle: { color: textColor },
        },
      ],
      tooltip: {
        trigger: "item",
        ...getTooltipStyle(),
        // 新代码
        formatter: function (params) {
          const d = params.data;
          let paramHtml = "";
          if (d.params) {
            for (let k in d.params) {
              const val = d.params[k];
              const pConfig = config.paramsList.find((p) => p.name === k);

              // ✨ 终极判定法：抛弃对小数位数的猜测！
              // 遍历当前散点图里的所有数据点，只要发现有任何一个点的该参数值与当前 val 不同，
              // 就证明这个参数在演化中“变动”过，它绝对是个优化变量！
              const isDynamicOpt = scatterDataArrayRaw.some(
                (p) => p.params && p.params[k] !== val,
              );

              // 结合 UI 勾选状态（双重保险：新任务靠 UI 勾选，历史任务靠数据动态对比）
              const isOptInUI = pConfig && pConfig.opt;

              if (isOptInUI || isDynamicOpt) {
                const displayVal = val % 1 === 0 ? val : Number(val).toFixed(3);
                paramHtml += `${k}: <span style="color:#3b82f6">${displayVal}</span><br/>`;
              }
            }
          }

          if (!paramHtml)
            paramHtml =
              "<span style='color: gray; font-size: 11px;'>暂无参与优化的参数</span>";

          return `<div style="font-family: monospace;">
                        <b>Gen ${d.gen} - No.${d.ind}</b><br/>
                        Score: <span style="color:#ef4444">${d.value[2].toFixed(2)}</span><br/>
                        Power: <span style="color:#f59e0b">${d.value[0].toFixed(2)} MW</span><br/>
                        Eff: <span style="color:#10b981">${d.value[1].toFixed(2)} %</span><br/>
                        <hr style="margin:4px 0; border:0; border-top:1px dashed rgba(255,255,255,0.2)" />
                        <span style="font-size:12px; color:var(--n-text-color-3);">[Opt Parameters]</span><br/>
                        ${paramHtml}
                      </div>`;
        },
      },
      grid: { top: 30, right: 80, bottom: 40, left: 50 },
      xAxis: {
        type: "value",
        name: "Power (MW)",
        splitLine: axisLineStyle,
        axisLabel: axisLabelStyle,
        scale: true,
      },
      yAxis: {
        type: "value",
        name: "Efficiency (%)",
        splitLine: axisLineStyle,
        axisLabel: axisLabelStyle,
        scale: true,
      },
      visualMap: {
        dimension: 2, // 映射到 data 数组的第三个元素 (索引 2，即 Score)
        orient: "vertical",
        right: 15,
        top: 60,
        text: ["高分", "低分"],
        textStyle: { color: textColor },
        calculable: true,
        // ✨ 新增这两行，开启数据极值自动计算 ✨
        min: "dataMin",
        max: "dataMax",
        inRange: {
          // 颜色从低分到高分排列 (冷色代表低分/负分，暖色代表高分)
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
      series: [
        {
          name: "Individuals",
          type: "scatter",
          symbolSize: 10,
          itemStyle: {
            opacity: 0.8,
            borderColor: "var(--n-card-color)",
            borderWidth: 1,
          },
          data: [],
        },
      ],
    });

    scatterChart.on("click", function (params) {
      autoTrackLatest.value = false;
      inspectGen.value = params.data.gen;
      inspectInd.value = params.data.ind;
      updateInspectorChart();
    });
  }

  // 3. 代数最优收敛趋势图
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value);
    trendChart.setOption({
      backgroundColor: "transparent",
      tooltip: { trigger: "axis", ...getTooltipStyle() },
      legend: { show: false, selected: { Eff: true, Power: true, Freq: true } }, // 隐藏自带图例，用 Naive UI 控制
      grid: { top: 40, right: 100, bottom: 40, left: 60 }, // 默认给右侧两个 Y 轴留足 100px 空间
      xAxis: {
        type: "category",
        data: [],
        splitLine: axisLineStyle,
        axisLabel: axisLabelStyle,
        name: "Gen",
      },
      yAxis: [
        {
          type: "value",
          name: "Eff (%)",
          position: "left",
          splitLine: axisLineStyle,
          axisLabel: axisLabelStyle,
          nameTextStyle: { color: "#10b981" },
          axisLine: { show: true, lineStyle: { color: "#10b981" } },
        },
        {
          type: "value",
          name: "Power (MW)",
          position: "right",
          offset: 0,
          splitLine: { show: false },
          axisLabel: axisLabelStyle,
          nameTextStyle: { color: "#f59e0b" },
          axisLine: { show: true, lineStyle: { color: "#f59e0b" } },
        },
        {
          type: "value",
          name: "Freq (GHz)",
          position: "right",
          offset: 80,
          splitLine: { show: false },
          axisLabel: axisLabelStyle,
          nameTextStyle: { color: "#3b82f6" },
          axisLine: { show: true, lineStyle: { color: "#3b82f6" } },
        },
      ],
      series: [
        {
          name: "Eff",
          type: "line",
          data: [],
          smooth: true,
          itemStyle: { color: "#10b981" },
        },
        {
          name: "Power",
          type: "line",
          yAxisIndex: 1,
          data: [],
          smooth: true,
          itemStyle: { color: "#f59e0b" },
        },
        {
          name: "Freq",
          type: "line",
          yAxisIndex: 2,
          data: [],
          smooth: true,
          itemStyle: { color: "#3b82f6" },
        },
      ],
    });
  }
};

// ✨ 趋势图指标动态切换逻辑：智能避免 Y 轴文字重叠
const updateTrendVisibility = (val) => {
  if (!trendChart) return;
  const powerShown = val.includes("power");
  const freqShown = val.includes("freq");

  trendChart.setOption({
    legend: {
      selected: {
        Eff: val.includes("eff"),
        Power: powerShown,
        Freq: freqShown,
      },
    },
    yAxis: [
      { show: val.includes("eff") },
      { show: powerShown, offset: 0 },
      // ✨ 修复：动态切换时，如果两根轴都在，偏移 80px
      { show: freqShown, offset: powerShown ? 80 : 0 },
    ],
    // ✨ 修复：两根轴同时存在时，画布右边距自动撑开到 100px；单轴 60px；无轴 30px
    grid: {
      right: powerShown && freqShown ? 100 : powerShown || freqShown ? 60 : 30,
    },
  });
};

const updateInspectorChart = () => {
  if (!inspectorChart) return;
  const g = inspectGen.value;
  const i = inspectInd.value;

  // ✨ 直接使用响应式的主题颜色函数
  const textColor = getThemeColor();
  const gridLineColor = getGridColor();

  // ✨ 顺手加上 type: "dashed"，让波形图的网格线风格和其他图表保持一致
  const axisLineStyle = { lineStyle: { color: gridLineColor, type: "dashed" } };
  const axisLabelStyle = { color: textColor, fontFamily: "monospace" };

  // 默认的基础坐标系框架
  let option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      ...getTooltipStyle(),
    },
    grid: { top: 40, right: 40, bottom: 40, left: 60 },
    xAxis: {
      type: "value",
      splitLine: axisLineStyle,
      axisLabel: axisLabelStyle,
      scale: true,
    },
    yAxis: {
      type: "value",
      splitLine: axisLineStyle,
      axisLabel: axisLabelStyle,
      scale: true,
    },
    series: [],
  };

  if (allDataPool[g] && allDataPool[g][i]) {
    const data = allDataPool[g][i];

    if (activeWaveTab.value === "power" && data.power) {
      // ✨修改：引入原版 Lab_2.py 的自动量级换算 (Auto-Scale) 逻辑
      let yRaw = data.power.y;
      let maxVal = Math.max(...yRaw.map(Math.abs));
      let scale = 1;
      let unit = "W";

      if (maxVal >= 1e9) {
        scale = 1e9;
        unit = "GW";
      } else if (maxVal >= 1e6) {
        scale = 1e6;
        unit = "MW";
      } else if (maxVal >= 1e3) {
        scale = 1e3;
        unit = "kW";
      }

      let yData = yRaw.map((v) => v / scale);
      let plotData = data.power.x.map((xVal, idx) => [xVal, yData[idx]]);

      option.xAxis.name = "Time (ns)";
      option.yAxis.name = `Power (${unit})`;
      option.yAxis.nameTextStyle = { color: "#f59e0b" };
      option.series = [
        {
          name: "功率",
          type: "line",
          smooth: true,
          showSymbol: false,
          itemStyle: { color: "#f59e0b" },
          data: plotData,
        },
      ];
    } else if (activeWaveTab.value === "eff" && data.eff) {
      // CST 传回是小数，转为百分比
      let yData = data.eff.y.map((v) => v * 100);
      let plotData = data.eff.x.map((xVal, idx) => [xVal, yData[idx]]);
      option.xAxis.name = "Time (ns)";
      option.yAxis.name = "Efficiency (%)";
      option.yAxis.nameTextStyle = { color: "#10b981" };
      option.series = [
        {
          name: "效率",
          type: "line",
          smooth: true,
          showSymbol: false,
          itemStyle: { color: "#10b981" },
          data: plotData,
        },
      ];
    } else if (activeWaveTab.value === "mainMode" && data.mainMode) {
      // 主模波形通常是正负振荡的幅度
      let plotData = data.mainMode.x.map((xVal, idx) => [
        xVal,
        data.mainMode.y[idx],
      ]);
      option.xAxis.name = "Time (ns)";
      option.yAxis.name = "Amplitude";
      option.yAxis.nameTextStyle = { color: "#8b5cf6" }; // 紫色主题
      option.series = [
        {
          name: "主模信号",
          type: "line",
          smooth: true,
          showSymbol: false,
          itemStyle: { color: "#8b5cf6" },
          data: plotData,
        },
      ];
    } else if (activeWaveTab.value === "fft" && data.fft) {
      // 频谱图
      let plotData = data.fft.x.map((xVal, idx) => [xVal, data.fft.y[idx]]);
      option.xAxis.name = "Freq (GHz)";
      option.yAxis.name = "Amplitude";
      option.yAxis.nameTextStyle = { color: "#ef4444" };
      // 频谱图通常画成带渐变色的面积图比较专业
      option.series = [
        {
          name: "频谱",
          type: "line",
          showSymbol: false,
          itemStyle: { color: "#ef4444" },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: "rgba(239,68,68,0.8)" },
              { offset: 1, color: "rgba(239,68,68,0.1)" },
            ]),
          },
          data: plotData,
        },
      ];
    }
  }

  // 注意：这里的第二个参数 true 非常关键！它指示 ECharts 完全清除旧坐标系，渲染全新的坐标轴和数据
  inspectorChart.setOption(option, true);
};

const refreshScatterFilter = () => {
  if (!scatterChart) return;
  const filteredData = scatterDataArrayRaw.filter(
    (item) => item.value[1] >= scatterFilterEff.value,
  );
  let minScore = 0;
  let maxScore = 200;
  if (filteredData.length > 0) {
    const scores = filteredData.map((d) => d.value[2]).filter((v) => !isNaN(v));
    if (scores.length > 0) {
      minScore = Math.min(...scores);
      maxScore = Math.max(...scores);
      // 如果当前只有一个点，强制拉开极值
      if (minScore === maxScore) {
        minScore -= 10;
        maxScore += 10;
      }
    }
  }
  scatterChart.setOption({
    visualMap: { min: minScore, max: maxScore },
    series: [{ data: filteredData }],
  });
};

const manualSelectWave = () => {
  autoTrackLatest.value = false;
  updateInspectorChart();
};
const handleAutoTrackChange = (val) => {
  if (val) updateInspectorChart();
};

const handleResize = () => {
  if (inspectorChart) inspectorChart.resize();
  if (scatterChart) scatterChart.resize();
  if (trendChart) trendChart.resize();
};
const scrollToBottom = async () => {
  await nextTick();
  if (logWindowRef.value)
    logWindowRef.value.scrollTop = logWindowRef.value.scrollHeight;
};
const fetchModelPreview = async () => {
  if (!config.cstPath) return;

  isFetchingImage.value = true;
  try {
    // 向后端发送 GET 请求，必须指定 responseType 为 blob 来接收二进制图片流
    const response = await axios.get(`${API_BASE}/get_model_image`, {
      params: { cst_path: config.cstPath },
      responseType: "blob",
    });

    // 释放旧的 URL 内存（防止多次加载导致内存泄漏）
    if (modelImageUrl.value) {
      URL.revokeObjectURL(modelImageUrl.value);
    }

    // 将二进制 Blob 数据转换为浏览器可直接渲染的本地 URL
    modelImageUrl.value = URL.createObjectURL(response.data);
  } catch (error) {
    console.error("加载模型预览图失败:", error);
    // 如果返回 404，说明还没有 .dib 文件，清空之前的旧图
    modelImageUrl.value = "";
  } finally {
    isFetchingImage.value = false;
  }
};



onMounted(async () => {
  fetchHistoryTasks();
  sortVariables();
  initCharts();
  document.addEventListener("fullscreenchange", handleFullscreenChange);
  window.addEventListener("resize", handleResize);

  // ✨ 数据抢救逻辑：尝试找回后台运行的任务
  try {
    const resTask = await axios.get(`${API_BASE}/get_running_task`);
    if (resTask.data.status === "success") {
      const activeTaskId = resTask.data.task_id; // 先保存查到的活跃任务 ID

      // 🛑 核心改变：不再强行接管，而是弹窗询问用户
      if (activeTaskId.startsWith("sim_")) {
      dialog.warning({
        title: "发现运行中的后台任务",
        content: `系统检测到后台正在运行任务 [${activeTaskId}]。您是要接管该任务的监控台，还是强制终止它并开启新任务？`,
        positiveText: "接管监控台",
        negativeText: "强制终止它",
        // 用户点击接管：执行原有的恢复图表逻辑
        onPositiveClick: async () => {
          currentTaskId.value = activeTaskId;
          isRunning.value = true;
          connectWebSocket(activeTaskId);

          message.loading("🔄 正在从数据库恢复历史波形与图表...");
          const resData = await axios.get(
            `${API_BASE}/get_task_data/${currentTaskId.value}`,
          );
          if (resData.data.status === "success") {
            const d = resData.data;

            // ✨ 修复：优先全量恢复配置面板，如果没有老配置，再退化回只改总代数
            if (d.config_json) {
              Object.assign(config, d.config_json);
            } else {
              config.algo.nGen = d.total_gen || 50;
            }
            Object.assign(allDataPool, d.all_data_pool);
            scatterDataArrayRaw.splice(
              0,
              scatterDataArrayRaw.length,
              ...d.scatter_data,
            );
            refreshScatterFilter();
            trendAxisData.splice(0, trendAxisData.length, ...d.trend_data.axis);
            trendEffData.splice(0, trendEffData.length, ...d.trend_data.eff);
            trendPowData.splice(0, trendPowData.length, ...d.trend_data.power);
            // 兼容老数据：如果库里没有频率数据，用 0 占位防崩
            trendFreqData.splice(
              0,
              trendFreqData.length,
              ...(d.trend_data.freq || Array(d.trend_data.axis.length).fill(0)),
            );

            if (trendChart) {
              trendChart.setOption({
                xAxis: { data: trendAxisData },
                series: [
                  { data: trendEffData },
                  { data: trendPowData },
                  { data: trendFreqData },
                ],
              });
            }

            if (trendAxisData.length > 0) {
              currentGen.value = trendAxisData[trendAxisData.length - 1];
              bestEff.value = trendEffData[trendEffData.length - 1].toFixed(2);
              bestPower.value =
                trendPowData[trendPowData.length - 1].toFixed(2);
            }
            message.success("✅ 历史数据已从数据库无损恢复！");
            updateInspectorChart();
          } else {
            // 👈 新增这个 else，一旦后台查数据报错，立刻弹窗告诉你原因
            message.error(`数据恢复失败: ${resData.data.message}`);
          }
        },
        // 用户点击终止：直接发送 kill 请求清空后台
        onNegativeClick: async () => {
          message.loading("正在强制终止后台任务...");
          try {
            await axios.post(`${API_BASE}/stop_optimization/${activeTaskId}`);
            message.success("✅ 任务已清理，您可以配置并开启全新任务了。");
          } catch (e) {
            message.error("清理任务失败，请检查后端状态。");
          }
          isRunning.value = false;
          if (islandState) islandState.CstOpt.isRunning = false; // 释放页面状态
        },
      });
    }
    }
  } catch (err) {
    // 后台无任务，正常静默
  }
});
onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (inspectorChart) inspectorChart.dispose();
  if (scatterChart) scatterChart.dispose();
  if (trendChart) trendChart.dispose();
  document.removeEventListener("fullscreenchange", handleFullscreenChange);
});

// ========================================================
// 模拟仿真循环
// ========================================================
const trendAxisData = [];
const trendEffData = [];
const trendPowData = [];
const trendFreqData = []; // ✨ 新增频率数据流
const selectedTrendLines = ref(["eff", "power", "freq"]); // ✨ 新增图表开关状态

const fetchHistoryTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/recent_tasks?task_type=opt`);
    if (res.data.status === "success") {
      historyTaskOptions.value = res.data.tasks.map((t) => ({
        label: `${t.name} [${t.bestEff}]`,
        value: t.id, // 注意：这里绑定的是任务的唯一 ID
      }));
    }
  } catch (err) {
    console.error("获取历史任务失败", err);
  }
};

const loadHistoricalTask = async (taskId) => {
  message.loading(`正在还原任务 [${taskId}] 的完整视图...`);
  try {
    const resData = await axios.get(`${API_BASE}/get_task_data/${taskId}`);
    if (resData.data.status === "success") {
      const d = resData.data;

      // ✨ 修复：与上面保持完全一致的配置恢复逻辑
      if (d.config_json) {
        Object.assign(config, d.config_json);
      } else {
        config.algo.nGen = d.total_gen || 50;
      }

      // 2. 注入波形池与散点数据
      Object.assign(allDataPool, d.all_data_pool);
      scatterDataArrayRaw.splice(
        0,
        scatterDataArrayRaw.length,
        ...d.scatter_data,
      );
      refreshScatterFilter();

      // 3. 恢复收敛趋势图
      trendAxisData.splice(0, trendAxisData.length, ...d.trend_data.axis);
      trendEffData.splice(0, trendEffData.length, ...d.trend_data.eff);
      trendPowData.splice(0, trendPowData.length, ...d.trend_data.power);
      trendFreqData.splice(0, trendFreqData.length, ...d.trend_data.freq);

      if (trendChart) {
        trendChart.setOption({
          xAxis: { data: trendAxisData },
          series: [
            { data: trendEffData },
            { data: trendPowData },
            { data: trendFreqData },
          ],
        });
      }

      // 4. 更新顶部发光指标卡片为该任务的最终记录
      if (trendAxisData.length > 0) {
        currentGen.value = trendAxisData[trendAxisData.length - 1];
        bestEff.value = trendEffData[trendEffData.length - 1].toFixed(2);
        bestPower.value = trendPowData[trendPowData.length - 1].toFixed(2);
        bestFreq.value = trendFreqData[trendFreqData.length - 1].toFixed(3);
      }

      // 5. 默认显示该任务的最后一个波形
      inspectGen.value = currentGen.value;
      inspectInd.value = 1;
      updateInspectorChart();

      message.success("✅ 历史仿真界面已完整复原");
    }
  } catch (err) {
    message.error("恢复数据时发生错误");
  }
};

// ✨ 新增：全屏与重绘管理函数
const toggleFullscreen = (e) => {
  const card = e.currentTarget.closest(".chart-card");
  if (!card) return;
  if (!document.fullscreenElement) {
    // 强行赋予当前主题 Class，打破全屏顶层的样式隔离
    card.classList.remove("light-mode", "dark-mode");
    card.classList.add(isDarkMode.value ? "dark-mode" : "light-mode");
    card
      .requestFullscreen()
      .catch((err) => message.error(`无法进入全屏: ${err.message}`));
  } else {
    document.exitFullscreen();
  }
};
const handleFullscreenChange = () => {
  // 检测当前是否处于全屏状态
  const isFullscreen = !!document.fullscreenElement;
  
  // 设定全屏和非全屏的字号大小
  const axisFontSize = isFullscreen ? 16 : 12; // 坐标轴字号
  const tooltipFontSize = isFullscreen ? 18 : 13; // 悬浮框字号
  
  // 提取主题颜色，防止覆盖掉原有的深色/浅色模式适配
  const tc = getThemeColor();
  const gc = getGridColor();
  const dashStyle = { lineStyle: { color: gc, type: "dashed" } };
  
  // 动态构建需要覆盖的 Option
  const fontUpdateOption = {
    tooltip: {
      textStyle: { fontSize: tooltipFontSize }
    },
    xAxis: { 
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle
    },
    yAxis: { 
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle
    }
  };

  // 1. 更新波形审查台
  if (inspectorChart) {
    inspectorChart.setOption(fontUpdateOption);
  }
  
  // 2. 更新散点图 (如果需要，还可以放大 symbolSize)
  if (scatterChart) {
    scatterChart.setOption({
      ...fontUpdateOption,
      series: [{ symbolSize: isFullscreen ? 16 : 10 }] // 全屏时把散点也变大
    });
  }
  
  // 3. 更新趋势图 (注意趋势图有多个 Y 轴)
  if (trendChart) {
    trendChart.setOption({
      tooltip: { textStyle: { fontSize: tooltipFontSize } },
      xAxis: { axisLabel: { fontSize: axisFontSize, color: tc }, splitLine: dashStyle },
      yAxis: [
        { axisLabel: { fontSize: axisFontSize, color: tc }, splitLine: dashStyle },
        { axisLabel: { fontSize: axisFontSize, color: tc } },
        { axisLabel: { fontSize: axisFontSize, color: tc } }
      ]
    });
  }

  // 保留原有的重绘逻辑，确保尺寸铺满
  handleResize();
  setTimeout(handleResize, 100);
  setTimeout(handleResize, 300);
  setTimeout(handleResize, 600);
};

// ========================================================
// 新增：WebSocket 专属房间通信逻辑
// ========================================================
let ws = null; // 全局保存 WebSocket 实例

const connectWebSocket = (taskId) => {
  // 1. 如果之前有连接，先切断（防止重复点击产生多个监听）
  if (ws) {
    ws.close();
  }

  // 2. 拿着后端刚刚分配的 taskId，连入专属数据通道
  ws = new WebSocket(`${WS_BASE}/progress/${taskId}`);
  // 3. 监听后端发来的消息
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "individual_progress") {
      // 1. 打印终端进度日志
      logs.value.push(
        `<span style='color:#3b82f6;'>[SYSTEM]</span> 正在计算 Gen ${data.gen} ... [${data.ind}/${data.total_ind}] 完成 | Eff: ${data.eff}%`,
      );
      scrollToBottom();

      // 2. 动态存入波形内存池
      if (!allDataPool[data.gen]) {
        allDataPool[data.gen] = {};
      }
      allDataPool[data.gen][data.ind] = data.wave_data;

      // 3. 自动追踪波形
      if (autoTrackLatest.value) {
        inspectGen.value = data.gen;
        inspectInd.value = data.ind;
        updateInspectorChart();
      }

      // ✨ [新增核心] 4. 让散点图逐个蹦出！
      scatterDataArrayRaw.push({
        gen: data.gen,
        ind: data.ind,
        value: [data.power, data.eff, data.score],
        params: data.wave_data.params, // 占位，单步推送暂无详细参数
      });
      refreshScatterFilter(); // 触发 ECharts 重绘散点
    } else if (data.type === "progress") {
      // 整代算完后触发
      // ⚡ 1. 更新顶部发光数字卡片 (只有一代算完，才能决出本代的 Best)
      currentGen.value = data.gen;
      bestEff.value = data.best_eff.toFixed(2);
      if (islandState && islandState.CstOpt.isRunning) {
        islandState.CstOpt.progress = Math.round(
          (currentGen.value / config.algo.nGen) * 100,
        );
      }
      bestPower.value = data.best_power.toFixed(2);
      bestFreq.value = data.best_freq.toFixed(3);

      logs.value.push(
        `<span style='color:#10b981;'>[SYSTEM]</span> ${data.message}`,
      );
      scrollToBottom();

      // ⚡ 2. 覆盖完整波形数据
      allDataPool[data.gen] = data.waves_dict;

      // ✨ [新增核心] 3. 绘制本代的趋势图折线
      // ✨ [新增核心] 3. 绘制本代的趋势图折线
      trendAxisData.push(data.gen);
      trendEffData.push(data.best_eff);
      trendPowData.push(data.best_power);
      trendFreqData.push(data.best_freq); // 👈 加入频率推送

      if (trendChart) {
        trendChart.setOption({
          xAxis: { data: trendAxisData },
          series: [
            { data: trendEffData },
            { data: trendPowData },
            { data: trendFreqData },
          ],
        });
      }

      // ⚡ 4. 补全这一代所有散点的详细参数 (覆盖刚才单步的简略版，以支持鼠标悬停查看变量)
      // 先把本代之前单步推进去的简略点删掉
      scatterDataArrayRaw.splice(
        scatterDataArrayRaw.length - data.batch_logs.length,
        data.batch_logs.length,
      );
      // 再把带有详尽参数的完整点推入
      data.batch_logs.forEach((ind) => {
        scatterDataArrayRaw.push({
          gen: data.gen,
          ind: ind.No,
          value: [ind.Power, ind.Eff, ind.Score],
          params: ind.params,
        });
      });
      refreshScatterFilter();
    } else if (data.type === "finish") {
      // 🏁 收到完成信号，关闭引擎运转状态
      isRunning.value = false;
      if (islandState) islandState.CstOpt.isRunning = false; // ✨ 修复这里
      logs.value.push(
        `<span style='color:#3b82f6;'>[SYSTEM]</span> ${data.message}`,
      );
      scrollToBottom();
    } else if (data.type === "error") {
      // ❌ 收到报错信号，强制关闭运转状态
      isRunning.value = false;
      if (islandState) islandState.CstOpt.isRunning = false; // ✨ 修复这里
      logs.value.push(
        `<span style='color:#ef4444;'>[ERROR]</span> 引擎中断: ${data.message}`,
      );
      scrollToBottom();
    }
  };

  ws.onopen = () => {
    logs.value.push(
      `<span style='color:#3b82f6;'>[SYSTEM]</span> 数据遥测通道已建立 (Room: ${taskId})`,
    );
    scrollToBottom();
  };

  ws.onclose = () => {
    console.log(`通道 ${taskId} 已关闭`);
  };
};

const startOptimization = async () => {
  // 1. 基础校验 (防呆设计)
  if (!config.cstPath) {
    message.error("请先选择或填写 CST 项目路径！");
    return;
  }
  const optVars = config.paramsList.filter((p) => p.opt);
  if (optVars.length === 0) {
    message.warning("请至少勾选一个优化变量 (Opt)！");
    return;
  }

  // 2. 界面状态锁定，开始请求
  isRunning.value = true;
  if (islandState) {
    islandState.CstOpt.isRunning = true;
    islandState.CstOpt.taskName = config.taskName || "新优化任务";
    islandState.CstOpt.filePath = config.cstPath;
    islandState.CstOpt.progress = 0;
    islandState.CstOpt.abortFn = stopOptimization;
  }
  logs.value.push(
    "<span style='color:#10b981;'>[INFO]</span> 正在将配置发送至后台引擎...",
  );
  scrollToBottom();

  try {
    // 3. 发送 POST 请求，把配置表交给后端
    const response = await axios.post(`${API_BASE}/start_optimization`, config);

    // 4. 后端接收成功，下发 Task ID
    if (response.data.status === "success") {
      message.success("引擎指令下发成功！");
      const newTaskId = response.data.task_id;
      currentTaskId.value = newTaskId;
      logs.value.push(
        `<span style='color:#3b82f6;'>[SYSTEM]</span> 任务 ID: ${newTaskId}`,
      );
      logs.value.push(
        `<span style='color:#10b981;'>[SYSTEM]</span> ${response.data.message}`,
      );
      scrollToBottom();

      // 5. ✨ 最关键的一步：拿着刚发下来的 Task ID，接上专属数据线 ✨
      connectWebSocket(newTaskId);
    }
  } catch (error) {
    // 如果连 POST 请求都发不过去（比如后端没开）
    console.error("请求失败:", error);
    message.error("连接后台引擎失败，请检查后端是否运行！");
    logs.value.push(
      `<span style='color:#ef4444;'>[ERROR]</span> 连接失败: ${error.message}`,
    );
    isRunning.value = false;
    if (islandState) islandState.CstOpt.isRunning = false; // 报错了就把按钮恢复，允许重试
    scrollToBottom();
  }
};

watch(isDarkMode, () => {
  const tc = getThemeColor();
  const gc = getGridColor();
  const tooltip = getTooltipStyle();
  const dashStyle = { lineStyle: { color: gc, type: "dashed" } };

  if (inspectorChart) {
    inspectorChart.setOption({
      tooltip,
      xAxis: { axisLabel: { color: tc }, splitLine: dashStyle },
      yAxis: { axisLabel: { color: tc }, splitLine: dashStyle },
    });
  }
  if (scatterChart) {
    scatterChart.setOption({
      tooltip,
      xAxis: { axisLabel: { color: tc }, splitLine: dashStyle },
      yAxis: { axisLabel: { color: tc }, splitLine: dashStyle },
      visualMap: { textStyle: { color: tc } },
      toolbox: { iconStyle: { borderColor: tc } },
      dataZoom: [{ textStyle: { color: tc } }, { textStyle: { color: tc } }],
    });
  }
  if (trendChart) {
    trendChart.setOption({
      tooltip,
      xAxis: { axisLabel: { color: tc }, splitLine: dashStyle },
      yAxis: [
        { axisLabel: { color: tc }, splitLine: dashStyle },
        { axisLabel: { color: tc } },
        { axisLabel: { color: tc } },
      ],
    });
  }
});
</script>

<style scoped>
.cst-container {
  display: flex;
  height: 100vh;
  background-color: var(--n-body-color);
  color: var(--n-text-color);
}

/* 左侧样式 */
.sidebar {
  flex: 4;
  max-width: 40%;
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
.modern-card {
  margin-bottom: 20px;
  border-radius: 8px;
  background-color: var(--n-card-color);
  /* 👇 质感升级：半透明精细边框 + 悬浮外阴影 + 顶部高光厚度 */
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
.var-fix-row {
  display: flex;
  align-items: center;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--n-border-color);
}
.fix-label {
  font-size: 13px;
  color: var(--n-text-color-2);
  white-space: nowrap;
}
.inner-panel {
  padding: 16px;
  background-color: var(--n-color);
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
  font-size: 16px;
  font-weight: bold;
  letter-spacing: 2px;
  border-radius: 8px;
  height: 50px;
}

:deep(.n-form-item) {
  margin-bottom: 16px;
}
:deep(.n-form-item .n-form-item-label) {
  font-weight: 500;
  font-size: 13px;
  margin-bottom: 6px;
}

/* 右侧大屏基础布局 */
.main-content {
  flex: 6;
  padding: 24px;
  display: flex;
  flex-direction: column;
  background-color: var(--n-body-color);
  overflow: hidden;
}

/* 卡片通用 */
.metric-card,
.chart-card {
  background-color: var(--n-card-color);
  border-radius: 8px;
  /* 👇 质感升级：统一光影风格 */
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
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
.echarts-container {
  width: 100%;
  height: 100%;
  min-height: 0;
}

.text-sub {
  color: var(--n-text-color-3);
}

/* 引入数据专属字体和等宽特性 (tabular-nums 防抖动) */
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

.n-config-provider:not([theme="light"]) .text-neon-white {
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
}
.n-config-provider:not([theme="light"]) .text-neon-green {
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}
.n-config-provider:not([theme="light"]) .text-neon-orange {
  text-shadow: 0 0 10px rgba(245, 158, 11, 0.4);
}
.n-config-provider:not([theme="light"]) .text-neon-blue {
  text-shadow: 0 0 10px rgba(59, 130, 246, 0.4);
}

/* 🌟 全新 1/2/1 黄金分割 Flex 排版 🌟 */
/* 中间排：模型 (25%) + 波形 (50%) + 日志 (25%) */
.middle-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex: 1; /* ✨ 改为 flex: 1，与下排完美平分 50% 高度 */
  min-height: 0; /* ✨ 允许内部图表自适应缩放 */
}
/* 底排：趋势 (50%) + 散点 (50%) */
.bottom-row {
  display: flex;
  gap: 16px;
  flex: 1; /* 撑满剩余全部空间 */
  min-height: 0;
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
  position: relative;
}
.scanner-line {
  position: absolute;
  top: 0;
  left: -50%;
  width: 200%;
  height: 2px;
  background: #3b82f6;
  box-shadow: 0 0 15px 2px #3b82f6;
  animation: scan 1.5s linear infinite;
}
@keyframes scan {
  0% {
    top: -20px;
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    top: 120%;
    opacity: 0;
  }
}
.placeholder-text {
  font-family: monospace;
  color: var(--n-text-color-3);
}

/* 波形审查台参数区 */
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
  padding-right: 4px;
}

/* 终端样式 */
.terminal-card {
  border-color: rgba(16, 185, 129, 0.3);
}
.log-window {
  flex: 1;
  background-color: var(--n-code-color); /* 自动切换：暗色深灰，浅色浅灰 */
  padding: 12px;
  overflow-y: auto;
  min-height: 0;
  font-family: "Consolas", monospace;
  font-size: 12px;
  color: var(--n-text-color); /* 自动切换文字颜色 */
  border-radius: 0 0 8px 8px;
}

/* 美化 Log 窗口的滚动条 */
.log-window::-webkit-scrollbar {
  width: 6px;
}
.log-window::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.4);
  border-radius: 3px;
}
.log-window::-webkit-scrollbar-track {
  background: transparent;
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

/* 新代码 */
/* 🚀 修复全屏背景：引入通透的亚克力毛玻璃质感 */
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
  /* ✨ 核心：为全屏卡片添加全局模糊滤镜，并强制应用 */
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

.chart-card:fullscreen .card-title {
  font-size: 20px !important;
}

.chart-card:fullscreen .text-sub {
  font-size: 16px !important;
}

.chart-card:fullscreen .param-tags-wrapper .n-tag {
  font-size: 16px !important;
  padding: 0 16px !important;
  height: auto !important;
  line-height: 1.5 !important;
}

/* 如果有单选按钮组件等，也可以酌情放大 */
.chart-card:fullscreen .n-radio-button {
  font-size: 16px !important;
}

.chart-card.light-mode:fullscreen {
  /* ✨ 将白色背景改为半透明，增加通透感 */
  background-color: rgba(255, 255, 255, 0.4) !important;
}

.chart-card.dark-mode:fullscreen {
  /* ✨ 将黑色背景改为半透明，增加通透感 */
  background-color: rgba(24, 24, 28, 0.4) !important;
}

.chart-card:fullscreen::backdrop {
  /* ✨ 确保浏览器底层的 backdrop 是透明的 */
  background-color: transparent !important;
}

/* 穿透修改内容层，打断 flex 尺寸死锁 */
.chart-card,
:deep(.n-card__content) {
  min-width: 0 !important;
  min-height: 0 !important;
}
</style>
