<template>
  <div class="home-container">
    <div class="home-theme-toggle">
      <n-switch v-model:value="isDarkMode" size="large">
        <template #checked-icon>🌙</template>
        <template #unchecked-icon>☀️</template>
      </n-switch>
    </div>
    <n-space vertical :size="24">
      <div class="welcome-header">
        <h1 class="glow-text">ZTTT SAEA Platform</h1>
        <p class="sub-title">基于代理模型辅助进化算法的微波器件智能优化平台</p>
      </div>

      <n-grid :x-gap="24" :y-gap="24" :cols="2">
        <n-gi>
          <n-card
            class="nav-card sweep-card"
            hoverable
            @click="goToPage('CstSweep')"
          >
            <div class="nav-content">
              <div class="custom-icon-box">
                <img
                  src="/cst-logo.png"
                  alt="CST Logo"
                  class="custom-logo-img"
                />
              </div>
              <div class="nav-text">
                <h3>CST 联合扫参</h3>
                <p>多维参数笛卡尔积遍历，快速构建物理样本空间</p>
              </div>
            </div>
            <div class="nav-action">进入工作台 ➡️</div>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card
            class="nav-card cst-card"
            hoverable
            @click="goToPage('CstOpt')"
          >
            <div class="nav-content">
              <div class="custom-icon-box">
                <img
                  src="/cst-logo.png"
                  alt="CST Logo"
                  class="custom-logo-img"
                />
              </div>
              <div class="nav-text">
                <h3>CST 联合仿真优化</h3>
                <p>调用 CST Studio Suite 进行电磁仿真与 GA 演化</p>
              </div>
            </div>
            <div class="nav-action">进入工作台 ➡️</div>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card
            class="nav-card nn-card"
            hoverable
            @click="goToPage('NeuralNet')"
          >
            <div class="nav-content">
              <div class="custom-icon-box">
                <img
                  src="/pycharm-logo.png"
                  alt="PyCharm Logo"
                  class="custom-logo-img"
                />
              </div>
              <div class="nav-text">
                <h3>神经网络预测模式</h3>
                <p>基于深度学习模型秒级预测器件性能，支持在线微调</p>
              </div>
            </div>
            <div class="nav-action">进入工作台 ➡️</div>
          </n-card>
        </n-gi>

        <n-gi>
          <n-card
            class="nav-card db-card"
            hoverable
            @click="goToPage('DataCenter')"
          >
            <div class="nav-content">
              <div class="custom-icon-box">
                <img
                  src="/datagrip-logo.png"
                  alt="DataGrip Logo"
                  class="custom-logo-img"
                />
              </div>
              <div class="nav-text">
                <h3>数据资产管理</h3>
                <p>查阅历史仿真数据与波形，支持 Excel 导出与离线归档</p>
              </div>
            </div>
            <div class="nav-action">管理库 ➡️</div>
          </n-card>
        </n-gi>
      </n-grid>

      <n-grid :x-gap="24" :y-gap="24" :cols="3">
        <n-gi :span="1">
          <n-card size="small" class="module-card" segmented>
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px">
                <n-icon :size="20"><Monitor /></n-icon>
                <span>系统探针 (System Probe)</span>
              </div>
            </template>
            <template #header-extra>
              <n-button
                size="tiny"
                secondary
                type="primary"
                @click="refreshSystemStatus"
              >
                <template #icon>
                  <n-icon><RefreshCw /></n-icon>
                </template>
                重连
              </n-button>
            </template>
            <n-space vertical :size="16">
              <div class="status-row">
                <span>CST 仿真引擎</span>
                <n-badge
                  dot
                  :type="cstStatus === 'running' ? 'success' : 'error'"
                  processing
                />
              </div>
              <div class="status-row">
                <span>FastAPI 后台服务</span>
                <n-badge
                  dot
                  :type="apiStatus === 'running' ? 'success' : 'error'"
                  processing
                />
              </div>
              <div class="status-row">
                <span>Agents智能体对话服务</span>
                <n-badge
                  dot
                  :type="agentsStatus === 'running' ? 'success' : 'error'"
                  processing
                />
              </div>

              <n-divider style="margin: 4px 0" />

              <n-grid :cols="2" :x-gap="12">
                <n-gi style="text-align: center">
                  <n-progress
                    type="dashboard"
                    gap-position="bottom"
                    :percentage="cpuUsage"
                    :color="cpuColor"
                  />
                  <div class="probe-label">CPU 负载</div>
                </n-gi>
                <n-gi style="text-align: center">
                  <n-progress
                    type="dashboard"
                    gap-position="bottom"
                    :percentage="ramUsage"
                    :color="ramColor"
                  />
                  <div class="probe-label">内存占用</div>
                </n-gi>
              </n-grid>

              <n-divider style="margin: 4px 0" />

              <n-descriptions label-placement="left" size="small" :column="1">
                <n-descriptions-item label="Python"
                  >3.10.12 (Conda)</n-descriptions-item
                >
                <n-descriptions-item label="PyTorch"
                  >2.1.0+cu118</n-descriptions-item
                >
                <n-descriptions-item label="CST"
                  >2024 (AMD64)</n-descriptions-item
                >
              </n-descriptions>
            </n-space>
          </n-card>
        </n-gi>

        <n-gi :span="2">
          <n-card size="small" class="module-card" segmented>
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px">
                <n-icon :size="20"><ClipboardList /></n-icon>
                <span>最近任务 (Recent Tasks)</span>
              </div>
            </template>

            <template #header-extra>
              <n-space :size="8">
                <n-button
                  size="tiny"
                  secondary
                  type="info"
                  @click="restoreTaskDisplay"
                >
                  恢复历史
                </n-button>
                <n-button
                  size="tiny"
                  secondary
                  type="warning"
                  @click="clearTaskDisplay"
                >
                  清空显示
                </n-button>
              </n-space>
            </template>

            <n-data-table
              :columns="taskColumns"
              :data="recentTasks"
              :bordered="false"
              striped
              size="small"
              :max-height="250"
            />
          </n-card>
        </n-gi>

        <n-gi :span="3">
          <n-card size="small" class="module-card" segmented>
            <template #header>
              <div style="display: flex; align-items: center; gap: 8px">
                <n-icon :size="20"><BookOpen /></n-icon>
                <span>快速上手指南与常见问题(Quick start/Q&A)</span>
              </div>
            </template>

            <n-alert type="info" show-icon style="margin-bottom: 20px">
              提示：在开始神经网络优化前，请确保至少已通过 CST
              传统算法积累了足量的高保真样本数据。
            </n-alert>

            <n-steps
              :current="currentStep"
              status="process"
              style="margin-bottom: 24px"
            >
              <n-step
                title="定义问题"
                description="在 CST 模式设置设计变量、约束边界与优化目标。"
                @click="currentStep = 1"
                style="cursor: pointer"
              />
              <n-step
                title="联合仿真"
                description="启动联合仿真模式，调用 CST 自动寻优并沉淀数据池。"
                @click="currentStep = 2"
                style="cursor: pointer"
              />
              <n-step
                title="代理模型"
                description="切换至神经网络模式，采用SAEA实现代理辅助进化。"
                @click="currentStep = 3"
                style="cursor: pointer"
              />
            </n-steps>

            <div
              style="text-align: center; margin-top: 16px; padding-bottom: 10px"
            >
              <n-button
                type="primary"
                dashed
                size="large"
                @click="showDocs = true"
              >
                <template #icon
                  ><n-icon><BookOpen /></n-icon
                ></template>
                查看完整平台手册与打分机制公示
              </n-button>
            </div>
          </n-card>
        </n-gi>
      </n-grid>
      <n-card class="modern-card simulator-card" size="small">
        <template #header>
          <span
            class="card-title"
            style="display: flex; align-items: center; gap: 8px"
          >
            算法评分机制模拟器 (Score Simulator)
          </span>
        </template>

        <n-grid :x-gap="24" :y-gap="24" :cols="24">
          <n-gi :span="8">
            <div class="sim-panel">
              <div class="sim-panel-title">假设 CST 输出了以下波形特征</div>
              <n-form label-placement="left" label-width="120" size="small">
                <n-form-item label="主频 (GHz)"
                  ><n-input-number v-model:value="simMetrics.freq" :step="0.01"
                /></n-form-item>
                <n-form-item label="杂波比 (0~1)"
                  ><n-slider
                    v-model:value="simMetrics.sideRatio"
                    :min="0"
                    :max="1"
                    :step="0.01"
                /></n-form-item>
                <n-form-item label="平均功率 (MW)"
                  ><n-input-number
                    v-model:value="simMetrics.powerVal"
                    :step="1"
                /></n-form-item>
                <n-form-item label="功率波动率 (%)"
                  ><n-slider
                    v-model:value="simMetrics.powerFluc"
                    :min="0"
                    :max="50"
                    :step="1"
                /></n-form-item>
                <n-form-item label="平均效率 (%)"
                  ><n-input-number v-model:value="simMetrics.effVal" :step="1"
                /></n-form-item>
                <n-form-item label="效率波动率 (%)"
                  ><n-slider
                    v-model:value="simMetrics.effFluc"
                    :min="0"
                    :max="50"
                    :step="1"
                /></n-form-item>
              </n-form>
            </div>
          </n-gi>

          <n-gi :span="10">
            <div class="sim-panel">
              <div
                class="sim-panel-title"
                style="
                  display: flex;
                  justify-content: space-between;
                  align-items: center;
                  border-bottom: 1px dashed var(--n-border-color);
                  padding-bottom: 8px;
                  margin-bottom: 16px;
                "
              >
                <span>您的优化门控设定</span>
                <n-radio-group v-model:value="simAlgo" size="small">
                  <n-radio-button value="GA">GA/PSO (断崖)</n-radio-button>
                  <n-radio-button value="BO">BO (平滑)</n-radio-button>
                </n-radio-group>
              </div>

              <n-collapse
                :default-expanded-names="['f', 'p', 'e']"
                style="margin-top: -8px"
              >
                <n-collapse-item title="频率目标" name="f">
                  <template #header-extra>
                    <n-switch
                      v-model:value="simConfigs.freq.enable"
                      size="small"
                      @click.stop
                    />
                  </template>
                  <n-space
                    align="center"
                    v-if="simConfigs.freq.enable"
                    :size="12"
                  >
                    <span>目标:</span>
                    <n-input-number
                      v-model:value="simConfigs.freq.target"
                      size="small"
                      style="width: 90px"
                      :step="0.01"
                    />
                    <n-text depth="3">GHz</n-text>

                    <n-divider vertical />

                    <span>盲区 ±</span>
                    <n-input-number
                      v-model:value="simConfigs.freq.blindGap"
                      size="small"
                      style="width: 100px"
                      :step="0.01"
                    />
                    <n-text depth="3">GHz</n-text>
                  </n-space>
                </n-collapse-item>

                <n-collapse-item title="功率设定" name="p">
                  <template #header-extra>
                    <n-switch
                      v-model:value="simConfigs.power.enable"
                      size="small"
                      @click.stop
                    />
                  </template>
                  <div
                    v-if="simConfigs.power.enable"
                    style="
                      display: flex;
                      flex-direction: column;
                      gap: 12px;
                      font-size: 13px;
                    "
                  >
                    <n-space align="center">
                      <span>模式:</span>
                      <n-radio-group
                        v-model:value="simConfigs.power.mode"
                        size="small"
                      >
                        <n-radio-button value="max">最大化</n-radio-button>
                        <n-radio-button value="target">逼近定值</n-radio-button>
                      </n-radio-group>
                    </n-space>

                    <n-space align="center" :size="12">
                      <span>淘汰死区: < </span>
                      <n-input-number
                        v-model:value="simConfigs.power.deadThresh"
                        size="small"
                        style="width: 80px"
                        :show-button="false"
                      />
                      <n-text depth="3">MW</n-text>

                      <n-divider vertical />

                      <span>权重:</span>
                      <n-input-number
                        v-model:value="simConfigs.power.weight"
                        size="small"
                        style="width: 60px"
                        :step="0.1"
                        :show-button="false"
                      />
                    </n-space>

                    <n-space
                      align="center"
                      v-if="simConfigs.power.mode === 'target'"
                      :size="12"
                    >
                      <span>目标值:</span>
                      <n-input-number
                        v-model:value="simConfigs.power.target"
                        size="small"
                        style="width: 80px"
                        :show-button="false"
                      />
                      <n-text depth="3">MW</n-text>

                      <n-divider vertical />

                      <span>容差:</span>
                      <n-input-number
                        v-model:value="simConfigs.power.tolerance"
                        size="small"
                        style="width: 60px"
                        :show-button="false"
                      />
                      <n-text depth="3">%</n-text>
                    </n-space>
                  </div>
                </n-collapse-item>

                <n-collapse-item title="效率设定" name="e">
                  <template #header-extra>
                    <n-switch
                      v-model:value="simConfigs.eff.enable"
                      size="small"
                      @click.stop
                    />
                  </template>
                  <div
                    v-if="simConfigs.eff.enable"
                    style="
                      display: flex;
                      flex-direction: column;
                      gap: 12px;
                      font-size: 13px;
                    "
                  >
                    <n-space align="center">
                      <span>模式:</span>
                      <n-radio-group
                        v-model:value="simConfigs.eff.mode"
                        size="small"
                      >
                        <n-radio-button value="max">最大化</n-radio-button>
                        <n-radio-button value="target">逼近定值</n-radio-button>
                      </n-radio-group>
                    </n-space>

                    <n-space align="center" :size="12">
                      <span>淘汰死区: < </span>
                      <n-input-number
                        v-model:value="simConfigs.eff.deadThresh"
                        size="small"
                        style="width: 80px"
                        :show-button="false"
                      />
                      <n-text depth="3">%</n-text>

                      <n-divider vertical />

                      <span>权重:</span>
                      <n-input-number
                        v-model:value="simConfigs.eff.weight"
                        size="small"
                        style="width: 60px"
                        :step="0.1"
                        :show-button="false"
                      />
                    </n-space>

                    <n-space
                      align="center"
                      v-if="simConfigs.eff.mode === 'target'"
                      :size="12"
                    >
                      <span>目标值:</span>
                      <n-input-number
                        v-model:value="simConfigs.eff.target"
                        size="small"
                        style="width: 80px"
                        :show-button="false"
                      />
                      <n-text depth="3">%</n-text>

                      <n-divider vertical />

                      <span>容差:</span>
                      <n-input-number
                        v-model:value="simConfigs.eff.tolerance"
                        size="small"
                        style="width: 60px"
                        :show-button="false"
                      />
                      <n-text depth="3">%</n-text>
                    </n-space>
                  </div>
                </n-collapse-item>
              </n-collapse>
            </div>
          </n-gi>

          <n-gi :span="6">
            <div class="sim-panel result-panel" :class="scoreResult.theme">
              <div
                class="sim-panel-title"
                style="text-align: center; margin-bottom: 24px"
              >
                引擎最终评判
              </div>
              <div class="score-display">
                <span class="score-value">{{
                  scoreResult.val.toExponential(2)
                }}</span>
              </div>
              <div class="score-reason">
                <n-icon size="16" style="margin-right: 4px"></n-icon>
                {{ scoreResult.reason }}
              </div>
            </div>
          </n-gi>
        </n-grid>
      </n-card>
    </n-space>
    <n-drawer
      v-model:show="showDocs"
      :width="550"
      placement="left"
      :class="isDarkMode ? 'acrylic-drawer-dark' : 'acrylic-drawer-light'"
    >
      <n-drawer-content title="SAEA 平台使用手册" closable>
        <n-tabs type="line" animated>
          <n-tab-pane name="qa" tab="操作与任务 (Q&A)">
            <n-scrollbar
              style="height: calc(100vh - 180px)"
              content-style="padding-right: 16px; padding-bottom: 24px;"
            >
              <div class="faq-module">
                <div class="faq-group-title">
                  <n-icon><Monitor /></n-icon> 环境与任务运行
                </div>
                <n-collapse class="faq-collapse">
                  <n-collapse-item name="q1">
                    <template #header
                      ><span class="faq-q"
                        >Q: 启动优化前需要做哪些准备？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge">A</div>
                      <div class="faq-a-text">
                        请务必关闭待优化器件的 CST
                        进程，否则会导致优化引擎启动失败（文件被锁）。一般情况下，只打开
                        CST 软件界面或者打开别的 CST
                        项目文件，不会影响当前优化任务的进行。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="q2">
                    <template #header
                      ><span class="faq-q"
                        >Q: 网页关了或者刷新了，优化会断吗？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge">A</div>
                      <div class="faq-a-text">
                        不会，平台为前后端分离架构，只要后台的 Python
                        终端不关，任务就会在后台持续运行。重新打开网页进入 CST
                        优化界面时，系统会弹窗询问您是否接管当前正在运行的后台任务。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="q3">
                    <template #header
                      ><span class="faq-q"
                        >Q: 中途报错、死机或停电，数据白跑了吗？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge">A</div>
                      <div class="faq-a-text">
                        平台具备智能数据抢救机制。每次 CST
                        跑完一个个体，数据和波形均已实时落库（SQLite）。即使意外中断，您也能在主页的“最近任务”中追溯并恢复该任务的所有历史图表与参数，数据库管理页面也可以搜索历史数据。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>

                <div class="faq-group-title" style="margin-top: 24px">
                  <n-icon><BrainCircuit /></n-icon> 高级寻优策略 (加速与微调)
                </div>
                <n-collapse class="faq-collapse">
                  <n-collapse-item name="q6">
                    <template #header
                      ><span class="faq-q"
                        >Q:
                        遇到结构相似的新管子，必须重新收集数据训练模型吗？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge" style="background: #8b5cf6">
                        A
                      </div>
                      <div class="faq-a-text">
                        一般情况下不需要，这是平台“在线微调 (Online
                        Learning)”的优势区间。只需加载旧管子的模型，开启在线微调并跑几十代。系统会将
                        神经网络预测的高分个体送入 CST
                        进行物理校验，并把真机结果“反向喂给”模型。仅需极少量的验证样本，模型就能在演化中“领悟”新管子的物理漂移规律，极大节省算力。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="q7">
                    <template #header
                      ><span class="faq-q"
                        >Q: 初始优良基因注入 (Inject) 有什么用？怎么用？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge" style="background: #8b5cf6">
                        A
                      </div>
                      <div class="faq-a-text">
                        如果之前这个管子已经跑过一些仿真，并且得到了还不错的参数组合，就可以尝试使用该功能。点击“生成当前变量模板”，填入数值后粘贴即可。引擎会强制将这组参数作为进化第
                        1 代的 0
                        号个体。这样可以让GA在初始阶段就获得一个优秀父代，基于平台的精英保留策略，之后的优化结果只会比这个初始参数组更好。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="q8">
                    <template #header
                      ><span class="faq-q"
                        >Q: 什么时候该开启“自适应变异 (Auto-Adaptive)”？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge" style="background: #8b5cf6">
                        A
                      </div>
                      <div class="faq-a-text">
                        一般情况下都建议开启这个功能。启用该功能后GA优化引擎会接管变异算子，按照进度条自动执行平滑过渡：前期大范围撒网探索（均匀变异）
                        ➔ 中期快速向高峰靠拢（高斯变异） ➔
                        后期在极小范围内极限压榨性能（布列德变异）。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>

                <div class="faq-group-title" style="margin-top: 24px">
                  <n-icon><ClipboardList /></n-icon> 平台交互与数据管理
                </div>
                <n-collapse class="faq-collapse">
                  <n-collapse-item name="q9">
                    <template #header
                      ><span class="faq-q"
                        >Q:
                        历史任务列表太拥挤了，点击“清空显示”会删掉底层数据吗？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge" style="background: #64748b">
                        A
                      </div>
                      <div class="faq-a-text">
                        绝对不会。点击“清空显示”仅仅是在浏览器的前端视图中将其隐藏，让工作台保持清爽。后台
                        SQLite
                        数据库中所有跑出的数据（波形、分数、参数）都完好无损。如果需要找回对比，点击旁边的“恢复历史”即可瞬间全部读取。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="q10">
                    <template #header
                      ><span class="faq-q"
                        >Q: 可以同时打开多个网页标签页跑不同的优化任务吗？</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-badge" style="background: #64748b">
                        A
                      </div>
                      <div class="faq-a-text">
                        不建议这样做。因为底层 CST Studio 软件调用的是系统级的
                        COM 接口，并发开启多个 CST
                        实例极易导致许可证冲突或内存溢出崩溃。建议排队串行运行，确保每一批数据的完整落库。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-scrollbar>
          </n-tab-pane>

          <n-tab-pane name="charts" tab="图表分析辞典 (Charts)">
            <n-scrollbar
              style="height: calc(100vh - 180px)"
              content-style="padding-right: 16px; padding-bottom: 24px;"
            >
              <div class="faq-module">
                <div class="faq-module-title cst-title" style="font-size: 16px">
                  <n-icon><Cpu /></n-icon> CST 联合仿真图表
                </div>
                <n-collapse class="faq-collapse">
                  <n-collapse-item name="c1">
                    <template #header
                      ><span class="faq-q"
                        >1. 帕累托散点云图 (Pareto Scatter)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b>
                        观察多目标的权衡边界与种群质量分布。<br /><b>读法：</b>
                        X/Y
                        轴可自由切换指标。颜色映射该个体的“综合打分”。暖色（红/橙）代表高分优质解，冷色（深蓝）代表被惩罚的劣质解或死波。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="c2">
                    <template #header
                      ><span class="faq-q"
                        >2. 代际最优收敛趋势 (Trend Line)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 监控遗传算法的演化健康度。<br /><b
                          >读法：</b
                        >
                        双 Y
                        轴分别追踪每一代的最高效率和最高功率。如果曲线稳步爬升说明演化正常；如果曲线长期平坦（超过10代毫无波澜），说明算法已收敛至物理极限，或陷入了局部最优死胡同。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="c3">
                    <template #header
                      ><span class="faq-q"
                        >3. 波形审查台 (Waveform Inspector)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 验证高分个体的物理真实性。<br /><b
                          >读法：</b
                        >
                        为保证网页流畅，后台对时频域曲线进行了降采样。主要用于快速观察波形是否平顶起振、是否存在严重杂波干扰。严谨的细节分析仍需返回
                        CST 软件内查看原始数据。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>

              <div class="faq-module" style="margin-top: 24px">
                <div class="faq-module-title nn-title" style="font-size: 16px">
                  <n-icon><Network /></n-icon> 代理辅助 AI 图表 (XAI)
                </div>
                <n-collapse class="faq-collapse">
                  <n-collapse-item name="a1">
                    <template #header
                      ><span class="faq-q"
                        >1. 全局参数敏感度 (Global SHAP)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b>
                        宏观评估各个物理尺寸对器件性能的话语权。<br /><b
                          >读法：</b
                        >
                        在加载模型时全空间计算得出。如果某参数的敏感度占比极低（如不足
                        2%），说明它是个边缘角色。在下一轮 CST
                        设计中，可将其直接固定（Fix），以此实现维度降维，把算力集中在敏感核心参数上。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="a2">
                    <template #header
                      ><span class="faq-q"
                        >2. 局部参数贡献解构 (Local SHAP)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 微观拆解单次预测得分的“因果关系”。<br /><b
                          >读法：</b
                        >
                        在正向推演时生成。红色柱代表正向提升，绿色柱代表反向拉扯（或反之，视具体指标而定）。它能清晰回答：“为什么这次效率能到
                        80%？是因为电压拉高贡献了 20%，还是半径缩小贡献了 15%？”
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="a3">
                    <template #header
                      ><span class="faq-q"
                        >3. 优胜个体相关性热力图 (Pearson)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 挖掘隐藏的底层物理约束。<br /><b
                          >读法：</b
                        >
                        仅提取历代排名前 50%
                        的“尖子生”进行统计。深红代表正相关，深蓝代表负相关。如果参数A和B呈现深蓝，意味着在优秀器件中，A变大B就必须变小。这能在一定程度上指导后续管子的参数调节策略。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="a4">
                    <template #header
                      ><span class="faq-q"
                        >4. 平行坐标系 (Parallel Coordinates)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 多维高维数据的轨迹追踪。<br /><b
                          >读法：</b
                        >
                        在目标轴（如效率）上框选高分区间，系统会高亮这些优秀个体经过所有输入参数轴时的轨迹。借此可以一眼看出高效率通常扎堆在哪些参数组合区间内。
                      </div>
                    </div>
                  </n-collapse-item>
                  <n-collapse-item name="a5">
                    <template #header
                      ><span class="faq-q"
                        >5. 3D 参数地形扫描 (3D Surface)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 输入输出关系可视化。<br /><b>读法：</b>
                        固定其他参数，扫描选定的 X 和
                        Y。通过观察3D地形图，可以快速分析锚定的两个输入参数与输出结果之间的三维关系。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-scrollbar>
          </n-tab-pane>

          <n-tab-pane name="math" tab="打分机制 (V2.0)">
            <n-scrollbar
              style="height: calc(100vh - 180px)"
              content-style="padding-right: 16px; padding-bottom: 24px;"
            >
              <n-alert
                type="info"
                :bordered="false"
                style="margin-bottom: 16px"
              >
                平台已升级至双轨制评价引擎。GA/PSO 使用阶跃断崖加速淘汰，BO
                使用平缓渐近线保障空间导数连续。
              </n-alert>

              <n-h4>1. 频率偏移重罚</n-h4>
              <p style="font-size: 13px; color: var(--n-text-color-3)">
                <b>[GA/PSO] 线性断崖惩罚：</b>
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 10px;
                  border-radius: 6px;
                  font-family: monospace;
                  text-align: center;
                  margin-bottom: 8px;
                "
              >
                Score = -P<sub>base</sub> &times; (1 + k &middot; |f -
                f<sub>target</sub>|)
              </div>
              <p style="font-size: 13px; color: var(--n-text-color-3)">
                <b>[BO] 有理渐近线平滑惩罚 (防跌穿)：</b>
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 10px;
                  border-radius: 6px;
                  font-family: monospace;
                  text-align: center;
                "
              >
                Score = -10000 - 30000 &times; [ &Delta;f / (&Delta;f + 0.5) ]
              </div>

              <n-h4>2. 物理死区拦截 (Dead Zone)</n-h4>
              <p style="font-size: 13px; color: var(--n-text-color-3)">
                <b>[GA/PSO] 瞬间淘汰：</b> Score = -300
              </p>
              <p style="font-size: 13px; color: var(--n-text-color-3)">
                <b>[BO] 相对深度陡坡：</b>
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 10px;
                  border-radius: 6px;
                  font-family: monospace;
                  text-align: center;
                "
              >
                depth = (Thresh - Actual) / Thresh <br />
                Score = -(100 + 1000 &times; depth)
              </div>

              <n-h4>3. 性能加权得分 (安全区 1:1 配平)</n-h4>
              <p style="font-size: 13px; color: var(--n-text-color-3)">
                底层自动进行量纲归一化。Target 模式与 Maximize 模式等价竞争：
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 10px;
                  border-radius: 6px;
                  font-family: monospace;
                  text-align: center;
                "
              >
                Score<sub>max</sub> += (Actual / Scale_Ref) &times; W
                <br /><br />
                Score<sub>target</sub> -= (Dist_from_Edge / Target) &times; W
              </div>
            </n-scrollbar>
          </n-tab-pane>
        </n-tabs>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import {
  ref,
  h,
  onMounted,
  onUnmounted,
  computed,
  reactive,
  inject,
} from "vue";
import { useRouter } from "vue-router";
import { NTag, NProgress, NButton, useMessage, NIcon } from "naive-ui"; // ✨ 新增引入 NIcon
import {
  Monitor,
  RefreshCw,
  ClipboardList,
  BookOpen,
  HelpCircle,
  Database,
} from "lucide-vue-next";
import axios from "axios";
const showDocs = inject("globalDocsVisible", ref(false));
const router = useRouter();
const isDarkMode = inject("globalTheme");
const message = useMessage();
const restoreTaskDisplay = () => {
  localStorage.removeItem("zttt_hidden_tasks");
  fetchRecentTasks(); // 重新向后端拉取一次完整数据
  message.success("已恢复所有历史任务显示！");
};
const API_BASE = "/api";
// 路由跳转
const goToPage = (routeName) => {
  router.push({ name: routeName });
};

