<template>
  <div class="home-container">
<!-- ================= 模块 1: 欢迎区与主题切换 ================= -->
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
<!-- ================= 模块 2: 核心功能导航卡片 (扫参/优化/神经网络/数据库) ================= -->
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

        <!-- 第5个卡片：文献助手，占据第三行左侧形成 2-2-1 -->
        <n-gi>
          <n-card
            class="nav-card lit-card"
            hoverable
            @click="goToPage('LiteratureAssistant')"
          >
            <div class="nav-content">
              <div class="custom-icon-box">
                <img
                  src="/deepseek-logo.png"
                  alt="DeepSeek Logo"
                  class="custom-logo-img"
                />
              </div>
              <div class="nav-text">
                <h3>教研室文献助手</h3>
                <p>基于本地知识库的高功率微波与计算机科学专属学术文献助手</p>
              </div>
            </div>
            <div class="nav-action">开始对话 ➡️</div>
          </n-card>
        </n-gi>
      </n-grid>

      <n-grid :x-gap="24" :y-gap="24" :cols="3">
<!-- ================= 模块 3: 系统探针面板 (API/CST/硬件负载) ================= -->
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
                <n-descriptions-item label="Python">
                  <span>{{ sysEnv.python }}</span>
                </n-descriptions-item>
                <n-descriptions-item label="PyTorch">
                  <span>{{ sysEnv.pytorch }}</span>
                </n-descriptions-item>
                <n-descriptions-item label="CST">
                  <span>{{ sysEnv.cst }}</span>
                </n-descriptions-item>
              </n-descriptions>
            </n-space>
          </n-card>
        </n-gi>
<!-- ================= 模块 4: 最近任务面板 ================= -->
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
      <ScoreSandbox />
    </n-space>
