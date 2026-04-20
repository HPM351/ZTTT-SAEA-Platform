<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider
      ><n-dialog-provider>
        <n-layout
          position="absolute"
          style="background-color: var(--n-color); user-select: none"
          @mousedown="handleMouseDown"
          @contextmenu.prevent="handleContextMenu"
        >
          <transition name="nav-fade">
            <n-layout-header
              v-if="!isHome"
              bordered
              class="global-header"
              :class="isDarkMode ? 'dark-header' : 'light-header'"
            >
              <div class="logo">ZTTT SAEA Platform</div>
              <div class="nav-center-wrapper">
                <div
                  class="nav-tabs-interactive-zone"
                  :class="{ 'is-global-running': isGlobalRunning }"
                  ref="navContainerRef"
                  :style="spotlightStyle"
                  @mousemove="handleSpotlightMouseMove"
                  @mouseleave="handleMouseLeave"
                >
                  <n-tabs
                    type="segment"
                    :value="activeKey"
                    @update:value="handleTabChange"
                    class="nav-tabs"
                  >
                    <n-tab-pane name="Home" tab="平台主页"></n-tab-pane>
                    <n-tab-pane name="CstSweep" tab="CST 联合扫参"></n-tab-pane>
                    <n-tab-pane name="CstOpt" tab="CST 联合优化"></n-tab-pane>
                    <n-tab-pane
                      name="NeuralNet"
                      tab="神经网络优化"
                    ></n-tab-pane>
                    <n-tab-pane name="DataCenter" tab="数据库管理"></n-tab-pane>
                  </n-tabs>
                </div>
              </div>
              <div class="header-actions">
                <n-switch v-model:value="isDarkMode" size="large">
                  <template #checked-icon>🌙</template>
                  <template #unchecked-icon>☀️</template>
                </n-switch>
              </div>
            </n-layout-header>
          </transition>

          <div class="island-wrapper">
            <transition name="island-drop">
              <div
                v-if="isGlobalRunning"
                class="dynamic-island"
                :class="{ 'is-expanded': isIslandExpanded }"
                @mouseenter="isIslandExpanded = true"
                @mouseleave="isIslandExpanded = false"
              >
                <div class="island-content-compact" v-show="!isIslandExpanded">
                  <div class="status-group">
                    <div class="task-indicator cst">⚙️</div>
                    <div class="pulse-dot"></div>
                  </div>
                  <span class="compact-text">SAEA 引擎处理中...</span>
                </div>

                <transition name="fade">
                  <div class="island-content-detailed" v-if="isIslandExpanded">
                    <div class="detail-header">实时任务监控</div>

                    <template
                      v-for="(state, routeKey) in islandState"
                      :key="routeKey"
                    >
                      <div
                        class="task-row dynamic-task-row"
                        v-if="state.isRunning"
                      >
                        <div class="task-info">
                          <template
                            v-if="
                              routeKey === 'CstSweep' || routeKey === 'CstOpt'
                            "
                          >
                            <span class="task-label"
                              >⚙️ {{ state.taskName || routeKey }}</span
                            >
                            <span class="task-subtext" :title="state.filePath"
                              >路径: {{ state.filePath }}</span
                            >
                            <n-progress
                              type="line"
                              :percentage="state.progress"
                              indicator-placement="inside"
                              processing
                              status="success"
                            />
                          </template>

                          <template v-if="routeKey === 'NeuralNet'">
                            <span class="task-label">
                              {{ state.modelName || "神经网络进程" }}</span
                            >
                            <span
                              class="task-subtext"
                              v-if="state.isOnlineLearning"
                              :title="state.filePath"
                              >微调路径: {{ state.filePath }}</span
                            >
                            <span class="task-subtext" v-else
                              >在线微调: 未启用</span
                            >
                            <n-progress
                              type="line"
                              :percentage="state.progress"
                              indicator-placement="inside"
                              processing
                              color="#3b82f6"
                            />
                          </template>
                        </div>
                        <n-button
                          size="tiny"
                          type="error"
                          quaternary
                          @click="state.abortFn && state.abortFn()"
                          >终止</n-button
                        >
                      </div>
                    </template>
                  </div>
                </transition>
              </div>
            </transition>
          </div>

          <n-layout-content
            class="global-content"
            :class="{ 'is-home': isHome }"
          >
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>

            <Teleport to="body">
              <transition name="radial-fade">
                <div
                  v-show="radialMenu.show"
                  class="radial-overlay"
                  :style="{
                    left: radialMenu.x + 'px',
                    top: radialMenu.y + 'px',
                  }"
                >
                  <div class="radial-circle">
                    <div
                      class="radial-slice slice-top"
                      :class="{ 'is-active': radialMenu.activeAction === 'ai' }"
                    >
                      <div class="slice-content">
                        <span class="radial-label">Agents智能体对话</span>
                      </div>
                    </div>

                    <div
                      class="radial-slice slice-right"
                      :class="{
                        'is-active': radialMenu.activeAction === 'docs',
                      }"
                    >
                      <div class="slice-content">
                        <span class="radial-label">查阅使用手册</span>
                      </div>
                    </div>

                    <div
                      class="radial-slice slice-bottom"
                      :class="{
                        'is-active': radialMenu.activeAction === 'theme',
                      }"
                    >
                      <div class="slice-content">
                        <span class="radial-label">主题切换</span>
                      </div>
                    </div>

                    <div
                      class="radial-slice slice-left"
                      :class="{
                        'is-active': radialMenu.activeAction === 'home',
                      }"
                    >
                      <div class="slice-content">
                        <span class="radial-label">返回主页</span>
                      </div>
                    </div>

                    <div class="radial-center-hole">
                      <div
                        class="center-dot"
                        :style="{
                          transform: radialMenu.activeAction
                            ? 'scale(1.5)'
                            : 'scale(1)',
                          transition: '0.2s',
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
              </transition>
            </Teleport>
          </n-layout-content>

          <FloatingChat />
        </n-layout> </n-dialog-provider
    ></n-message-provider>
  </n-config-provider>
