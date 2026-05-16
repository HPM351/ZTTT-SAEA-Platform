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
<!-- ================= 模块 1: 项目与任务配置 (历史记录/路径解析) ================= -->
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
<!-- ================= 模块 2: 变量空间管理 (参数提取/极值设定/固定调节) ================= -->
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
                  <n-gi :span="7">
                    <n-input
                      v-model:value="item.name"
                      placeholder="变量名"
                      clearable
                    />
                  </n-gi>
                  <n-gi :span="5">
                    <n-input-number
                      v-model:value="item.min"
                      :show-button="false"
                    >
                      <template #prefix
                        ><span class="inner-label">Min</span></template
                      >
                    </n-input-number>
                  </n-gi>
                  <n-gi :span="5">
                    <n-input-number
                      v-model:value="item.max"
                      :show-button="false"
                    >
                      <template #prefix
                        ><span class="inner-label">Max</span></template
                      >
                    </n-input-number>
                  </n-gi>
                  <n-gi
                    :span="5"
                    style="display: flex; justify-content: center"
                  >
                    <n-switch
                      v-model:value="item.opt"
                      size="medium"
                      @update:value="sortVariables"
                    >
                      <template #checked>Opt (优化)</template>
                      <template #unchecked>Fix (固定)</template>
                    </n-switch>
                  </n-gi>
                  <n-gi :span="2" style="text-align: right">
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
            </transition-group>
          </n-card>
<!-- ================= 模块 3: 全局环境配置与多目标函数设定 ================= -->
          <n-collapse :default-expanded-names="['env', 'targets', 'algo']">
            <n-collapse-item title="全局变量设置" name="env">
              <div class="inner-panel">
                <n-grid :x-gap="24" :cols="2">
                  <n-gi>
                    <n-form-item>
                      <template #label>
                        时域稳态起始时间 (ns)
                        <n-tooltip trigger="hover">
                          <template #trigger
                            ><span style="cursor: help; margin-left: 4px"
                              >❔</span
                            ></template
                          >
                          非时域仿真(如频域天线)请关闭此项
                        </n-tooltip>
                      </template>
                      <n-input-group>
                        <n-button
                          :type="
                            config.env.useStableTime ? 'primary' : 'default'
                          "
                          @click="
                            config.env.useStableTime = !config.env.useStableTime
                          "
                        >
                          {{
                            config.env.useStableTime ? "提取: 开" : "提取: 关"
                          }}
                        </n-button>
                        <n-input-number
                          v-model:value="config.env.stableTime"
                          :step="1.0"
                          :disabled="!config.env.useStableTime"
                          style="flex: 1"
                        />
                      </n-input-group>
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </div>
            </n-collapse-item>

            <n-collapse-item title="演化寻优目标" name="targets">
              <template #header-extra>
                <n-button
                  type="primary"
                  size="small"
                  dashed
                  @click.stop="addTarget"
                >
                  + 新增目标
                </n-button>
              </template>

              <transition-group
                name="list-anim"
                tag="div"
                class="params-list-container"
              >
                <div
                  v-for="(target, index) in config.targetsList"
                  :key="target.id"
                  class="var-item"
                  style="padding: 16px; border-color: var(--n-border-color)"
                >
                  <div
                    style="
                      display: flex;
                      justify-content: space-between;
                      align-items: center;
                      margin-bottom: 16px;
                    "
                  >
                    <n-input
                      v-model:value="target.name"
                      placeholder="目标名称 (如 VSWR, 效率)"
                      style="width: 240px"
                    >
                      <template #prefix>
                        <span
                          style="
                            font-weight: bold;
                            color: var(--n-text-color-3);
                          "
                        >
                          目标 {{ index + 1 }} :
                        </span>
                      </template>
                    </n-input>
                    <n-button
                      type="error"
                      quaternary
                      circle
                      @click="removeTarget(target.id)"
                    >
                      🗑️
                    </n-button>
                  </div>

                  <n-grid
                    :x-gap="16"
                    :y-gap="14"
                    :cols="2"
                    style="margin-bottom: 16px"
                  >
                    <n-gi :span="2">
                      <n-input-group>
                        <n-input-group-label>路径</n-input-group-label>
                        <n-input
                          v-model:value="target.path"
                          placeholder="CST 结果树路径 (例如: Tables\1D Results\EFF)"
                        />
                      </n-input-group>
                    </n-gi>

                    <n-gi>
                      <n-input-group>
                        <n-input-group-label>优化模式</n-input-group-label>
                        <n-select
                          v-model:value="target.mode"
                          :options="[
                            { label: '最大化 (Maximize)', value: 'maximize' },
                            { label: '最小化 (Minimize)', value: 'minimize' },
                            { label: '逼近定值 (Target)', value: 'target' },
                            {
                              label: '仅波形展示 (Display Only)',
                              value: 'display_only',
                            },
                          ]"
                        />
                      </n-input-group>
                    </n-gi>
                    <n-gi>
                      <n-input-group>
                        <n-input-group-label>提取规则</n-input-group-label>
                        <n-select
                          v-model:value="target.extractMethod"
                          :options="[
                            { label: '稳态后求均值', value: 'time_mean' },
                            { label: '寻找最大主峰', value: 'freq_peak' },
                            { label: '读取单值标量', value: '0d_scalar' },
                          ]"
                        />
                      </n-input-group>
                    </n-gi>

                    <n-gi>
                      <n-input-group>
                        <n-input-group-label>量纲预处理</n-input-group-label>
                        <n-select
                          v-model:value="target.multiplier"
                          filterable
                          tag
                          :options="[
                            { label: '保持原值 (× 1.0)', value: 1.0 },
                            { label: 'W → MW (× 1e-6)', value: 1e-6 },
                            { label: '小数 → % (× 100)', value: 100.0 },
                          ]"
                          placeholder="仅限纯数字 (如: 0.5 或 1e-3)"
                        />
                      </n-input-group>
                    </n-gi>
                  </n-grid>

                  <div
                    v-if="target.mode !== 'display_only'"
                    style="
                      background: rgba(16, 185, 129, 0.05);
                      padding: 14px;
                      border-radius: 8px;
                      border: 1px dashed rgba(16, 185, 129, 0.3);
                      margin-bottom: 16px;
                    "
                  >
                    <div
                      style="
                        font-size: 13px;
                        font-weight: bold;
                        color: #10b981;
                        margin-bottom: 12px;
                      "
                    >
                      柔性归一化与加权
                    </div>
                    <n-grid :x-gap="20" :cols="2">
                      <n-gi>
                        <n-input-number
                          v-model:value="target.reference_scale"
                          :step="1"
                        >
                          <template #prefix
                            ><span class="text-sub" style="font-size: 13px"
                              >基准尺 (Scale)</span
                            ></template
                          >
                        </n-input-number>
                      </n-gi>
                      <n-gi>
                        <n-input-number
                          v-model:value="target.weight"
                          :step="0.5"
                        >
                          <template #prefix
                            ><span class="text-sub" style="font-size: 13px"
                              >权重 (Weight)</span
                            ></template
                          >
                        </n-input-number>
                      </n-gi>
                    </n-grid>

                    <n-grid
                      v-if="target.mode === 'target'"
                      :x-gap="20"
                      :cols="2"
                      style="margin-top: 12px"
                    >
                      <n-gi>
                        <n-input-number v-model:value="target.target_val">
                          <template #prefix
                            ><span class="text-sub" style="font-size: 13px"
                              >靶心值 (Target)</span
                            ></template
                          >
                        </n-input-number>
                      </n-gi>
                      <n-gi>
                        <n-input-number
                          v-model:value="target.tolerance"
                          :step="0.01"
                        >
                          <template #prefix
                            ><span class="text-sub" style="font-size: 13px"
                              >完美容差 ±</span
                            ></template
                          >
                        </n-input-number>
                      </n-gi>
                    </n-grid>
                  </div>

                  <div
                    v-if="target.mode !== 'display_only'"
                    style="
                      background: rgba(245, 158, 11, 0.05);
                      padding: 14px;
                      border-radius: 8px;
                      border: 1px dashed rgba(245, 158, 11, 0.3);
                    "
                  >
                    <div
                      style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 12px;
                      "
                    >
                      <span
                        style="
                          font-size: 13px;
                          font-weight: bold;
                          color: #f59e0b;
                        "
                        >刚性拦截</span
                      >
                      <n-switch v-model:value="target.constraints.enable" />
                    </div>

                    <div v-if="target.constraints.enable">
                      <n-grid :x-gap="16" :cols="2" :y-gap="12">
                        <template v-if="target.mode !== 'target'">
                          <n-gi>
                            <n-input-number
                              v-model:value="target.constraints.min"
                              placeholder="无"
                            >
                              <template #prefix
                                ><span class="text-sub" style="font-size: 13px"
                                  >下限 (Min)</span
                                ></template
                              >
                            </n-input-number>
                          </n-gi>
                          <n-gi>
                            <n-input-number
                              v-model:value="target.constraints.max"
                              placeholder="无"
                            >
                              <template #prefix
                                ><span class="text-sub" style="font-size: 13px"
                                  >上限 (Max)</span
                                ></template
                              >
                            </n-input-number>
                          </n-gi>
                        </template>
                        <template v-else>
                          <n-gi>
                            <n-input-number
                              v-model:value="target.constraints.max_diff"
                              placeholder="无"
                            >
                              <template #prefix
                                ><span class="text-sub" style="font-size: 13px"
                                  >最大偏离容差 (Max Diff ±)</span
                                ></template
                              >
                            </n-input-number>
                          </n-gi>
                        </template>

                        <n-gi v-if="target.extractMethod === 'time_mean'">
                          <div
                            style="
                              display: flex;
                              align-items: center;
                              justify-content: space-between;
                              margin-bottom: 4px;
                            "
                          >
                            <span class="text-sub" style="font-size: 13px"
                              >波动容差模式</span
                            >
                            <n-switch
                              v-model:value="target.constraints.fluc_type"
                              checked-value="relative"
                              unchecked-value="absolute"
                              size="small"
                            >
                              <template #checked>百分比(相对)</template>
                              <template #unchecked>物理量(绝对)</template>
                            </n-switch>
                          </div>
                          <n-input-number
                            v-model:value="target.constraints.max_fluc"
                            placeholder="无(默认不限)"
                          >
                            <template #prefix>
                              <span class="text-sub" style="font-size: 13px">
                                {{
                                  target.constraints.fluc_type === "absolute"
                                    ? "最大波动 (绝对值)"
                                    : "最大波动 (±%)"
                                }}
                              </span>
                            </template>
                          </n-input-number>
                        </n-gi>
                        <n-gi v-if="target.extractMethod === 'freq_peak'">
                          <n-input-number
                            v-model:value="target.constraints.max_side_ratio"
                            placeholder="无(默认10%)"
                          >
                            <template #prefix
                              ><span class="text-sub" style="font-size: 13px"
                                >最大杂模占比 (%)</span
                              ></template
                            >
                          </n-input-number>
                        </n-gi>
                      </n-grid>
                    </div>
                  </div>
                </div>
              </transition-group>
            </n-collapse-item>
