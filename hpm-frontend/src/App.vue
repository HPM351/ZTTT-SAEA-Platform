<template>
  <n-config-provider :theme="theme" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider :container-style="{ paddingTop: isHome ? '0' : '68px' }">
      ><n-dialog-provider>
        <n-layout
          position="absolute"
          style="background-color: var(--n-color); user-select: none"
          @mousedown="handleMouseDown"
          @contextmenu.prevent="handleContextMenu"
        >
          <transition name="nav-fade">
<!-- ================= 模块 1: 全局顶部导航栏 (Logo/发光Pill导航/主题切换) ================= -->
            <n-layout-header
              v-if="!isHome"
              bordered
              class="global-header"
              :class="isDarkMode ? 'dark-header' : 'light-header'"
            >
              <div class="logo">ZTTT SAEA Platform</div>
              <div class="nav-pills">
                <div
                  v-for="pill in navPills"
                  :key="pill.key"
                  class="nav-pill"
                  :class="{ 'is-active': activeKey === pill.key }"
                  :style="activeKey === pill.key ? { '--pill-glow': pill.glow } : {}"
                  @click="navigateTo(pill.key)"
                >
                  <n-icon :size="16"><component :is="pill.icon" /></n-icon>
                  <span class="pill-label">{{ pill.label }}</span>
                  <span v-if="pill.hasPulse && islandState[pill.key]?.isRunning" class="pill-pulse-dot"></span>
                </div>
              </div>
              <div class="header-island">
                <transition name="island-fade">
                  <div
                    v-if="isGlobalRunning"
                    class="dynamic-island"
                    :class="{ 'is-expanded': isIslandExpanded }"
                    @mouseenter="isIslandExpanded = true"
                    @mouseleave="isIslandExpanded = false"
                  >
                    <div class="island-content-compact" v-show="!isIslandExpanded">
                      <div class="status-group">
                        <span class="task-indicator">⚙️</span>
                        <span class="pulse-dot"></span>
                      </div>
                      <span class="compact-text">SAEA 引擎处理中...</span>
                    </div>
                    <div class="island-content-detailed" v-if="isIslandExpanded">
                      <div class="detail-header">实时任务监控</div>
                      <template v-for="(state, routeKey) in islandState" :key="routeKey">
                        <div class="task-row dynamic-task-row" v-if="state.isRunning">
                          <div class="task-info">
                            <template v-if="routeKey === 'CstSweep' || routeKey === 'CstOpt'">
                              <span class="task-label">⚙️ {{ state.taskName || routeKey }}</span>
                              <span class="task-subtext" :title="state.filePath">路径: {{ state.filePath }}</span>
                              <n-progress type="line" :percentage="state.progress" indicator-placement="inside" processing status="success" />
                            </template>
                            <template v-if="routeKey === 'NeuralNet'">
                              <span class="task-label">{{ state.modelName || "神经网络进程" }}</span>
                              <span class="task-subtext" v-if="state.isOnlineLearning" :title="state.filePath">微调路径: {{ state.filePath }}</span>
                              <span class="task-subtext" v-else>在线微调: 未启用</span>
                              <n-progress type="line" :percentage="state.progress" indicator-placement="inside" processing color="#3b82f6" />
                            </template>
                          </div>
                          <n-button size="tiny" type="error" quaternary @click="state.abortFn && state.abortFn()">终止</n-button>
                        </div>
                      </template>
                    </div>
                  </div>
                </transition>
              </div>
              <div class="header-actions">
                <n-switch v-model:value="isDarkMode" size="large">
                  <template #checked-icon>🌙</template>
                  <template #unchecked-icon>☀️</template>
                </n-switch>
              </div>
            </n-layout-header>
          </transition>

          <n-layout-content
            class="global-content"
            :class="{ 'is-home': isHome }"
          >
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
<!-- ================= 模块 3: 鼠标右键径向菜单 (Radial Menu) ================= -->
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
import {
  Grid3X3,
  Cpu,
  BrainCircuit,
  BookOpen,
  Database,
  Home,
} from "lucide-vue-next";
import FloatingChat from "./components/FloatingChat.vue";