<!-- ================= 模块 5: 平台使用手册与打分机制 (抽屉视图) ================= -->
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
                        轴以及颜色都可以自由切换变量或者目标，通常建议将横纵轴设置为优化目标，颜色设置为分数。暖色（红/橙）代表高分优质解，冷色（深蓝）代表被惩罚的劣质解或死波。
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
                        多 Y
                        轴可通过用户自定义选取，分析不同的优化目标在GA迭代过程中的变化趋势。如果曲线稳步爬升说明演化正常；如果曲线长期平坦（超过10代毫无波澜），说明算法已收敛至物理极限，或陷入了局部最优死胡同。
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
                        为保证网页流畅，后台对时频域曲线稍微进行了降采样。主要用于快速观察波形是否平顶起振、是否存在严重杂波干扰。严谨的细节分析仍需返回
                        CST 软件内查看原始数据。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>

              <div class="faq-module" style="margin-top: 24px">
                <div class="faq-module-title nn-title" style="font-size: 16px">
                  <n-icon><Network /></n-icon> 代理辅助进化算法图表 (SAEA)
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
                        >2. 局部参数贡献解构 (正向预测部分)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 微观拆解单次预测得分的“因果关系”。<br /><b
                          >读法：</b
                        >
                        在正向预测时生成。红色柱代表正向提升，绿色柱代表反向拉扯（或反之，视具体指标而定）。它能清晰回答：“为什么这次效率能到
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
                        的“尖子生”进行统计。深红代表正相关，深蓝代表负相关。如果参数A和B呈现深蓝，意味着在优秀器件中，A变大通常情况下B就必须变小。这能在一定程度上指导后续管子的参数调节策略。
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
                        <b>功能：</b> 多维数据的轨迹追踪。<br /><b
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
                  <n-collapse-item name="a6">
                    <template #header
                      ><span class="faq-q"
                        >6. 在线学习监控台(Online Monitor)</span
                      ></template
                    >
                    <div class="faq-a-box">
                      <div class="faq-a-text">
                        <b>功能：</b> 数据反向微调代理模型过程可视化。<br /><b
                          >读法：</b
                        >
                        记录了每一代结果返回微调代理模型后，模型的损失函数以及预测误差。通常前半部分是二者都会有很大波动，在自适应变异策略离开了均匀变异或者演化进行到后半段时，曲线会
                        逐渐趋于稳定。数据库中保留了一次较为标准的在线学习微调的曲线图，名称为“测试V2”。
                      </div>
                    </div>
                  </n-collapse-item>
                </n-collapse>
              </div>
            </n-scrollbar>
          </n-tab-pane>

          <n-tab-pane name="math" tab="打分机制">
            <n-scrollbar
              style="height: calc(100vh - 180px)"
              content-style="padding-right: 16px; padding-bottom: 24px;"
            >
              <n-alert
                type="info"
                :bordered="false"
                style="margin-bottom: 16px; font-size: 15px; line-height: 1.6;"
              >
                平台已升级至
                <b>V3.0双轨评分</b>。对GA\PSO与BO采取两种评分曲线的拟合，较好的满足了不同算法对于评分梯度的需求。
                通过模块化的目标设置，以及对目标的物理意义高度解耦，实现了对更多微波器件的指标优化场景的覆盖。
              </n-alert>

              <n-h3>1. 基础适应度 (Base Fitness)</n-h3>
              <p style="font-size: 15px; color: var(--n-text-color-3)">
                无论个体死活，引擎首先基于基准尺 (Scale)
                计算无视死区的基础得分，作为保证边界连续性的锚点：
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 16px;
                  border-radius: 8px;
                  font-family: monospace;
                  margin-bottom: 20px;
                  line-height: 1.8;
                  font-size: 15px;
                "
              >
                <span style="color: #10b981; font-weight: bold"
                  >Maximize (最大化):</span
                ><br />
                Score = (Val / Scale) &times; Weight <br /><br />

                <span style="color: #3b82f6; font-weight: bold"
                  >Minimize (最小化):</span
                >
                <span style="color: var(--n-text-color-3); font-size: 14px"
                  >*翻转为正向奖励</span
                ><br />
                Score = [1.0 - (Val / Scale)] &times; Weight <br /><br />

                <span style="color: #f59e0b; font-weight: bold"
                  >Target (逼近定值):</span
                ><br />
                <span style="color: var(--n-text-color-3)">容差内:</span> Score
                = 1.0 &times; Weight <br />
                <span style="color: var(--n-text-color-3)">容差外:</span> Score
                = [1.0 - (Diff - Tol) / Scale] &times; Weight
              </div>

              <n-h3>2. 时频域软硬双重惩罚 (Soft/Hard Penalties)</n-h3>
              <p style="font-size: 15px; color: var(--n-text-color-3)">
                引入物理波形质量约束。在触碰绝对死区前，引擎会施加非线性缓坡惩罚过滤劣质波形：
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 16px;
                  border-radius: 8px;
                  font-family: monospace;
                  margin-bottom: 20px;
                  line-height: 1.8;
                  font-size: 15px;
                "
              >
                <span style="color: #f59e0b; font-weight: bold">时域波动率 (Fluctuation)：</span><br />
                波动 > 阈值A：触发软惩罚，最高削减此项基础分的 95%。<br />
                波动 > 阈值B (A的3倍)：波形崩溃，强制触发死区越界。<br /><br />
                
                <span style="color: #f59e0b; font-weight: bold">频域杂模抑制 (Side Ratio)：</span><br />
                杂波 > 阈值A：触发缓坡惩罚，最高削减此项基础分的 50%。<br />
                杂波 > 阈值B (A的3倍)：频域崩溃，强制触发死区越界。
              </div>

              <n-h3>3. 刚性拦截与惩罚融合 (Dead Zone)</n-h3>
              <p style="font-size: 15px; color: var(--n-text-color-3)">
                计算最终越界深度 (Depth)，根据驱动算法分发不同的物理界限惩罚：
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 16px;
                  border-radius: 8px;
                  font-family: monospace;
                  margin-bottom: 20px;
                  line-height: 1.8;
                  font-size: 15px;
                "
              >
                <span style="color: #ef4444; font-weight: bold"
                  >[GA / PSO] 阶跃断崖淘汰：</span
                ><br />
                触发任何死区即刻执行一票否决，无视单项得分，总分直接抹杀。<br />
                <br />
                <span style="color: #8b5cf6; font-weight: bold"
                  >[BO] C0 绝对连续平滑衰减：</span
                ><br />
                消除断崖，继承边界 Base Score，仅向下叠加线性深度惩罚：<br />
                Final_Score = Base_Score - (500.0 &times; Depth)
              </div>

              <n-h3>4. 综合结算与地形激活 (Terrain Activation)</n-h3>
              <p style="font-size: 15px; color: var(--n-text-color-3)">
                为激发贝叶斯优化中高斯过程 (GP)
                核函数的寻优积极性，人为拉开方差，防止微小梯度淹没于浮点噪声：
              </p>
              <div
                style="
                  background: var(--n-code-color);
                  padding: 20px;
                  border-radius: 8px;
                  font-family: monospace;
                  text-align: center;
                  font-size: 18px;
                  font-weight: bold;
                "
              >
                Total_Fitness = &sum;(Final_Scores) &times; 100.0 <br /><br />
                <span
                  style="color: #ef4444; font-size: 14px; font-weight: normal; display: inline-block; margin-top: 8px;"
                >
                  * 触发死区的 GA/PSO 个体，总分强制抹杀为 -10,000,000 (-1e7)
                </span>
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
  BrainCircuit,
  Cpu,
  Network,
} from "lucide-vue-next";
import axios from "axios";
import ScoreSandbox from "@/components/ScoreSandbox.vue";
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