// ==========================================
// 模块 1: 系统探针逻辑
// ==========================================
const apiStatus = ref("error");
const cstStatus = ref("error");
const agentsStatus = ref("error");
const cpuUsage = ref(0);
const ramUsage = ref(0);

const cpuColor = computed(() =>
  cpuUsage.value > 80 ? "#ef4444" : cpuUsage.value > 50 ? "#f59e0b" : "#10b981",
);
const ramColor = computed(() => (ramUsage.value > 85 ? "#ef4444" : "#3b82f6"));

let pollInterval = null;

const refreshSystemStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/health`);
    if (res.data.status === "ok") {
      apiStatus.value = "running";
      cstStatus.value = "running";
      agentsStatus.value = "running"; // ✨ 新增：连通时绿灯
    }
  } catch (e) {
    apiStatus.value = "error";
    cstStatus.value = "error";
    agentsStatus.value = "error"; // ✨ 新增：断开时红灯
  }
};

const fetchHardwareStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/system_status`);
    if (res.data.status === "success") {
      cpuUsage.value = Math.round(res.data.cpu);
      ramUsage.value = Math.round(res.data.ram);
    }
  } catch (e) {
    console.error("无法获取硬件状态", e);
  }
};

// ==========================================
// 模块 2: 最近任务逻辑 (DataTable)
// ==========================================
const taskColumns = [
  { title: "任务名称", key: "name", width: 150 },
  {
    title: "状态",
    key: "status",
    width: 100,
    render(row) {
      const typeMap = { running: "info", completed: "success", error: "error" };
      const textMap = {
        running: "运行中",
        completed: "已完成",
        error: "异常中断",
      };
      return h(
        NTag,
        {
          type: typeMap[row.status] || "default",
          bordered: false,
          size: "small",
        },
        { default: () => textMap[row.status] || row.status },
      );
    },
  },
  {
    title: "演化进度 (Gen)",
    key: "progress",
    render(row) {
      if (row.status === "error")
        return h("span", { style: "color: #ef4444" }, "已停止");
      return h(NProgress, {
        type: "line",
        percentage: Math.round((row.currentGen / row.totalGen) * 100),
        indicatorPlacement: "inside",
        processing: row.status === "running",
      });
    },
  },
  {
    title: "操作",
    key: "actions",
    width: 100,
    render(row) {
      return h(
        NButton,
        {
          size: "small",
          secondary: true,
          type: "primary",
          onClick: () => {
            message.info(`正在跳转任务：${row.name}`);
            goToPage("CstOpt");
          },
        },
        { default: () => "进入工作台" },
      );
    },
  },
];