<!-- ================= 模块 4: 算法引擎超参数与控制中枢 (GA/PSO/BO) ================= -->
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
                                <div
                                  style="
                                    display: flex;
                                    justify-content: space-between;
                                    font-size: 12px;
                                    margin-bottom: 8px;
                                  "
                                >
                                  <div
                                    style="color: #3b82f6; font-weight: bold"
                                  >
                                    均匀变异 (探索
                                    {{ config.algo.ga.autoMutRange[0] }}%)
                                  </div>
                                  <div
                                    style="color: #10b981; font-weight: bold"
                                  >
                                    高斯变异 (收敛)
                                  </div>
                                  <div
                                    style="color: #f59e0b; font-weight: bold"
                                  >
                                    布列德 (微调
                                    {{ 100 - config.algo.ga.autoMutRange[1] }}%)
                                  </div>
                                </div>

                                <n-slider
                                  v-model:value="config.algo.ga.autoMutRange"
                                  range
                                  :step="1"
                                  :min="0"
                                  :max="100"
                                />
                              </div>
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
<!-- ================= 模块 5: 核心引擎动作触发区 (启动/急停) ================= -->
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
<!-- ================= 模块 6: 顶部状态指示 (演化进度/全局最优解) ================= -->
      <n-grid
        :x-gap="16"
        :cols="1 + config.targetsList.length"
        style="margin-bottom: 16px"
      >
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

        <n-gi v-for="(target, index) in config.targetsList" :key="target.id">
          <n-card class="metric-card" size="small">
            <n-statistic :label="`最优个体 ${target.name}`">
              <span
                :class="
                  [
                    'text-neon-green',
                    'text-neon-orange',
                    'text-neon-blue',
                    'text-neon-white',
                  ][index % 4]
                "
              >
                {{
                  bestMetrics[target.name] !== undefined
                    ? Number(bestMetrics[target.name]).toFixed(2)
                    : "--"
                }}
              </span>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>
      <div class="middle-row">