</template>

<script setup>
import {
  ref,
  computed,
  watch,
  provide,
  reactive,
  onMounted,
  onUnmounted,
} from "vue";
import { useRoute, useRouter } from "vue-router";
import { darkTheme, createDiscreteApi } from "naive-ui";
import FloatingChat from "./components/FloatingChat.vue";

const route = useRoute();
const router = useRouter();

// ✨ 修复 1：将主题控制状态提升到顶部优先初始化
const isDarkMode = ref(true);
provide("globalTheme", isDarkMode);
const theme = computed(() => (isDarkMode.value ? darkTheme : null));
watch(
  isDarkMode,
  (isDark) => {
    if (isDark) {
      document.body.classList.add("dark-mode");
      document.body.classList.remove("light-mode");
    } else {
      document.body.classList.add("light-mode");
      document.body.classList.remove("dark-mode");
    }
  },
  { immediate: true },
);

const themeOverrides = computed(() => {
  // 定义统一的高级亚克力半透明背景色
  const acrylicBg = isDarkMode.value
    ? "rgba(30, 30, 34, 0.65)"
    : "rgba(255, 255, 255, 0.75)";

  return {
    common: {
      primaryColor: "#10b981",
      primaryColorHover: "#059669",
      borderRadius: "12px",
    },
    Message: {
      color: acrylicBg,
      colorInfo: acrylicBg,
      colorSuccess: acrylicBg,
      colorWarning: acrylicBg,
      colorError: acrylicBg,
      colorLoading: acrylicBg,
      boxShadow: isDarkMode.value
        ? "0 8px 32px rgba(0, 0, 0, 0.4)"
        : "0 8px 32px rgba(0, 0, 0, 0.2)",
    },
    Dialog: {
      color: acrylicBg,
    },
  };
});