const sysEnv = reactive({
  python: "检测中...",
  pytorch: "检测中...",
  cst: "检测中...",
});

//2. 定义拉取接口的函数
const fetchEnvInfo = async () => {
  try {
    const res = await axios.get(`${API_BASE}/env_info`);
    if (res.data.status === "success") {
      sysEnv.python = res.data.data.python;
      sysEnv.pytorch = res.data.data.pytorch;
      sysEnv.cst = res.data.data.cst;
    }
  } catch (e) {
    console.error("无法获取系统环境信息", e);
    sysEnv.python = "获取失败";
    sysEnv.pytorch = "获取失败";
    sysEnv.cst = "获取失败";
  }
};

const cpuColor = computed(() =>
  cpuUsage.value > 80 ? "#ef4444" : cpuUsage.value > 50 ? "#f59e0b" : "#10b981",
);
const ramColor = computed(() => (ramUsage.value > 85 ? "#ef4444" : "#3b82f6"));

let pollInterval = null;

const refreshSystemStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/health`);
    
    // 1. 只要这个接口没抛出异常（网络能通），说明 FastAPI 后台必定是活的
    apiStatus.value = "running";

    // 2. CST 探针：优先使用后端专门的探针结果，如果没有，借用环境检测的数据兜底
    if (res.data.cst_alive !== undefined) {
      cstStatus.value = res.data.cst_alive ? "running" : "error";
    } else {
      // 兜底：只要路径不是这几个失败词，就当它活着
      cstStatus.value = (sysEnv.cst && !["检测中...", "获取失败", "未安装"].includes(sysEnv.cst)) 
        ? "running" : "error";
    }

    // 3. Agents 探针：必须依靠后端去真实 Ping 它的端口
    if (res.data.agents_alive !== undefined) {
      agentsStatus.value = res.data.agents_alive ? "running" : "error";
    } else {
      agentsStatus.value = "error"; 
    }

  } catch (e) {
    // 接口彻底不通（FastAPI 挂了或断网），一损俱损全亮红灯
    apiStatus.value = "error";
    cstStatus.value = "error";
    agentsStatus.value = "error";
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
  { 
    title: "任务名称", 
    key: "name", 
    width: 170,
    render(row) {
      const typeMap = { 
        opt: { type: 'success', label: '联合优化' }, 
        sweep: { type: 'info', label: '网格扫参' }, 
        nn: { type: 'warning', label: '在线学习' } 
      };
      const t = typeMap[row.type] || { type: 'default', label: '未知' };
      
      return h('div', { style: 'display: flex; flex-direction: column; gap: 6px; align-items: flex-start;' }, [
        h('span', { style: 'font-weight: 600;' }, row.name),
        h(NTag, { size: 'tiny', type: t.type, bordered: false }, { default: () => t.label })
      ]);
    }
  },
  {
    title: "状态",
    key: "status",
    width: 90,
    render(row) {
      const typeMap = { running: "info", completed: "success", error: "error", stopped: "warning" };
      const textMap = { running: "运行中", completed: "已完成", error: "异常中断", stopped: "已停止" };
      return h(
        NTag,
        { type: typeMap[row.status] || "default", bordered: false, size: "small" },
        { default: () => textMap[row.status] || row.status },
      );
    },
  },
  {
    title: "总体进度 (Progress)",
    key: "progress",
    render(row) {
      if (row.status === "error") return h("span", { style: "color: #ef4444; font-size: 13px;" }, "异常中断");
      if (row.status === "stopped") return h("span", { style: "color: #f59e0b; font-size: 13px;" }, "手动终止");
      
      const pct = row.totalGen ? Math.round((row.currentGen / row.totalGen) * 100) : 0;
      return h(NProgress, {
        type: "line",
        percentage: pct > 100 ? 100 : pct,
        indicatorPlacement: "inside",
        processing: row.status === "running",
      });
    },
  },
  {
    title: "操作",
    key: "actions",
    width: 110,
    render(row) {
      return h(
        NButton,
        {
          size: "small",
          secondary: true,
          type: "primary",
          onClick: () => {
            message.info(`正在前往 ${row.name} 工作台...`);
            // ✨ 核心机制：智能路由分发
            if (row.type === 'sweep') goToPage("CstSweep");
            else if (row.type === 'nn') goToPage("NeuralNet");
            else goToPage("CstOpt");
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
    const res = await axios.get(`${API_BASE}/recent_tasks?task_type=all`);
    if (res.data.status === "success") {
      const hiddenTaskIds = JSON.parse(
        localStorage.getItem("zttt_hidden_tasks") || "[]",
      );
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
  fetchEnvInfo();

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

.custom-icon-box {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 72px;
  height: 72px;
  background: var(--n-action-color); 
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

.nav-card {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.nav-action {
  transition: color 0.3s ease;
}

.nav-card.sweep-card:hover {
  border-color: #3b82f6 !important;
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3) !important;
  transform: translateY(-4px); /* 悬浮时轻微上浮 */
}
.nav-card.sweep-card:hover .nav-action {
  color: #3b82f6;
}


.nav-card.cst-card:hover {
  border-color: #10b981 !important;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.cst-card:hover .nav-action {
  color: #10b981;
}


.nav-card.nn-card:hover {
  border-color: #8b5cf6 !important;
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.nn-card:hover .nav-action {
  color: #8b5cf6;
}

.nav-card.db-card:hover {
  border-color: #f59e0b !important;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.db-card:hover .nav-action {
  color: #f59e0b;
}

/* 文献助手专属卡片 hover 发光颜色 (粉红系) */
.nav-card.lit-card:hover {
  border-color: #ec4899 !important;
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3) !important;
  transform: translateY(-4px);
}
.nav-card.lit-card:hover .nav-action {
  color: #ec4899;
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
   FAQ 使用手册样式
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
.acrylic-drawer-dark {
  background-color: rgba(24, 24, 28, 0.6) !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.acrylic-drawer-light {
  background-color: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
}

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

.acrylic-drawer-dark .n-tabs-tab,
.acrylic-drawer-light .n-tabs-tab {
  background-color: transparent !important;
}
</style>