<!-- ================= 模块 7: 结构预览面板 (.dib 图像提取) ================= -->
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
<!-- ================= 模块 9: 算法运行终端与状态回传 (WebSocket) ================= -->
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
                  <n-radio-button
                    v-for="target in config.targetsList"
                    :key="target.id"
                    :value="target.name"
                  >
                    {{ target.name }}
                  </n-radio-button>
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

        <n-card
          class="chart-card terminal-card"
          style="flex: 25; display: flex; flex-direction: column"
          content-style="padding: 0; display: flex; flex-direction: column; flex: 1; min-height: 0;"
        >
          <div class="card-header">
            <span class="card-title">Engine Log</span>
            <transition name="fade">
              <n-space
                v-if="isRunning && Object.keys(telemetryData).length > 0"
                size="small"
                align="center"
              >
                <span
                  class="text-sub"
                  style="font-size: 12px; font-family: monospace"
                  >[动态遥测]</span
                >
                <n-tag
                  v-for="(val, key) in telemetryData"
                  :key="key"
                  type="info"
                  size="small"
                  :bordered="false"
                  style="font-family: monospace; font-weight: bold"
                >
                  {{ key }}: {{ val }}
                </n-tag>
              </n-space>
            </transition>
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
<!-- ================= 模块 10: 演化收敛趋势图 (多 Y 轴折线) ================= -->
        <n-card
          class="chart-card trend-card"
          style="flex: 55"
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
                  <n-checkbox
                    v-for="t in config.targetsList"
                    :key="t.name"
                    :value="t.name"
                    :label="t.name"
                  />
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
<!-- ================= 模块 11: 帕累托高维散点云图 (过滤/降维) ================= -->
        <n-card
          class="chart-card scatter-card"
          style="flex: 45"
          content-style="padding: 0; display: flex; flex-direction: column;"
        >
          <div
            class="card-header"
            style="
              display: flex;
              justify-content: space-between;
              align-items: flex-start;
              padding: 16px 24px 16px 16px;
            "
          >
            <div style="display: flex; flex-direction: column; gap: 16px">
              <n-space align="center">
                <span class="card-title">多维结果分布 (散点映射)</span>
                <n-button
                  quaternary
                  circle
                  size="small"
                  @click="toggleFullscreen"
                  title="全屏查看"
                >
                  <n-icon><Maximize /></n-icon>
                </n-button>
              </n-space>

              <n-space align="center" :size="12">
                <span class="text-sub" style="font-size: 12px">过滤底线:</span>
                <n-slider
                  v-model:value="scatterFilterScore"
                  :min="scatterSliderMin"
                  :max="scatterSliderMax"
                  :step="1"
                  style="width: 120px"
                  @update:value="refreshScatterFilter"
                />
                <span
                  style="
                    font-size: 13px;
                    font-weight: bold;
                    width: 65px;
                    display: inline-block;
                    text-align: left;
                  "
                  class="text-neon-green"
                  >{{ scatterFilterScore }}</span
                >
              </n-space>
            </div>

            <div
              style="
                display: flex;
                flex-direction: column;
                gap: 8px;
                width: 185px;
              "
            >
              <n-input-group style="display: flex; width: 100%">
                <n-input-group-label
                  size="small"
                  style="width: 48px; justify-content: center"
                  >X轴</n-input-group-label
                >
                <n-select
                  v-model:value="scatterConfig.xAxis"
                  :options="axisOptions"
                  size="small"
                  style="flex: 1"
                  @update:value="refreshScatterFilter"
                />
              </n-input-group>

              <n-input-group style="display: flex; width: 100%">
                <n-input-group-label
                  size="small"
                  style="width: 48px; justify-content: center"
                  >Y轴</n-input-group-label
                >
                <n-select
                  v-model:value="scatterConfig.yAxis"
                  :options="axisOptions"
                  size="small"
                  style="flex: 1"
                  @update:value="refreshScatterFilter"
                />
              </n-input-group>

              <n-input-group style="display: flex; width: 100%">
                <n-input-group-label
                  size="small"
                  style="width: 48px; justify-content: center"
                  >颜色</n-input-group-label
                >
                <n-select
                  v-model:value="scatterConfig.color"
                  :options="axisOptions"
                  size="small"
                  style="flex: 1"
                  @update:value="refreshScatterFilter"
                />
              </n-input-group>
            </div>
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
  backgroundColor: isDarkMode.value
    ? "rgba(15, 23, 42, 0.45)"
    : "rgba(255, 255, 255, 0.60)",
  borderColor: isDarkMode.value
    ? "rgba(255, 255, 255, 0.2)"
    : "rgba(0, 0, 0, 0.1)",
  borderWidth: 1,
  padding: 12,
  textStyle: { color: isDarkMode.value ? "#e2e8f0" : "#333333", fontSize: 13 },
  extraCssText:
    "backdrop-filter: blur(14px) !important; -webkit-backdrop-filter: blur(14px) !important; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15) !important; border-radius: 10px !important;",
});