// ✨ 修复 2：将当前的主题和覆盖样式包装为 ProviderProps
const configProviderPropsRef = computed(() => ({
  theme: theme.value,
  themeOverrides: themeOverrides.value,
}));

// ✨ 修复 3：将响应式配置传给脱离文档流的 DiscreteApi
const { message } = createDiscreteApi(["message"], {
  configProviderProps: configProviderPropsRef,
});

// 全局状态控制 (沿用之前的修复)
const isChatVisible = ref(false);
const isDocsVisible = ref(false);
provide("isChatVisible", isChatVisible);
provide("globalDocsVisible", isDocsVisible);
const islandState = reactive({
  CstSweep: {
    isRunning: false,
    taskName: "",
    filePath: "",
    progress: 0,
    abortFn: null,
  },
  CstOpt: {
    isRunning: false,
    taskName: "",
    filePath: "",
    progress: 0,
    abortFn: null,
  },
  NeuralNet: {
    isRunning: false,
    modelName: "",
    progress: 0,
    isOnlineLearning: false,
    filePath: "",
    abortFn: null,
  },
});
provide("islandState", islandState);

// 兼容旧逻辑，只要有一个在跑，导航栏就亮灯
const isGlobalRunning = computed(() => {
  return Object.values(islandState).some((state) => state.isRunning);
});
provide("isGlobalRunning", isGlobalRunning);
const isIslandExpanded = ref(false); // 控制岛屿是否展开
const radialMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  activeAction: null, // 记录当前鼠标角度命中的功能
});