const recentTasks = ref([]);

const fetchRecentTasks = async () => {
  try {
    const res = await axios.get(`${API_BASE}/recent_tasks`);
    if (res.data.status === "success") {
      // ✨ 1. 读取本地缓存的“视觉黑名单”
      const hiddenTaskIds = JSON.parse(
        localStorage.getItem("zttt_hidden_tasks") || "[]",
      );

      // ✨ 2. 过滤掉被隐藏的任务，只显示没被隐藏的
      recentTasks.value = res.data.tasks.filter(
        (t) => !hiddenTaskIds.includes(t.id),
      );
    }
  } catch (e) {
    console.error("获取最近任务失败", e);
  }
};

const clearTaskDisplay = () => {
  if (recentTasks.value.length === 0) {
    message.info("当前列表已经为空啦");
    return;
  }

  // 1. 获取已有的黑名单
  const hiddenTaskIds = JSON.parse(
    localStorage.getItem("zttt_hidden_tasks") || "[]",
  );

  // 2. 提取当前正在显示的所有任务 ID
  const currentIds = recentTasks.value.map((t) => t.id);

  // 3. 合并去重，生成新的黑名单并存入浏览器缓存
  const newHidden = [...new Set([...hiddenTaskIds, ...currentIds])];
  localStorage.setItem("zttt_hidden_tasks", JSON.stringify(newHidden));

  // 4. 瞬间清空当前界面的表格
  recentTasks.value = [];
  message.success("已清空列表显示（后台仿真数据安全保留）");
};
// ==========================================
// 初始化与定时轮询 (真实对接)
// ==========================================
onMounted(() => {
  refreshSystemStatus();
  fetchHardwareStatus();
  fetchRecentTasks();

  // 每 2.5 秒静默刷新一次系统探针和任务列表
  pollInterval = setInterval(() => {
    fetchHardwareStatus();
    fetchRecentTasks();
  }, 2500);
});

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval);
});