const API_BASE = "/api"; // HTTP 走 Vite 代理
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
  targetsList: [
    {
      id: generateId(),
      name: "效率",
      path: "Tables\\1D Results\\EFF",
      mode: "maximize",
      extractMethod: "time_mean", 
      multiplier: 100.0, 
      reference_scale: 100.0,
      weight: 5.0,
      target_val: 0.0,
      tolerance: 0.0,
      constraints: {
        enable: true,
        min: 15.0,
        max: null,
        max_diff: null,
        max_fluc: 5.0,
        max_side_ratio: null,
      },
    },
    {
      id: generateId(),
      name: "频率",
      path: "Tables\\1D Results\\FFT",
      mode: "target",
      extractMethod: "freq_peak",
      multiplier: 1.0,
      reference_scale: 2.45,
      weight: 10.0,
      target_val: 2.45,
      tolerance: 0.02,
      constraints: {
        enable: true,
        min: null,
        max: null,
        max_diff: 0.5,
        max_side_ratio: 10.0,
      },
    },
  ],
  env: {
    useStableTime: true,
    stableTime: 20.0,
  },
  algo: {
    type: "SAEA-GA", 
    nPop: 10, 
    nGen: 50,
    injectJson: "",

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
      useAutoAcq: true, 
      kappa: 2.5, // 探索系数 (LCB)
      xi: 0.01, // 期望提升阈值 (EI)
    },
  },
});
const activeWaveTab = ref(
  config.targetsList.length > 0 ? config.targetsList[0].name : "mainMode",
);
const addTarget = () => {
  config.targetsList.push({
    id: generateId(),
    name: "新目标",
    path: "",
    mode: "maximize",
    extractMethod: "time_mean",
    multiplier: 1.0,
    reference_scale: 1.0,
    weight: 1.0,
    target_val: 0.0,
    tolerance: 0.0,
    constraints: {
      enable: false,
      fluc_type: "relative",
      min: null,
      max: null,
      max_diff: null,
      max_fluc: null,
      max_side_ratio: null,
    },
  });
};

const removeTarget = (id) => {
  const idx = config.targetsList.findIndex((t) => t.id === id);
  if (idx !== -1) config.targetsList.splice(idx, 1);
};

const generateInjectTemplate = () => {
  const template = {};
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

      if (saved.taskName) config.taskName = saved.taskName;
      if (saved.paramsList) config.paramsList = saved.paramsList;

      if (saved.env) {
        config.env = {
          ...config.env,
          ...saved.env,
        };
      }

      if (saved.targetsList && Array.isArray(saved.targetsList)) {
        config.targetsList = saved.targetsList.map((t) => ({
          ...t,
          constraints: t.constraints || {
            enable: false,
            min: null,
            max: null,
            max_diff: null,
            max_fluc: null,
            max_side_ratio: null,
          },
        }));
      }

      if (saved.algo) {
        config.algo = { ...config.algo, ...saved.algo };
      }

      message.success(`📂 已自动加载专属配置`);
      sortVariables();
    }
  } catch (err) {
    console.error("加载配置请求失败", err);
  }
};