// 1. 鼠标右键按下：记录圆心坐标，展开轮盘，开始监听拖拽
const handleMouseDown = (e) => {
  if (e.button === 2) {
    // 2 代表鼠标右键
    e.preventDefault();
    radialMenu.x = e.clientX;
    radialMenu.y = e.clientY;
    radialMenu.show = true;
    radialMenu.activeAction = null;

    // 开启全局鼠标监听
    window.addEventListener("mousemove", handleRadialMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  }
};

// 2. 屏蔽原生的右键菜单弹出
const handleContextMenu = (e) => {
  e.preventDefault();
};
// 3. 鼠标拖拽中：利用三角函数计算滑动角度与距离
const handleRadialMouseMove = (e) => {
  if (!radialMenu.show) return;

  const dx = e.clientX - radialMenu.x;
  const dy = e.clientY - radialMenu.y;
  const distance = Math.sqrt(dx * dx + dy * dy);

  // 死区设定：如果拖拽距离小于 40px，认为是中心挖空区，不触发任何功能
  if (distance < 40) {
    radialMenu.activeAction = null;
    return;
  }

  // 计算角度：将 atan2 的弧度转换为 0-360 度的角度
  let angle = Math.atan2(dy, dx) * (180 / Math.PI);
  if (angle < 0) angle += 360;

  // 划定 4 个扇形的触发角度范围 (每个扇形 90 度)
  if (angle >= 315 || angle < 45) {
    radialMenu.activeAction = "docs"; // 右
  } else if (angle >= 45 && angle < 135) {
    radialMenu.activeAction = "theme"; // 下
  } else if (angle >= 135 && angle < 225) {
    radialMenu.activeAction = "home"; // 左
  } else if (angle >= 225 && angle < 315) {
    radialMenu.activeAction = "ai"; // 上
  }
};

// 4. 鼠标右键松开：执行高亮的功能并关闭轮盘
const handleMouseUp = (e) => {
  if (e.button === 2 && radialMenu.show) {
    if (radialMenu.activeAction) {
      triggerRadialAction(radialMenu.activeAction);
    }
    closeRadialMenu();
  }
};

const closeRadialMenu = () => {
  radialMenu.show = false;
  radialMenu.activeAction = null;
  // 销毁监听，节约性能（补上缺失的 e）
  window.removeEventListener("mousemove", handleRadialMouseMove);
  window.removeEventListener("mouseup", handleMouseUp);
};

onMounted(() => {
  window.addEventListener("click", closeRadialMenu);
  // ✨ 新增：在全局 Window 级别死死拦截原生的右键菜单
  window.addEventListener("contextmenu", handleContextMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeRadialMenu);
  // ✨ 新增：组件卸载时移除拦截
  window.removeEventListener("contextmenu", handleContextMenu);
});
// 轮盘按钮具体的点击动作
const triggerRadialAction = (action) => {
  switch (action) {
    case "ai":
      // ✨ 唤醒/休眠 AI
      isChatVisible.value = !isChatVisible.value;
      message.success(
        isChatVisible.value ? "已唤醒 Agents 智能体" : "Agents 智能体已休眠",
      );
      break;
    case "docs":
      // ✨ 自动跳转主页并打开手册 Drawer
      isDocsVisible.value = true;
      if (!isHome.value) {
        router.push({ name: "Home" });
      }
      message.success("正在查阅平台使用手册...");
      break;
    case "theme":
      isDarkMode.value = !isDarkMode.value;
      message.success(`已切换至${isDarkMode.value ? "深色" : "浅色"}模式`);
      break;
    case "home":
      router.push({ name: "Home" });
      break;
  }
};
// 实际开发中，你可以通过 inject 获取这两个状态，这里先做逻辑占位
const isCstTaskRunning = computed(() => isGlobalRunning.value); // 示例逻辑
const isNnTaskRunning = ref(false); // 示例逻辑
// ✨ 新增：高光随动 (Spotlight) 核心计算逻辑
const navContainerRef = ref(null);
const mouseX = ref(-100);
const mouseY = ref(-100);
const isOutside = ref(true);

const handleSpotlightMouseMove = (e) => {
  if (!navContainerRef.value) return;
  const rect = navContainerRef.value.getBoundingClientRect();
  mouseX.value = e.clientX - rect.left;
  mouseY.value = e.clientY - rect.top;
  isOutside.value = false;
};
const handleMouseLeave = () => {
  isOutside.value = true;
};
const spotlightStyle = computed(() => ({
  "--x": `${mouseX.value}px`,
  "--y": `${mouseY.value}px`,
  "--opacity": isOutside.value ? 0 : 1,
}));

// 🌟 动态判断当前是否为首页（通过路径或路由名称）
const isHome = computed(() => {
  return (
    route.path === "/" ||
    route.path === "/home" ||
    route.name === "Home" ||
    route.name === "home"
  );
});

// 导航菜单配置
const activeKey = ref("Home");
const handleTabChange = (name) => {
  activeKey.value = name;
  router.push({ name: name });
};

// 监听路由变化，同步高亮菜单
watch(
  () => route.path,
  (newPath) => {
    const pathLower = newPath.toLowerCase();

    // 增加对扫参路由的匹配
    if (pathLower.includes("sweep")) {
      activeKey.value = "CstSweep";
    }
    // 匹配优化路由
    else if (pathLower.includes("opt") || pathLower.includes("cst")) {
      activeKey.value = "CstOpt";
    }
    // 匹配神经网络
    else if (pathLower.includes("nn") || pathLower.includes("neuralnet")) {
      activeKey.value = "NeuralNet";
    }
    // 匹配数据库管理
    else if (pathLower.includes("data")) {
      activeKey.value = "DataCenter";
    }
    // 兜底返回主页
    else {
      activeKey.value = "Home";
    }
  },
  { immediate: true },
);
</script>

<style scoped>
/* ===== 导航栏样式 ===== */
.global-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  height: 60px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.05) !important;
}

.dynamic-task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* 给任务之间留出呼吸感 */
  padding-bottom: 10px;
}

/* ✨ 核心魔法：选中除了最后一个之外的所有任务行，加上底部分割线 */
.dynamic-task-row:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 10px;
}

/* 最后一个任务行不需要底部内边距，防止撑破灵动岛 */
.dynamic-task-row:last-child {
  padding-bottom: 0;
}