const currentStep = ref(1);
const simMetrics = reactive({
  freq: 2.35,
  sideRatio: 0.05,
  powerVal: 850, // kW
  powerFluc: 8, // %
  effVal: 52.0, // %
  effFluc: 12, // %
});

const simAlgo = ref("GA"); // 新增：算法流派选择状态

const simConfigs = reactive({
  freq: {
    enable: true,
    target: 2.4,
    blindGap: 0.05,
    penaltyBase: 10000,
    decayK: 10.0,
    clutterPenalty: 3000,
  },
  power: {
    enable: true,
    mode: "target",
    target: 800,
    deadThresh: 1.0,
    weight: 1.0,
    fluc: 10,
    tolerance: 10,
  },
  eff: {
    enable: true,
    mode: "max",
    target: 50.0,
    deadThresh: 1.0,
    weight: 6.0,
    fluc: 15,
    tolerance: 10,
    checkPhys: true,
  },
});

// 🚀 完全复刻 evaluator.py V2.0 双轨制标准
const scoreResult = computed(() => {
  const m = simMetrics;
  const c = simConfigs;
  const isBO = simAlgo.value === "BO";
  const BASE_L3 = -10.0;

  // ====== 1. Level 4 致命物理崩溃 ======
  const isFatal =
    m.freq <= 0 ||
    (c.eff.enable && c.eff.checkPhys && (m.effVal < 0 || m.effVal > 100));
  if (isFatal) {
    return {
      val: isBO ? -50000.0 : -10000000.0, // BO 谷底 vs GA 负一千万
      reason: "💀 致命物理错误 (波形无效或违背常理)",
      theme: "fatal",
    };
  }

  let penalty_score = 0.0;
  let is_dead = false;
  let reason_text = "✅ 跨越死区：正常加权得分";
  let theme = "success";

  // ====== 2. Level 3 频率判决 ======
  if (c.freq.enable) {
    const diff = Math.abs(m.freq - c.freq.target);
    if (diff > c.freq.blindGap) {
      is_dead = true;
      theme = "error";
      if (isBO) {
        // BO 专属：有理渐近线平滑惩罚
        const net_diff = diff - c.freq.blindGap;
        const base_penalty = -Math.abs(c.freq.penaltyBase);
        const max_extra_penalty = 30000.0;
        const decay_k = 0.5;
        penalty_score +=
          base_penalty - max_extra_penalty * (net_diff / (net_diff + decay_k));
        reason_text = "📉 BO 频率渐近惩罚 (逼近 -40000)";
      } else {
        // GA/PSO 专属：线性断崖深渊
        const base = -Math.abs(c.freq.penaltyBase);
        penalty_score += base * (1.0 + c.freq.decayK * diff);
        reason_text = "📉 GA/PSO 频率越界断崖惩罚";
        return { val: penalty_score, reason: reason_text, theme: theme }; // GA 直接短路
      }
    }
    if (m.sideRatio > 0.1) {
      is_dead = true;
      theme = "warning";
      penalty_score -= Math.abs(c.freq.clutterPenalty) * m.sideRatio;
      reason_text = "⚠️ 杂波超标惩罚";
      if (!isBO)
        return { val: penalty_score, reason: reason_text, theme: theme };
    }
  }

  // ====== 3. Level 2 淘汰死区 ======
  if (!is_dead) {
    const p_thresh = c.power.enable ? c.power.deadThresh : 0;
    const e_thresh = c.eff.enable ? c.eff.deadThresh : 0;

    if (isBO) {
      // BO 专属：相对跌破深度陡坡
      let dead_zone_penalty = 0;
      if (p_thresh > 0 && m.powerVal < p_thresh) {
        const depth = (p_thresh - m.powerVal) / p_thresh;
        dead_zone_penalty -= 100.0 + 1000.0 * depth;
        is_dead = true;
      }
      if (e_thresh > 0 && m.effVal < e_thresh) {
        const depth = (e_thresh - m.effVal) / e_thresh;
        dead_zone_penalty -= 100.0 + 1000.0 * depth;
        is_dead = true;
      }
      if (is_dead) {
        penalty_score += dead_zone_penalty;
        reason_text = "🕳️ BO 死区相对深度陡坡惩罚";
        theme = "fatal";
      }
    } else {
      // GA/PSO 专属：一刀切 -300
      if (
        (p_thresh > 0 && m.powerVal < p_thresh) ||
        (e_thresh > 0 && m.effVal < e_thresh)
      ) {
        return {
          val: -300.0,
          reason: "🧱 GA/PSO 断崖淘汰死区 (-300)",
          theme: "fatal",
        };
      }
    }
  }

  // BO 如果在前两关落入深渊，直接返回惩罚分（维持处处可导）
  if (is_dead || penalty_score < 0) {
    return { val: penalty_score, reason: reason_text, theme: theme };
  }

  // ====== 4. 模块 0：公共奖励 (安全区) ======
  let reward_score = 0.0;

  const processMetric = (metric_key, isEff) => {
    const o = c[metric_key];
    if (!o.enable) return;

    const val = isEff ? m.effVal : m.powerVal;
    const fluc = isEff ? m.effFluc : m.powerFluc;
    const raw_target = o.target;

    const tol_fluc = o.fluc / 100.0;
    const tol_target = o.tolerance / 100.0;
    const weight = o.weight;

    let target_val, norm_val, actual_val;

    if (!isEff) {
      target_val = raw_target * 1e6; // 归一化基准
      actual_val = val * 1e6;
      norm_val = actual_val / (target_val + 1e-6);
    } else {
      target_val = raw_target;
      actual_val = val;
      norm_val = actual_val / 100.0;
    }

    // 时域纹波罚分
    if (fluc / 100.0 > tol_fluc) {
      reward_score += BASE_L3 * (fluc / 100.0 / tol_fluc) * 2.0;
    }

    // 目标逼近加/扣分 (1:1 梯度配平)
    if (o.mode === "target") {
      if (actual_val < target_val) {
        const diff_from_target = target_val - actual_val;
        const allowed_error = target_val * tol_target;

        if (diff_from_target > allowed_error) {
          const dist_from_edge = diff_from_target - allowed_error;
          // 边缘平滑扣分
          reward_score += BASE_L3 * (dist_from_edge / (allowed_error + 1e-6));
          // ✨ 移除 * 10.0，与最大化模式对等
          const norm_dist = dist_from_edge / (target_val + 1e-6);
          reward_score -= norm_dist * weight;
        }
      }
    } else {
      // Maximize 模式
      reward_score += norm_val * weight;
    }
  };

  processMetric("power", false);
  processMetric("eff", true);

  if (reward_score < 0) {
    theme = "warning";
    reason_text = "⚠️ 虽过死区，但纹波过大导致得分为负";
  }

  // ====== 5. 缩放输出 ======
  // BO 正分直接返回原值；GA/PSO 放大 100 倍以刺激变异
  if (isBO) {
    return { val: reward_score, reason: reason_text, theme: theme };
  } else {
    const display_score =
      reward_score > 0 ? reward_score * 100.0 : reward_score;
    return { val: display_score, reason: reason_text, theme: theme };
  }
});
</script>