const route = useRoute();
const router = useRouter();

// ================= 模块 1: 主题配置与 UI 引擎 (Naive UI Provider) =================
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

// 导航药丸配置: 扩展路由只需在此数组追加一项
const navPills = [
  { key: "Home", label: "主页", icon: Home, glow: "rgba(156,163,175,0.4)", hasPulse: false },
  { key: "CstSweep", label: "联合扫参", icon: Grid3X3, glow: "rgba(59,130,246,0.5)", hasPulse: true },
  { key: "CstOpt", label: "联合优化", icon: Cpu, glow: "rgba(34,168,122,0.5)", hasPulse: true },
  { key: "NeuralNet", label: "神经网络", icon: BrainCircuit, glow: "rgba(139,92,246,0.5)", hasPulse: true },
  { key: "LiteratureAssistant", label: "文献助手", icon: BookOpen, glow: "rgba(236,72,153,0.5)", hasPulse: false },
  { key: "DataCenter", label: "数据库", icon: Database, glow: "rgba(245,158,11,0.5)", hasPulse: false },
];

const themeOverrides = computed(() => {
  const acrylicBg = isDarkMode.value
    ? "rgba(30, 30, 34, 0.65)"
    : "rgba(255, 255, 255, 0.75)";

  return {
    common: {
      primaryColor: "#22a87a",
      primaryColorHover: "#1a8a62",
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


const configProviderPropsRef = computed(() => ({
  theme: theme.value,
  themeOverrides: themeOverrides.value,
}));


const { message } = createDiscreteApi(["message"], {
  configProviderProps: configProviderPropsRef,
});


const isChatVisible = ref(false);
const isDocsVisible = ref(false);
provide("isChatVisible", isChatVisible);
provide("globalDocsVisible", isDocsVisible);
// ================= 模块 2: 全局状态注入与灵动岛数据核心 =================
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
// ================= 模块 3: 鼠标右键轮盘交互算法与事件拦截 =================
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
  // 在全局 Window 级别拦截原生的右键菜单
  window.addEventListener("contextmenu", handleContextMenu);
});

onUnmounted(() => {
  window.removeEventListener("click", closeRadialMenu);
  // 组件卸载时移除拦截
  window.removeEventListener("contextmenu", handleContextMenu);
});
// 轮盘按钮具体的点击动作
const triggerRadialAction = (action) => {
  switch (action) {
    case "ai":
      isChatVisible.value = !isChatVisible.value;
      message.success(
        isChatVisible.value ? "已唤醒 Agents 智能体" : "Agents 智能体已休眠",
      );
      break;
    case "docs":
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

// 导航跳转
const isHome = computed(() => {
  return (
    route.path === "/" ||
    route.path === "/home" ||
    route.name === "Home" ||
    route.name === "home"
  );
});

const activeKey = ref("Home");
const navigateTo = (name) => {
  activeKey.value = name;
  router.push({ name });
};

// 路由变化时同步激活态
watch(
  () => route.name,
  (name) => {
    activeKey.value = name || "Home";
  },
  { immediate: true },
);
</script>

<style scoped>
/* ===== 导航栏框架 ===== */
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
  background: linear-gradient(90deg, #22a87a, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ===== 发光 Pill 导航 ===== */
.nav-pills {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 20px;
  border-radius: 22px;
  cursor: pointer;
  position: relative;
  user-select: none;

  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    color 0.25s ease,
    transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1),
    box-shadow 0.35s ease;
}

/* ---- 暗色主题: 暗底 pill, 融入导航栏色系 ---- */
.dark-header .nav-pill {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.45);
}
.dark-header .nav-pill:hover {
  background: rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.75);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}
.dark-header .nav-pill.is-active {
  background: rgba(0, 0, 0, 0.55);
  border-color: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  transform: scale(1.05);
  box-shadow:
    0 0 22px var(--pill-glow, rgba(34, 168, 122, 0.5)),
    0 4px 20px rgba(0, 0, 0, 0.35);
}

/* ---- 亮色主题: 亮底 pill, 干净 ---- */
.light-header .nav-pill {
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(0, 0, 0, 0.06);
  color: rgba(0, 0, 0, 0.45);
}
.light-header .nav-pill:hover {
  background: rgba(255, 255, 255, 0.78);
  border-color: rgba(0, 0, 0, 0.14);
  color: rgba(0, 0, 0, 0.72);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}
.light-header .nav-pill.is-active {
  background: rgba(255, 255, 255, 0.95);
  border-color: rgba(0, 0, 0, 0.15);
  color: #111111;
  transform: scale(1.05);
  box-shadow:
    0 0 22px var(--pill-glow, rgba(34, 168, 122, 0.4)),
    0 4px 20px rgba(0, 0, 0, 0.1);
}

.pill-label {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  white-space: nowrap;
}

/* ===== 运行态呼吸脉冲点 ===== */
.pill-pulse-dot {
  position: absolute;
  top: 0;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #22a87a;
  border-radius: 50%;
  border: 1.5px solid v-bind('isDarkMode ? "#18181c" : "#fff"');
  box-shadow: 0 0 10px #22a87a;
  animation: pill-pulse 1.2s infinite ease-in-out;
  z-index: 10;
}

@keyframes pill-pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
    box-shadow: 0 0 14px #22a87a;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
}

@keyframes island-pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
    box-shadow: 0 0 16px #22a87a;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
}