/* ✨ 1. Logo 渐变科技字体 */
.logo {
  font-size: 20px;
  font-weight: 900;
  letter-spacing: 1px;
  white-space: nowrap;
  flex-shrink: 0;
  font-family:
    "Montserrat",
    "SF Pro Display",
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    Roboto,
    sans-serif;
  background: linear-gradient(90deg, #10b981, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ✨ 2. 导航绝对居中与自适应宽度 */
.nav-center-wrapper {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.nav-tabs {
  width: auto;
  min-width: 560px; /* 保证胶囊不被压扁 */
}

/* ✨ 3. 轨道背景与内边距 (解决拥挤) */
.nav-tabs :deep(.n-tabs-rail) {
  border-radius: 14px;
  padding: 6px !important; /* 强制撑开上下左右，留出呼吸感 */
  transition: all 0.3s;
  overflow: visible !important;
}
.dark-header .nav-tabs :deep(.n-tabs-rail) {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.3);
}
.light-header .nav-tabs :deep(.n-tabs-rail) {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.05);
}

/* ✨ 4. 滑块 (Active Pill) 弹簧物理效果 */
.nav-tabs :deep(.n-tabs-capsule) {
  border-radius: 10px !important;
  transition: all 0.5s cubic-bezier(0.32, 1.15, 0.38, 1) !important;
  background: #10b981 !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5) !important;
  border: none !important;
}

/* ✨ 5. 灵动岛呼吸灯效果 */
.is-global-running :deep(.n-tabs-capsule)::after {
  content: "";
  position: absolute;
  top: -6px;
  right: -6px;
  width: 14px;
  height: 14px;
  background: #10b981;
  border-radius: 50%;
  border: 2px solid v-bind('isDarkMode ? "#18181c" : "#fff"');
  box-shadow: 0 0 16px #10b981;
  animation: island-pulse 1.2s infinite ease-in-out;
  z-index: 100;
}

@keyframes island-pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
    box-shadow: 0 0 18px #10b981;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
}

/* ✨ 6. 字体微调与层级保护 (解决文字挤压) */
.nav-tabs :deep(.n-tabs-tab) {
  padding: 6px 20px !important; /* 强制拉开文字左右间距，解决文字连在一起的问题 */
  font-weight: bold;
  letter-spacing: 0.5px;
  z-index: 2;
  transition: color 0.3s;
}
.nav-tabs :deep(.n-tabs-tab--active) {
  color: #ffffff !important;
}

/* ===== 页面内容区域适配 ===== */
.global-content {
  padding-top: 60px;
  height: 100vh;
  box-sizing: border-box;
  transition: padding-top 0.4s ease;
}
.global-content.is-home {
  padding-top: 0;
}

/* ===== 动画 ===== */
.nav-fade-enter-active,
.nav-fade-leave-active {
  transition:
    opacity 0.4s ease,
    transform 0.4s ease;
}
.nav-fade-enter-from,
.nav-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.fade-enter-active,
.fade-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>

<style>
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* 适配火狐 */
* {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}

.n-message,
.n-dialog {
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

/* 提升大弹窗的阴影层级，增加悬浮感 */
.n-dialog {
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3) !important;
}

.island-wrapper {
  position: fixed;
  top: 45px; /* 悬浮在 Header 区域或稍微靠下 */
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999; /* 确保在所有内容之上 */
  pointer-events: none; /* 防止包裹层遮挡下方点击 */
}

.dynamic-island {
  pointer-events: auto; /* 恢复岛屿本身的交互 */
  background: v-bind(
    'isDarkMode ? "rgba(0, 0, 0, 0.4)" : "rgba(255, 255, 255, 0.4)"'
  );
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 22px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);

  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: hidden;

  /* 弹性动画核心 */
  min-width: 180px;
  height: 36px;
  transition: all 0.6s cubic-bezier(0.32, 1.15, 0.38, 1);
}

/* 展开态的高宽变化 */
.dynamic-island.is-expanded {
  min-width: 280px;
  height: auto; /* ✨ 让内容自动撑开高度 */
  min-height: 110px; /* ✨ 保持基础高度不变 */
  padding: 16px;
  border-radius: 20px;
}