<style scoped>
.home-container {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

/* 欢迎区样式 */
.welcome-header {
  text-align: center;
  margin-bottom: 20px;
}
.glow-text {
  font-size: 36px;
  font-weight: 800;
  margin: 0;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 2px;
}
.sub-title {
  color: var(--n-text-color-3);
  font-size: 16px;
  margin-top: 8px;
}

/* 导航大卡片 */
.nav-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
  background-color: var(--n-card-color);
  /* 👇 质感升级 */
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow:
    0 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(255, 255, 255, 0.06) !important;
}
.nav-card:hover {
  transform: translateY(-5px);
  /* 👇 hover 时阴影扩散，高光变亮 */
  box-shadow:
    0 12px 28px rgba(0, 0, 0, 0.3),
    inset 0 1px 2px rgba(255, 255, 255, 0.15) !important;
}
.cst-card:hover {
  border-color: #3b82f6;
}
.nn-card:hover {
  border-color: #10b981;
}
.db-card:hover {
  border-color: #3b82f6;
}
.db-card:hover .nav-action {
  color: #3b82f6;
}

.nav-content {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px;
}

/* ✨ 替换原来的 emoji nav-icon 样式，使用自定义图片框样式 */
.custom-icon-box {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 72px;
  height: 72px;
  background: var(--n-action-color); /* ✅ 替换为 NaiveUI 自适应次级背景色 */
  border-radius: 12px;
  padding: 10px;
  flex-shrink: 0;
}
.custom-logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 4px 6px rgba(0, 0, 0, 0.3));
}