/* 灵动岛内部任务行 */
.dynamic-task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 10px;
}
.dynamic-task-row:not(:last-child) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 10px;
}
.dynamic-task-row:last-child {
  padding-bottom: 0;
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


* {
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.15) transparent;
}

.n-message-container {
  pointer-events: none !important;
}
.n-message,
.n-dialog {
  pointer-events: auto !important;
  backdrop-filter: blur(20px) saturate(180%) !important;
  -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
}

/* 提升大弹窗的阴影层级，增加悬浮感 */
.n-dialog {
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.3) !important;
}

.header-island {
  position: relative;
  flex-shrink: 0;
  z-index: 100;
}

.dynamic-island {
  cursor: pointer;
  background: v-bind(
    'isDarkMode ? "rgba(0, 0, 0, 0.45)" : "rgba(255, 255, 255, 0.5)"'
  );
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 22px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);

  display: flex;
  flex-direction: column;
  align-items: center;
  overflow: visible;

  height: 36px;
  min-width: 180px;
  transition: all 0.6s cubic-bezier(0.32, 1.15, 0.38, 1);
}

/* 展开: 面板从下方弹出 */
.dynamic-island.is-expanded {
  overflow: visible;
}

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
.task-indicator {
  font-size: 14px;
}
.pulse-dot {
  position: absolute;
  top: -2px;
  right: -4px;
  width: 6px;
  height: 6px;
  background: #22a87a;
  border-radius: 50%;
  animation: island-pulse 1.5s infinite;
}

.compact-text {
  font-size: 12px;
  font-weight: bold;
  opacity: 0.8;
  white-space: nowrap;
}

/* 展开面板: 绝对定位下沉到导航栏下方 */
.island-content-detailed {
  position: absolute;
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  width: 300px;
  padding: 16px;
  border-radius: 16px;

  background: v-bind(
    'isDarkMode ? "rgba(0, 0, 0, 0.5)" : "rgba(255, 255, 255, 0.55)"'
  );
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);

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

/* 岛屿显隐动画 */
.island-fade-enter-active,
.island-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.32, 1.15, 0.38, 1);
}
.island-fade-enter-from,
.island-fade-leave-to {
  opacity: 0;
  transform: scale(0.85);
}

.task-subtext {
  font-size: 10px;
  opacity: 0.6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}


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