// ====== 修改：触发路径变化时，调用加载函数 ======
const syncPath = (val) => {
  if (val) {
    config.cstPath = val;
    tryLoadConfig(val); 
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
const removeVariable = (id) => {
  const idx = config.paramsList.findIndex((p) => p.id === id);
  if (idx !== -1) config.paramsList.splice(idx, 1);
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

const triggerFileInput = async () => {
  message.loading("正在唤起系统资源管理器，请在弹窗中选择...");
  try {
    // 发送 GET 请求，让后端的 Python 帮我们弹窗
    const res = await axios.get(`${API_BASE}/browse_cst`);

    if (res.data.status === "success") {
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
const bestMetrics = reactive({});
const logs = ref(["[SYSTEM] WAITING FOR SAEA TASKS."]);
const logWindowRef = ref(null);
const telemetryData = reactive({});
const modelImageUrl = ref("");
const isFetchingImage = ref(false);
const allDataPool = reactive({});
let scatterDataArrayRaw = reactive([]);
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
let inspectorResizeObserver = null;
let scatterResizeObserver = null;
let trendResizeObserver = null;
const initCharts = () => {
  const textColor = getThemeColor();
  const gridLineColor = getGridColor();
  const echartsGridConfig = { top: 40, right: 40, bottom: 40, left: 60 };
  const axisLineStyle = { lineStyle: { color: gridLineColor, type: "dashed" } };
  const axisLabelStyle = { color: textColor, fontFamily: "monospace" };

  // 1. 波形审查台
  if (inspectorChartRef.value) {
    if (inspectorChart) {
      echarts.dispose(inspectorChartRef.value);
    } 
    inspectorChart = echarts.init(inspectorChartRef.value);
    if (!inspectorResizeObserver) {
      inspectorResizeObserver = new ResizeObserver(() => {
        if (inspectorChart) inspectorChart.resize();
      });
      inspectorResizeObserver.observe(inspectorChartRef.value);
    }
  }
  // 2. 帕累托散点云图
  if (scatterChartRef.value) {
    if (scatterChart) {
      echarts.dispose(scatterChartRef.value);
    } 
    scatterChart = echarts.init(scatterChartRef.value);
    if (!scatterResizeObserver) {
      scatterResizeObserver = new ResizeObserver(() => {
        if (scatterChart) scatterChart.resize();
      });
      scatterResizeObserver.observe(scatterChartRef.value);
    }

    // 动态提取 X 和 Y 轴（如果只有一个目标，X轴退化为得分）
    const xName = config.targetsList[0]?.name || "指标1";
    const yName =
      config.targetsList.length > 1 ? config.targetsList[1].name : "综合得分";

    scatterChart.setOption(
      {
        backgroundColor: "transparent",
        toolbox: {
          feature: {
            dataZoom: {
              yAxisIndex: "none",
              title: { zoom: "区域缩放", back: "取消缩放" }, // ✨ 改个更明确的名字
            },
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
          formatter: function (params) {
            const d = params.data; // [xVal, yVal, score, gen, ind, metricsDict, paramDict]

            let metricsHtml = "";
            for (let k in d[5]) {
              metricsHtml += `${k}: <span style="color:#10b981; font-weight:bold">${Number(d[5][k]).toFixed(3)}</span><br/>`;
            }

            let paramHtml = "";
            if (d[6]) {
              for (let k in d[6]) {
                const val = d[6][k];
                const pConfig = config.paramsList.find((p) => p.name === k);
                const isOptInUI = pConfig && pConfig.opt;
                if (isOptInUI) {
                  const displayVal =
                    val % 1 === 0 ? val : Number(val).toFixed(3);
                  paramHtml += `${k}: <span style="color:#3b82f6">${displayVal}</span><br/>`;
                }
              }
            }

            return `<div style="font-family: monospace;">
                    <b>Gen ${d[3]} - No.${d[4]}</b><br/>
                    Score: <span style="color:#ef4444">${Number(d[7]).toFixed(2)}</span><br/>
                    <hr style="margin:4px 0; border:0; border-top:1px dashed rgba(255,255,255,0.2)" />
                    ${metricsHtml}
                    <hr style="margin:4px 0; border:0; border-top:1px dashed rgba(255,255,255,0.2)" />
                    <span style="font-size:12px; color:var(--n-text-color-3);">[Opt Params]</span><br/>
                    ${paramHtml || "<span style='color: gray; font-size: 11px;'>暂无参数</span>"}
                  </div>`;
          },
        },
        grid: { top: 30, right: 80, bottom: 55, left: 50 },
        xAxis: {
          type: "value",
          name: xName,
          splitLine: axisLineStyle,
          axisLabel: axisLabelStyle,
          scale: true,
        },
        yAxis: {
          type: "value",
          name: yName,
          splitLine: axisLineStyle,
          axisLabel: axisLabelStyle,
          scale: true,
        },
        visualMap: {
          dimension: 2, 
          orient: "vertical",
          right: 15,
          top: 60,
          text: ["Max", "Min"],
          textStyle: { color: textColor },
          calculable: true,
          min: "dataMin",
          max: "dataMax",
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
      },
      true,
    );

    scatterChart.on("click", function (params) {
      autoTrackLatest.value = false;
      inspectGen.value = params.data[3];
      inspectInd.value = params.data[4];
      updateInspectorChart();
    });
  }

  // ==========================================
  // 3. 代数最优收敛趋势图 (动态多Y轴)
  // ==========================================
  if (trendChartRef.value) {
    if (trendChart) {
      echarts.dispose(trendChartRef.value);
    } 
    trendChart = echarts.init(trendChartRef.value);
    if (!trendResizeObserver) {
      trendResizeObserver = new ResizeObserver(() => {
        if (trendChart) trendChart.resize();
      });
      trendResizeObserver.observe(trendChartRef.value);
    }

    // 动态生成 Y 轴和折线 Series
    const yAxisArr = [];
    const seriesArr = [];
    const colors = ["#10b981", "#f59e0b", "#3b82f6", "#8b5cf6", "#ef4444"];

    config.targetsList.forEach((t, idx) => {
      const c = colors[idx % colors.length];
      const isLeft = idx % 2 === 0;
      const offset = Math.floor(idx / 2) * 50;

      yAxisArr.push({
        type: "value",
        name: t.name,
        position: isLeft ? "left" : "right",
        offset: offset,
        splitLine: idx === 0 ? axisLineStyle : { show: false },
        axisLabel: axisLabelStyle,
        nameTextStyle: { color: c },
        axisLine: { show: true, lineStyle: { color: c } },
      });

      seriesArr.push({
        name: t.name,
        type: "line",
        yAxisIndex: idx,
        data: [],
        smooth: true,
        itemStyle: { color: c },
      });
    });

    // 动态计算 Grid 的左右边距防止坐标轴越界
    const maxLeftOffset = Math.floor((config.targetsList.length - 1) / 2) * 50;
    const maxRightOffset = Math.floor((config.targetsList.length - 2) / 2) * 50;

    trendChart.setOption(
      {
        backgroundColor: "transparent",
        tooltip: { trigger: "axis", ...getTooltipStyle() },
        legend: { show: false }, // 由 UI Checkbox 控制
        grid: {
          top: 40,
          right: 60 + Math.max(0, maxRightOffset),
          bottom: 40,
          left: 60 + Math.max(0, maxLeftOffset),
        },
        xAxis: {
          type: "category",
          data: [],
          splitLine: axisLineStyle,
          axisLabel: axisLabelStyle,
          name: "Gen",
        },
        yAxis: yAxisArr,
        series: seriesArr,
      },
      true,
    );
  }
  selectedTrendLines.value = config.targetsList.map((t) => t.name);
};
const refreshScatterFilter = () => {
  if (!scatterChart) return;

  // 1. 刚性底线过滤：无论怎么切换维度，Score 底线过滤绝不妥协
  const filteredData = scatterDataArrayRaw.filter(
    (d) => d.score >= scatterFilterScore.value,
  );

  // 2. 核心适配逻辑：从个体对象中根据 Key 提取数值 (兼容参数/指标/得分)
  const getVal = (d, key) => {
    if (key === "score") return d.score;
    if (d.metrics && d.metrics[key] !== undefined) return d.metrics[key];
    if (d.params && d.params[key] !== undefined) return d.params[key];
    return 0;
  };

  // 辅助函数：根据选项值获取中文 Label
  const getLabel = (val) =>
    axisOptions.value.find((o) => o.value === val)?.label || val;

  let colorMin = Infinity,
    colorMax = -Infinity;

  // 3. 映射为 ECharts 坐标数据并实时扫描颜色极值
  const plotData = filteredData.map((d) => {
    const cVal = Number(getVal(d, scatterConfig.color)) || 0;
    if (cVal < colorMin) colorMin = cVal;
    if (cVal > colorMax) colorMax = cVal;

    return [
      Number(getVal(d, scatterConfig.xAxis)) || 0,
      Number(getVal(d, scatterConfig.yAxis)) || 0,
      cVal, // d[2]: 颜色映射值 (交由 visualMap 处理)
      d.gen, // d[3]
      d.ind, // d[4]
      d.metrics, // d[5]
      d.params, // d[6]
      d.score, //  d[7]: 原始得分始终保留，专供 Tooltip 悬浮框使用
    ];
  });

  // 4. 颜色轴极值自适应及防 NaN 崩溃机制
  if (colorMin === Infinity || colorMin === colorMax) {
    colorMin = colorMin === Infinity ? 0 : Math.floor(colorMin) - 1;
    colorMax = Math.ceil(colorMax) + 1;
  }
  if (isNaN(colorMin) || !isFinite(colorMin)) colorMin = 0;
  if (isNaN(colorMax) || !isFinite(colorMax)) colorMax = 200;

  scatterChart.setOption({
    xAxis: { name: getLabel(scatterConfig.xAxis) },
    yAxis: { name: getLabel(scatterConfig.yAxis) },
    visualMap: { min: colorMin, max: colorMax },
    series: [{ data: plotData }],
  });
};
const updateTrendVisibility = (valArray) => {
  if (!trendChart) return;
  const selectedDict = {};
  const yAxisOpts = [];

  config.targetsList.forEach((t) => {
    const isVisible = valArray.includes(t.name);
    selectedDict[t.name] = isVisible;
    yAxisOpts.push({
      show: isVisible, // 动态控制这根 Y 轴的显示与隐藏
    });
  });

  trendChart.setOption({
    legend: { selected: selectedDict },
    yAxis: yAxisOpts,
  });
};


const updateInspectorChart = () => {
  if (!inspectorChart) return;
  const g = inspectGen.value;
  const i = inspectInd.value;

  const textColor = getThemeColor();
  const gridLineColor = getGridColor();
  const axisLineStyle = { lineStyle: { color: gridLineColor, type: "dashed" } };
  const axisLabelStyle = { color: textColor, fontFamily: "monospace" };

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
    const currentTab = activeWaveTab.value;

    // ==========================================
    // 处理固有波形 (主模)
    // ==========================================
    const targetCfg = config.targetsList.find((t) => t.name === currentTab);

    const isDisplayOnly = targetCfg && targetCfg.mode === "display_only";
    const curveKey = `${currentTab}_curve`;
    const curveData = data[curveKey];

    if (curveData && curveData.x && curveData.y) {
      const isFft = targetCfg && targetCfg.extractMethod === "freq_peak";
      const multiplier = targetCfg ? Number(targetCfg.multiplier) : 1.0;

      let plotData = curveData.x.map((xVal, idx) => [
        xVal,
        curveData.y[idx] * multiplier,
      ]);

      // 自动分配颜色：主模/仅展示用紫色，频域红色，其余绿色
      const themeColor = isDisplayOnly
        ? "#8b5cf6"
        : isFft
          ? "#ef4444"
          : "#10b981";

      option.xAxis.name = isFft ? "Freq (GHz)" : "Time (ns)";
      option.yAxis.name = currentTab;
      option.yAxis.nameTextStyle = { color: themeColor };

      option.series = [
        {
          name: currentTab,
          type: "line",
          smooth: !isFft,
          showSymbol: false,
          itemStyle: { color: themeColor },
          ...(isFft
            ? {
                areaStyle: {
                  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: "rgba(239,68,68,0.8)" },
                    { offset: 1, color: "rgba(239,68,68,0.1)" },
                  ]),
                },
              }
            : {}),
          data: plotData,
        },
      ];
    } else {
      // 容错处理，防止 Unknown series 报错
      option.series = [{ name: "等待数据...", type: "line", data: [] }];
    }
  }

  // 渲染
  inspectorChart.setOption(option, true);
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

  //数据抢救逻辑：尝试找回后台运行的任务
  try {
    const resTask = await axios.get(`${API_BASE}/get_running_task`);
    if (resTask.data.status === "success") {
      const activeTaskId = resTask.data.task_id; // 先保存查到的活跃任务 ID

      // 核心改变：不再强行接管，而是弹窗询问用户
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

            // 接管任务时，同步通知外层 App.vue 唤醒灵动岛
            if (islandState) {
              islandState.CstOpt.isRunning = true;
              islandState.CstOpt.taskName = activeTaskId; // 临时显示 ID，等下面拿到详细数据后可覆盖
              islandState.CstOpt.filePath = config.cstPath || "恢复中...";
              islandState.CstOpt.progress = 0;
              islandState.CstOpt.abortFn = stopOptimization;
            }

            message.loading("🔄 正在从数据库恢复历史波形与图表...");
            const resData = await axios.get(
              `${API_BASE}/get_task_data/${currentTaskId.value}`,
            );
            if (resData.data.status === "success") {
              const d = resData.data;

              // 优先全量恢复配置面板，如果没有老配置，再退化回只改总代数
              if (d.config_json) {
                const saved = d.config_json;
                if (saved.taskName) config.taskName = saved.taskName;
                if (saved.paramsList) config.paramsList = saved.paramsList;
                if (saved.env) {
                  config.env = {
                    ...config.env,
                    ...saved.env,
                    mainMode: {
                      ...config.env.mainMode,
                      ...(saved.env.mainMode || {}),
                    },
                  };
                }
                if (saved.algo) config.algo = { ...config.algo, ...saved.algo };
                if (saved.targetsList && Array.isArray(saved.targetsList)) {
                  config.targetsList = saved.targetsList.map((t) => ({
                    ...t,
                    constraints: t.constraints || {
                      enable: false,
                      min: null,
                      max: null,
                      max_diff: null,
                      max_fluc: null,
                      max_side_ratio: null,
                    },
                  }));
                }
              } else {
                config.algo.nGen = d.total_gen || 50;
              }

              initCharts();
              Object.assign(allDataPool, d.all_data_pool);
              scatterDataArrayRaw.splice(
                0,
                scatterDataArrayRaw.length,
                ...d.scatter_data,
              );
              updateScatterBounds();
              refreshScatterFilter();
              trendAxisData.splice(
                0,
                trendAxisData.length,
                ...d.trend_data.axis,
              );

              // 2. 动态恢复所有目标的趋势线数据
              config.targetsList.forEach((t) => {
                if (!trendSeriesData[t.name]) trendSeriesData[t.name] = [];
                trendSeriesData[t.name].splice(
                  0,
                  trendSeriesData[t.name].length,
                  ...(d.trend_data[t.name] ||
                    Array(d.trend_data.axis.length).fill(0)),
                );
              });

              // 3. 动态重绘趋势图
              if (trendChart) {
                const dynamicSeries = config.targetsList.map((t) => ({
                  name: t.name,
                  data: trendSeriesData[t.name],
                }));
                trendChart.setOption({
                  xAxis: { data: trendAxisData },
                  series: dynamicSeries,
                });
              }

              // 4. 动态恢复顶部发光指标卡片的最新值
              if (trendAxisData.length > 0) {
                currentGen.value = trendAxisData[trendAxisData.length - 1];
                config.targetsList.forEach((t) => {
                  if (
                    trendSeriesData[t.name] &&
                    trendSeriesData[t.name].length > 0
                  ) {
                    bestMetrics[t.name] =
                      trendSeriesData[t.name][
                        trendSeriesData[t.name].length - 1
                      ];
                  }
                });

                // 接管任务时，同步唤醒灵动岛的进度，避免因全局状态落后而卡在 0%
                if (islandState && islandState.CstOpt.isRunning) {
                  islandState.CstOpt.progress = Math.round(
                    (currentGen.value / (config.algo.nGen || 1)) * 100,
                  );
                }
              }
              message.success("✅ 历史数据已从数据库无损恢复！");
              updateInspectorChart();
            } else {
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
  document.removeEventListener("fullscreenchange", handleFullscreenChange);

  if (inspectorResizeObserver) inspectorResizeObserver.disconnect();
  if (scatterResizeObserver) scatterResizeObserver.disconnect();
  if (trendResizeObserver) trendResizeObserver.disconnect();

  if (inspectorChart) inspectorChart.dispose();
  if (scatterChart) scatterChart.dispose();
  if (trendChart) trendChart.dispose();
});

const trendAxisData = reactive([]);
const trendSeriesData = reactive({}); // 字典池，格式如: { "效率": [], "频率": [] }
const selectedTrendLines = ref([]);
const scatterFilterScore = ref(-500);
const scatterSliderMin = ref(-50000);
const scatterSliderMax = ref(500);

// 散点图的动态轴向配置 (默认全部看 Score，符合寻优直觉)
const scatterConfig = reactive({
  xAxis: "score",
  yAxis: "score",
  color: "score",
});

// 动态汇聚“参数、指标、得分”作为可选项
const axisOptions = computed(() => {
  const options = [{ label: "综合得分 (Score)", value: "score" }];
  // 仅提取勾选了 opt 的优化变量，过滤掉无关紧要的固定参数
  config.paramsList.forEach((p) => {
    if (p.opt) options.push({ label: `[参数] ${p.name}`, value: p.name });
  });
  // 提取所有的目标指标
  config.targetsList.forEach((t) => {
    options.push({ label: `[指标] ${t.name}`, value: t.name });
  });
  return options;
});

// 动态计算并更新滑块边界的函数
const updateScatterBounds = () => {
  if (scatterDataArrayRaw.length === 0) return;
  const scores = scatterDataArrayRaw
    .map((d) => Number(d.score))
    .filter((v) => !isNaN(v));
  if (scores.length > 0) {
    const minS = Math.min(...scores);
    const maxS = Math.max(...scores);
    // 稍微向外扩展一点范围，防止滑块卡死在边缘
    scatterSliderMin.value = Math.floor(minS) - 100;
    scatterSliderMax.value = Math.ceil(maxS) + 100;

    // 如果当前的过滤阈值已经超出了新数据的范围，自动把阈值拉到底线，确保至少能看到点
    if (
      scatterFilterScore.value < scatterSliderMin.value ||
      scatterFilterScore.value > scatterSliderMax.value
    ) {
      scatterFilterScore.value = scatterSliderMin.value;
    }
  }
};

const fetchHistoryTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/recent_tasks?task_type=opt`);
    if (res.data.status === "success") {
      historyTaskOptions.value = res.data.tasks.map((t) => ({
        label: t.best_score
          ? `${t.name} [得分: ${Number(t.best_score).toFixed(2)}]`
          : t.name,
        value: t.id,
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

      // 与上面保持完全一致的配置恢复逻辑
      if (d.config_json) {
        const saved = d.config_json;
        if (saved.taskName) config.taskName = saved.taskName;
        if (saved.paramsList) config.paramsList = saved.paramsList;
        if (saved.env) {
          config.env = {
            ...config.env,
            ...saved.env,
          };
        }
        if (saved.algo) config.algo = { ...config.algo, ...saved.algo };
        if (saved.targetsList && Array.isArray(saved.targetsList)) {
          config.targetsList = saved.targetsList.map((t) => ({
            ...t,
            constraints: t.constraints || {
              enable: false,
              min: null,
              max: null,
              max_diff: null,
            },
          }));
        }
      } else {
        config.algo.nGen = d.total_gen || 50;
      }

      initCharts();

      // 2. 注入波形池与散点数据
      Object.assign(allDataPool, d.all_data_pool);
      scatterDataArrayRaw.splice(
        0,
        scatterDataArrayRaw.length,
        ...d.scatter_data,
      );
      updateScatterBounds();
      refreshScatterFilter();

      // 3. 恢复收敛趋势图
      trendAxisData.splice(0, trendAxisData.length, ...d.trend_data.axis);
      config.targetsList.forEach((t) => {
        if (!trendSeriesData[t.name]) trendSeriesData[t.name] = [];
        trendSeriesData[t.name].splice(
          0,
          trendSeriesData[t.name].length,
          ...(d.trend_data[t.name] || Array(d.trend_data.axis.length).fill(0)),
        );
      });

      if (trendChart) {
        const dynamicSeries = config.targetsList.map((t) => ({
          name: t.name,
          data: trendSeriesData[t.name],
        }));
        trendChart.setOption({
          xAxis: { data: trendAxisData },
          series: dynamicSeries,
        });
      }

      // 4. 更新顶部发光指标卡片为该任务的最终记录
      if (trendAxisData.length > 0) {
        currentGen.value = trendAxisData[trendAxisData.length - 1];
        config.targetsList.forEach((t) => {
          if (trendSeriesData[t.name] && trendSeriesData[t.name].length > 0) {
            bestMetrics[t.name] =
              trendSeriesData[t.name][trendSeriesData[t.name].length - 1];
          }
        });
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

// 全屏与重绘管理函数
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
      textStyle: { fontSize: tooltipFontSize },
    },
    xAxis: {
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle,
    },
    yAxis: {
      axisLabel: { fontSize: axisFontSize, color: tc },
      splitLine: dashStyle,
    },
  };

  // 1. 更新波形审查台
  if (inspectorChart) {
    inspectorChart.setOption(fontUpdateOption);
  }

  // 2. 更新散点图 (如果需要，还可以放大 symbolSize)
  if (scatterChart) {
    scatterChart.setOption({
      ...fontUpdateOption,
      series: [{ symbolSize: isFullscreen ? 16 : 10 }], // 全屏时把散点也变大
    });
  }

  // 3. 更新趋势图 (注意趋势图有多个 Y 轴)
  if (trendChart) {
    trendChart.setOption({
      tooltip: { textStyle: { fontSize: tooltipFontSize } },
      xAxis: {
        axisLabel: { fontSize: axisFontSize, color: tc },
        splitLine: dashStyle,
      },
      yAxis: [
        {
          axisLabel: { fontSize: axisFontSize, color: tc },
          splitLine: dashStyle,
        },
        { axisLabel: { fontSize: axisFontSize, color: tc } },
        { axisLabel: { fontSize: axisFontSize, color: tc } },
      ],
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
      // 1. 打印终端日志 (动态读取第一个目标)
      const firstName = config.targetsList[0]?.name || "Value";
      const firstVal = data.metrics[firstName] || 0;
      logs.value.push(
        `<span style='color:#3b82f6;'>[SYSTEM]</span> 正在计算 Gen ${data.gen} ... [${data.ind}/${data.total_ind}] 完成 | ${firstName}: ${Number(firstVal).toFixed(2)}`,
      );
      scrollToBottom();

      // 2. 动态存入波形内存池
      if (!allDataPool[data.gen]) allDataPool[data.gen] = {};
      allDataPool[data.gen][data.ind] = data.wave_data;

      if (autoTrackLatest.value) {
        inspectGen.value = data.gen;
        inspectInd.value = data.ind;
        updateInspectorChart();
      }

      // 3. 散点图全量推入字典
      scatterDataArrayRaw.push({
        gen: data.gen,
        ind: data.ind,
        score: data.score,
        metrics: data.metrics, // 全量字典入库
        params: data.wave_data.params,
      });
      refreshScatterFilter();
    } else if (data.type === "progress") {
      //1. 更新顶部发光卡片
      currentGen.value = data.gen;
      Object.assign(bestMetrics, data.best_metrics); // 字典无缝覆盖

      if (islandState && islandState.CstOpt.isRunning) {
        islandState.CstOpt.progress = Math.round(
          (currentGen.value / config.algo.nGen) * 100,
        );
      }

      //1.5 接收并解析算法专属遥测数据 (如果后端发了的话)
      if (data.telemetry) {
        // 清空旧遥测数据，混入新数据
        for (const key in telemetryData) delete telemetryData[key];
        Object.assign(telemetryData, data.telemetry);
      }

      logs.value.push(
        `<span style='color:#10b981;'>[SYSTEM]</span> ${data.message}`,
      );
      scrollToBottom();

      //2. 覆盖波形数据
      allDataPool[data.gen] = data.waves_dict;

      //3. 动态绘制趋势图折线
      trendAxisData.push(data.gen);
      config.targetsList.forEach((t) => {
        if (!trendSeriesData[t.name]) trendSeriesData[t.name] = [];
        trendSeriesData[t.name].push(data.best_metrics[t.name] || 0);
      });

      if (trendChart) {
        const dynamicSeries = config.targetsList.map((t) => ({
          name: t.name,
          data: trendSeriesData[t.name],
        }));
        trendChart.setOption({
          xAxis: { data: trendAxisData },
          series: dynamicSeries,
        });
      }

      //4. 补全详尽参数的散点
      scatterDataArrayRaw = scatterDataArrayRaw.filter(
        (item) => item.gen !== data.gen,
      );
      data.batch_logs.forEach((ind) => {
        scatterDataArrayRaw.push({
          gen: data.gen,
          ind: ind.No,
          score: ind.Score,
          metrics: ind.metrics,
          params: ind.params,
        });
      });
      updateScatterBounds();
      refreshScatterFilter();
    } else if (data.type === "finish") {
      isRunning.value = false;
      if (islandState) islandState.CstOpt.isRunning = false;
      logs.value.push(
        `<span style='color:#3b82f6;'>[SYSTEM]</span> ${data.message}`,
      );
      scrollToBottom();
    } else if (data.type === "error") {
      isRunning.value = false;
      if (islandState) islandState.CstOpt.isRunning = false;
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

selectedTrendLines.value = config.targetsList.map((t) => t.name);

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

  currentGen.value = 0;
  Object.keys(bestMetrics).forEach((k) => delete bestMetrics[k]);
  trendAxisData.length = 0;
  Object.keys(trendSeriesData).forEach((k) => (trendSeriesData[k] = []));
  scatterDataArrayRaw.length = 0;
  for (const key in allDataPool) delete allDataPool[key]; // 清空波形池
  for (const key in telemetryData) delete telemetryData[key]; //清空旧遥测数据
  logs.value = []; // 清空日志

  // 强制重置 Echarts 画面
  initCharts();
  if (inspectorChart) inspectorChart.setOption({ series: [] });

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

      // 5. 拿着刚发下来的 Task ID，接上专属数据线 ✨
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
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
}
.card-title {
  font-weight: 600;
  font-size: 14px;
  color: var(--n-text-color);
  white-space: nowrap; 
  flex-shrink: 0; 
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

  overflow-y: auto;
}

.main-content::-webkit-scrollbar {
  width: 8px;
}
.main-content::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.3);
  border-radius: 4px;
}
.main-content::-webkit-scrollbar-track {
  background: transparent;
}

/* 卡片通用 */
.metric-card,
.chart-card {
  background-color: var(--n-card-color);
  border-radius: 8px;
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

/* 中间排：模型 (25%) + 波形 (50%) + 日志 (25%) */
.middle-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex: 1;
  /* 无论屏幕多扁，波形审查台和日志区最低也要保持 400px，保证波形可读 */
  min-height: 400px;
}
/* 底排：趋势 (50%) + 散点 (50%) */
.bottom-row {
  display: flex;
  gap: 16px;
  /* 稍微增加底排的纵向 flex 权重，压缩顶部模块，给散点图和折线图更多空间 */
  flex: 1.2;
  min-height: 420px;
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
  /* 为全屏卡片添加全局模糊滤镜，并强制应用 */
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
  /* 将白色背景改为半透明，增加通透感 */
  background-color: rgba(255, 255, 255, 0.4) !important;
}

.chart-card.dark-mode:fullscreen {
  /* 将黑色背景改为半透明，增加通透感 */
  background-color: rgba(24, 24, 28, 0.4) !important;
}

.chart-card:fullscreen::backdrop {
  /* 确保浏览器底层的 backdrop 是透明的 */
  background-color: transparent !important;
}

/* 穿透修改内容层，打断 flex 尺寸死锁 */
.chart-card {
  display: flex !important;
  flex-direction: column !important;
  min-width: 0 !important;
  min-height: 0 !important;
}
:deep(.n-card__content) {
  flex: 1 !important;
  display: flex !important;
  flex-direction: column !important;
  min-width: 0 !important;
  min-height: 0 !important;
}
.params-list-container {
  position: relative;
}

/* 确立移动过程中的过渡曲线（FLIP动画） */
.list-anim-move,
.list-anim-enter-active,
.list-anim-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}

/* 元素进入和离开时的状态 */
.list-anim-enter-from,
.list-anim-leave-to {
  opacity: 0;
  transform: translateY(15px) scale(0.98);
}

/* 确保离开的元素被拔出文档流，这样下面的元素才能顺滑滑上来补位 */
.list-anim-leave-active {
  position: absolute;
  width: 100%;
}
</style>