.nav-text h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: var(--n-text-color);
}
.nav-text p {
  margin: 0;
  color: var(--n-text-color-2);
  font-size: 14px;
  line-height: 1.5;
}
.nav-action {
  margin-top: 20px;
  text-align: right;
  font-weight: bold;
  color: var(--n-text-color-3);
}
.cst-card:hover .nav-action {
  color: #3b82f6;
}
.nn-card:hover .nav-action {
  color: #10b981;
}

/* 模块卡片 */
.module-card {
  border-radius: 12px;
  height: 100%;
}
.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--n-text-color-2);
}
.probe-label {
  font-size: 12px;
  color: var(--n-text-color-3);
  margin-top: -10px;
}
.simulator-card {
  border-color: rgba(59, 130, 246, 0.3);
}
.sim-panel {
  background-color: var(--n-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
}
.sim-panel-title {
  font-size: 13px;
  font-weight: bold;
  color: var(--n-text-color-3);
  margin-bottom: 16px;
  border-bottom: 1px dashed var(--n-border-color);
  padding-bottom: 8px;
}
.nav-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.nav-action {
  transition: color 0.3s ease;
}

/* 1. 扫参卡片：科技蓝 (搭配 CST Logo) */
.nav-card.sweep-card:hover {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
  transform: translateY(-4px); /* 悬浮时轻微上浮 */
}
.nav-card.sweep-card:hover .nav-action {
  color: #3b82f6;
}

/* 2. 优化卡片：翡翠绿 (搭配 CST Logo) */
.nav-card.cst-card:hover {
  border-color: #10b981 !important;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.cst-card:hover .nav-action {
  color: #10b981;
}

/* 3. 神经网络卡片：霓虹紫 (搭配 PyCharm Logo 的深色调) */
.nav-card.nn-card:hover {
  border-color: #8b5cf6 !important;
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.nn-card:hover .nav-action {
  color: #8b5cf6;
}

/* 4. 数据库卡片：活力橙 (完美契合 DataGrip Logo) */
.nav-card.db-card:hover {
  border-color: #f59e0b !important;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.db-card:hover .nav-action {
  color: #f59e0b;
}
.result-panel {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transition: all 0.3s;
}
.score-display {
  margin-bottom: 16px;
}
.score-value {
  font-size: 32px;
  font-weight: 900;
  font-family: monospace;
}
.score-reason {
  font-size: 13px;
  font-weight: bold;
}

/* 动态主题颜色 */
.result-panel.fatal {
  background-color: rgba(225, 29, 72, 0.1);
  border-color: #e11d48;
  color: #e11d48;
}
.result-panel.error {
  background-color: rgba(244, 63, 94, 0.1);
  border-color: #f43f5e;
  color: #f43f5e;
}
.result-panel.warning {
  background-color: rgba(245, 158, 11, 0.1);
  border-color: #f59e0b;
  color: #f59e0b;
}
.result-panel.success {
  background-color: rgba(16, 185, 129, 0.1);
  border-color: #10b981;
  color: #10b981;
}
/* ==========================================
   FAQ 使用手册专属现代样式
   ========================================== */
.faq-module {
  margin-bottom: 16px;
}
.faq-module-title {
  font-size: 20px;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--n-border-color);
}
.cst-title {
  color: #3b82f6;
}
.nn-title {
  color: #10b981;
}

.faq-group-title {
  font-size: 15px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: var(--n-text-color-2);
}

/* 覆盖 Naive UI 默认的边框和背景 */
.faq-collapse {
  background: var(--n-card-color);
  border: 1px solid var(--n-border-color);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}
:deep(.faq-collapse .n-collapse-item) {
  border-bottom: 1px solid var(--n-border-color);
}
:deep(.faq-collapse .n-collapse-item:last-child) {
  border-bottom: none;
}
:deep(.faq-collapse .n-collapse-item__header) {
  padding: 14px 16px !important;
  background: rgba(255, 255, 255, 0.02);
  transition: all 0.3s;
}
:deep(.faq-collapse .n-collapse-item__header:hover) {
  background: rgba(255, 255, 255, 0.05);
}

.faq-q {
  font-weight: 600;
  font-size: 14px;
  color: var(--n-text-color);
  letter-spacing: 0.5px;
}

/* 优雅的回答气泡区 */
.faq-a-box {
  display: flex;
  gap: 14px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.1);
  border-top: 1px dashed var(--n-border-color);
}
.faq-a-badge {
  background: #3b82f6;
  color: #fff;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 14px;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}
.faq-a-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--n-text-color-2);
  margin-top: 2px;
}