/* 压缩态内部样式 */
.island-content-compact {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 36px;
  padding: 0 16px;
}

.status-group {
  position: relative;
  display: flex;
  align-items: center;
}
.pulse-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: island-pulse 1.5s infinite;
}

.compact-text {
  font-size: 12px;
  font-weight: bold;
  opacity: 0.8;
}

/* 展开态内部样式 */
.island-content-detailed {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-header {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  opacity: 0.5;
  font-weight: bold;
  margin-bottom: 4px;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.task-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.task-label {
  font-size: 13px;
  font-weight: 600;
}

/* 岛屿进入动画：从顶部滑落 */
.island-drop-enter-active,
.island-drop-leave-active {
  transition: all 0.6s cubic-bezier(0.32, 1.15, 0.38, 1);
}
.island-drop-enter-from,
.island-drop-leave-to {
  opacity: 0;
  transform: translateY(-50px) scale(0.8);
}

.task-subtext {
  font-size: 10px;
  opacity: 0.6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

/* ✨ 右键径向轮盘 (四等分甜甜圈版) */
.radial-overlay {
  position: fixed;
  z-index: 99999;
  width: 0;
  height: 0;
}

/* 圆盘总容器 */
.radial-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 240px;
  height: 240px;
  margin-left: -120px;
  margin-top: -120px;
  border-radius: 50%;
  overflow: hidden;
  /* ✨ 核心魔法：旋转 45 度，让内部的四个正方形变成上下左右的扇形 */
  transform: rotate(45deg);

  background: v-bind(
    'isDarkMode ? "rgba(30, 30, 34, 0.5)" : "rgba(255, 255, 255, 0.6)"'
  );
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

/* 4 个扇形区块 */
.radial-slice {
  position: absolute;
  width: 50%;
  height: 50%;
  background: transparent;
  transition: background 0.2s;
  cursor: pointer;
  box-sizing: border-box;
}

/* 扇形定位与极细的内部十字分割线 */
.slice-top {
  top: 0;
  left: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.slice-right {
  top: 0;
  right: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.slice-bottom {
  bottom: 0;
  right: 0;
  border-left: 1px solid rgba(255, 255, 255, 0.08);
}
.slice-left {
  bottom: 0;
  left: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* 悬停高亮为主题色 */
.radial-slice.is-active {
  background: rgba(16, 185, 129, 0.75);
}

/* 扇形内部内容：必须反向旋转 -45 度，否则字是歪的 */
.slice-content {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  transform: rotate(-45deg);
  color: var(--n-text-color);
}

/* 内容交互动效 */
.radial-icon {
  font-size: 24px;
  margin-bottom: 4px;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.radial-slice.is-active .radial-icon {
  transform: scale(1.3);
}
.radial-label {
  font-size: 12px;
  font-weight: bold;
  opacity: 0.9;
}

/* 中心防误触死区 (甜甜圈的孔) */
.radial-center-hole {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 64px;
  height: 64px;
  margin-left: -32px;
  margin-top: -32px;
  border-radius: 50%;
  /* 动态获取网页底色 */
  background: var(--n-color);
  box-shadow:
    inset 0 4px 12px rgba(0, 0, 0, 0.3),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  pointer-events: none; /* 穿透点击，防止死区拦截事件 */
  display: flex;
  justify-content: center;
  align-items: center;
  /* 反向旋转，保持内部元素水平 */
  transform: rotate(-45deg);
}
.center-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 12px #10b981;
}

/* 🚀 物理弹簧缩放动画 */
.radial-fade-enter-active,
.radial-fade-leave-active {
  transition: opacity 0.2s ease;
}
.radial-fade-enter-active .radial-circle,
.radial-fade-leave-active .radial-circle {
  transition:
    transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
    opacity 0.2s;
}
.radial-fade-enter-from .radial-circle,
.radial-fade-leave-to .radial-circle {
  transform: rotate(45deg) scale(0.4);
  opacity: 0;
}
</style>