.home-theme-toggle {
  position: absolute;
  top: 32px;
  right: 40px;
  z-index: 100;
}
</style>

<style>
/* 深色模式亚克力抽屉 */
.acrylic-drawer-dark {
  background-color: rgba(24, 24, 28, 0.6) !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}
/* 浅色模式亚克力抽屉 */
.acrylic-drawer-light {
  background-color: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
}

/* 强制抽屉的 Header 和 Body 背景变透明，让毛玻璃透出来 */
.acrylic-drawer-dark .n-drawer-content,
.acrylic-drawer-light .n-drawer-content,
.acrylic-drawer-dark .n-drawer-header,
.acrylic-drawer-light .n-drawer-header,
.acrylic-drawer-dark .n-drawer-body-content-wrapper,
.acrylic-drawer-light .n-drawer-body-content-wrapper {
  background-color: transparent !important;
}

.acrylic-drawer-dark .n-tabs-tab.n-tabs-tab--active,
.acrylic-drawer-light .n-tabs-tab.n-tabs-tab--active,
.acrylic-drawer-dark .n-tabs-tab:hover,
.acrylic-drawer-light .n-tabs-tab:hover {
  background-color: transparent !important;
  box-shadow: none !important;
}

/* 顺便优化一下未选中时的字体透明度，让高亮更加聚焦 */
.acrylic-drawer-dark .n-tabs-tab,
.acrylic-drawer-light .n-tabs-tab {
  background-color: transparent !important;
}
</style>
