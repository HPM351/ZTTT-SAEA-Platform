<template>
  <div class="saea-feature-page">
    <!-- 左侧:功能侧边栏 -->
    <div class="feature-sidebar">
      <div class="sidebar-header">
        <span class="title">教研室文献助手</span>
        <n-button
          secondary
          type="info"
          size="small"
          block
          @click="createNewChat"
        >
          <template #icon>
            <n-icon><Plus /></n-icon>
          </template>
          新建研讨
        </n-button>
      </div>

      <n-scrollbar
        class="history-list"
        style="padding: 0"
        content-style="padding: 12px; box-sizing: border-box;"
      >
        <div
          v-for="chat in chatHistories"
          :key="chat.id"
          class="history-item"
          :class="{ 'is-active': chat.id === currentChatId }"
          @click="selectChat(chat.id)"
          style="display: flex; align-items: center; gap: 8px"
        >
          <n-icon size="16" style="opacity: 0.7"><MessageSquare /></n-icon>

          <!-- 内联编辑模式 -->
          <div v-if="editingChatId === chat.id" style="flex: 1; display: flex">
            <n-input
              ref="editInputRef"
              v-model:value="editingTitle"
              size="tiny"
              @blur="saveChatTitle(chat)"
              @keyup.enter="saveChatTitle(chat)"
              @click.stop
            />
          </div>
          <!-- 正常显示模式 -->
          <span
            v-else
            class="history-title"
            style="
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            "
          >
            {{ chat.title }}
          </span>

          <!-- 操作按钮组 -->
          <div
            class="chat-actions"
            style="display: flex; gap: 6px; opacity: 0.5"
          >
            <n-icon
              class="action-icon"
              size="14"
              style="cursor: pointer"
              @click.stop="startEditChat(chat)"
            >
              <Pen />
            </n-icon>
            <n-icon
              class="action-icon"
              size="14"
              style="cursor: pointer"
              @click.stop="deleteChat(chat.id)"
            >
              <Trash2 />
            </n-icon>
          </div>
        </div>
      </n-scrollbar>
    </div>

    <!-- ================= 身份认证弹窗 (JWT 登录屏障) ================= -->
    <n-modal
      v-model:show="showLoginModal"
      :mask-closable="false"
      :closable="false"
    >
      <n-card
        style="
          width: 400px;
          border-radius: 12px;
          background: var(--n-card-color);
        "
        :title="isLoginMode ? '教研室身份认证 - 登录' : '教研室账号注册'"
        :bordered="false"
        size="huge"
        role="dialog"
        aria-modal="true"
      >
        <p
          style="
            color: var(--n-text-color-3);
            margin-bottom: 24px;
            margin-top: -12px;
            font-size: 13px;
          "
        >
          {{
            isLoginMode
              ? "请输入您的专属通行证,您的历史研讨记录将被加密隔离保存。"
              : "请设置您的专属账号与通行密钥。"
          }}
        </p>
        <n-form>
          <n-form-item label="研究员账号 (字母数字均可)">
            <n-input
              v-model:value="authForm.username"
              placeholder="例如: 2024001"
            />
          </n-form-item>
          <n-form-item label="通行密钥 (Password)">
            <n-input
              v-model:value="authForm.password"
              type="password"
              show-password-on="click"
              placeholder="请输入密码"
              @keyup.enter="handleAuth"
            />
          </n-form-item>

          <n-button
            type="primary"
            block
            size="large"
            :loading="isAuthenticating"
            @click="handleAuth"
            style="margin-top: 12px; border-radius: 8px"
          >
            {{ isLoginMode ? "登录并进入系统" : "注册并进入系统" }}
          </n-button>

          <!-- 模式切换按钮 -->
          <div style="text-align: center; margin-top: 16px">
            <n-button
              quaternary
              type="info"
              size="small"
              @click="toggleAuthMode"
              :disabled="isAuthenticating"
            >
              {{
                isLoginMode
                  ? "没有账号?点击注册新账号"
                  : "已有账号?点击返回登录"
              }}
            </n-button>
          </div>
        </n-form>
      </n-card>
    </n-modal>

    <!-- 右侧:主工作区 -->
    <div class="feature-main">
      <!-- 顶部配置面板 (极简状态) -->
      <div class="main-header" style="justify-content: space-between">
        <div class="header-left">
          <n-tag type="info" size="small" bordered>DeepSeek V4.0 Flash</n-tag>
        </div>

        <!-- 新增:右侧用户头像与控制台 -->
        <div
          class="header-right"
          style="display: flex; align-items: center; gap: 12px"
        >
          <span
            style="
              font-size: 13px;
              color: var(--n-text-color-3);
              font-weight: bold;
            "
          >
            {{ currentUser }}
          </span>
          <n-dropdown :options="userMenuOptions" @select="handleUserMenu">
            <n-avatar
              round
              size="medium"
              style="
                cursor: pointer;
                background-color: #3b82f6;
                color: white;
                font-weight: bold;
                border: 2px solid rgba(59, 130, 246, 0.3);
              "
            >
              {{ currentUser ? currentUser.charAt(0).toUpperCase() : "U" }}
            </n-avatar>
          </n-dropdown>

          <!-- 附件管理面板开关 -->
          <n-badge
            :value="currentChatFiles.length"
            :max="99"
            :show="currentChatFiles.length > 0"
            style="cursor: pointer"
          >
            <n-button
              quaternary
              circle
              size="small"
              @click="showFilePanel = !showFilePanel"
              :type="showFilePanel ? 'info' : 'default'"
            >
              <template #icon>
                <n-icon size="18"><Paperclip /></n-icon>
              </template>
            </n-button>
          </n-badge>
        </div>
      </div>

      <!-- 聊天内容流 -->
      <n-scrollbar
        class="message-area"
        ref="scrollbarRef"
        content-style="padding: 24px 0; box-sizing: border-box; overflow-x: hidden;"
      >
        <!-- 将 v-for 循环生成的对话框,严格包裹在这个 900px 的中央容器内 -->
        <div
          style="
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            padding: 0 24px;
            box-sizing: border-box;
          "
        >
          <div
            v-for="(msg, index) in currentMessages"
            :key="index"
            :class="['message-item', msg.role]"
            style="width: 100%"
          >
            <div class="message-content-wrapper">
              <!-- Gemini 风格的身份标识头 -->
              <div
                style="
                  display: flex;
                  align-items: center;
                  gap: 6px;
                  margin-bottom: 6px;
                  font-size: 13px;
                  color: var(--n-text-color-3);
                "
              >
                <n-icon v-if="msg.role === 'ai'" size="16" color="#3b82f6"
                  ><Sparkles
                /></n-icon>
                <n-icon v-else size="16"><User /></n-icon>
                <span>{{ msg.role === "ai" ? "DeepSeek" : currentUser }}</span>
              </div>

              <!-- 流式输出时,如果内容为空且处于 loading 状态,显示闪烁光标 -->
              <div class="bubble">
                <span
                  v-if="msg.content === '' && isLoading"
                  class="typing-cursor"
                  >█</span
                >
                <!-- 🔴 修改:换成 div 并加上 md-render-box 类名 -->
                <div
                  v-else
                  class="md-render-box"
                  v-html="formatMessage(msg.content)"
                ></div>
              </div>

              <!-- 带图标的操作栏 -->
              <div class="msg-actions" v-if="msg.content">
                <span
                  @click="copyMessage(msg.content)"
                  style="display: inline-flex; align-items: center; gap: 4px"
                >
                  <n-icon><Copy /></n-icon> 复制
                </span>
                <span
                  @click="deleteSingleMessage(index)"
                  style="display: inline-flex; align-items: center; gap: 4px"
                >
                  <n-icon><Trash2 /></n-icon> 删除
                </span>
              </div>
            </div>
          </div>
        </div>
      </n-scrollbar>

      <!-- 底部输入控制台 -->
      <!-- 底部输入控制台 -->
      <div class="input-console">
        <div
          class="input-wrapper"
          :class="{ 'is-dragging': isDragging }"
          @dragover.prevent="onDragOver"
          @dragleave.prevent="onDragLeave"
          @drop.prevent="onDrop"
        >
          <!-- 附件预览区 -->
          <div class="attachments-preview" v-if="pendingFiles.length > 0">
            <div
              v-for="(file, index) in pendingFiles"
              :key="index"
              class="attachment-item"
            >
              <span class="attachment-name">{{ file.name }}</span>
              <n-icon class="remove-btn" @click="removeFile(index)"
                ><X
              /></n-icon>
            </div>
          </div>

          <n-input
            v-model:value="inputText"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            placeholder="输入您的问题... (支持拖拽或粘贴文件,如 PDF、TXT 等)"
            :bordered="false"
            @keyup.enter.exact="sendMessage"
            @paste="handlePaste"
            :disabled="isLoading"
            style="background: transparent"
          />

          <div
            class="input-tools"
            style="justify-content: space-between; align-items: center"
          >
            <!-- 左侧工具栏:附件上传 -->
            <div class="left-tools">
              <n-button
                quaternary
                circle
                @click="triggerFileInput"
                :disabled="isLoading"
              >
                <template #icon
                  ><n-icon size="18"><Paperclip /></n-icon
                ></template>
              </n-button>
              <!-- 隐藏的 file input -->
              <input
                type="file"
                ref="fileInputRef"
                style="display: none"
                multiple
                @change="handleFileSelect"
              />
            </div>

            <!-- 右侧工具栏:发送按钮 -->
            <div class="right-tools">
              <n-button
                color="#3b82f6"
                @click="sendMessage"
                :disabled="isLoading"
                style="padding: 0 24px; border-radius: 8px"
              >
                <template #icon>
                  <n-icon><Send /></n-icon>
                </template>
                发送
              </n-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ================= 右侧:附件管理面板(可收起) ================= -->
    <transition name="file-panel-slide">
      <div v-if="showFilePanel" class="feature-filesidebar">
        <div class="filesidebar-header">
          <span class="filesidebar-title">📎 附件管理</span>
          <div class="filesidebar-actions">
            <n-button
              quaternary
              size="tiny"
              type="warning"
              @click="clearSessionFiles"
              v-if="currentChatFiles.length > 0"
            >
              清空
            </n-button>
            <n-button
              quaternary
              circle
              size="tiny"
              @click="showFilePanel = false"
            >
              <template #icon>
                <n-icon size="16"><X /></n-icon>
              </template>
            </n-button>
          </div>
        </div>
        <n-scrollbar class="filesidebar-body">
          <div
            v-for="f in currentChatFiles"
            :key="f.id"
            class="filesidebar-item"
          >
            <n-checkbox v-model:checked="f.selected" size="small" />
            <span class="file-name" :title="f.name">{{ f.name }}</span>
            <span class="file-size">{{
              f.size > 1024 * 1024
                ? (f.size / 1024 / 1024).toFixed(1) + "MB"
                : (f.size / 1024).toFixed(0) + "KB"
            }}</span>
            <n-icon
              size="14"
              class="file-remove"
              @click="removeSessionFile(f.id)"
            >
              <X />
            </n-icon>
          </div>
          <div v-if="currentChatFiles.length === 0" class="file-empty-hint">
            暂无附件,拖拽或粘贴文件到输入框即可添加。
          </div>
        </n-scrollbar>
        <div class="filesidebar-footer">
          <span class="filesidebar-tip" v-if="currentChatFiles.length > 0">
            勾选的文件将在下一轮发送时一并解析
          </span>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted } from "vue";
import { useMessage, NIcon } from "naive-ui";
import {
  Plus,
  MessageSquare,
  Trash2,
  Pen,
  Copy,
  Send,
  Sparkles,
  User,
  Paperclip,
  X,
} from "lucide-vue-next";
import axios from "axios";

// ================= 新增:引入 Markdown 与代码高亮 =================
import MarkdownIt from "markdown-it";
import hljs from "highlight.js";
import "highlight.js/styles/atom-one-dark.css";

// 初始化解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`;
  },
});
// =============================================================

// 确保 CSS 文件路径正确
import "../styles/feature-layout.css";

const messageUI = useMessage();
const scrollbarRef = ref(null);
const inputText = ref("");
const isLoading = ref(false);
let abortController = null;

// ================= JWT 登录与权限控制 =================
const showLoginModal = ref(false);
const isAuthenticating = ref(false);
const isLoginMode = ref(true); // 控制当前是登录还是注册模式
const authForm = ref({ username: "", password: "" });
const currentUser = ref("研究员");

const userMenuOptions = [
  { type: "divider", key: "d1" },
  { label: "退出登录", key: "logout" },
];

const handleUserMenu = (key) => {
  if (key === "logout") {
    localStorage.removeItem("saea_token");
    localStorage.removeItem("saea_user");
    delete axios.defaults.headers.common["Authorization"];
    currentUser.value = "";
    authForm.value = { username: "", password: "" };
    isLoginMode.value = true;
    showLoginModal.value = true;
    chatHistories.value = []; // 退出时清空当前聊天列表
    messageUI.success("已安全退出当前账号");
  }
};

onMounted(() => {
  const token = localStorage.getItem("saea_token");
  if (!token) {
    showLoginModal.value = true;
  } else {
    axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    currentUser.value = localStorage.getItem("saea_user") || "研究员";
    fetchCloudHistories(); // 重点:带着 Token 去拉取云端记录
  }
});

const toggleAuthMode = () => {
  isLoginMode.value = !isLoginMode.value;
  authForm.value.password = ""; // 切换模式时清空密码以防误操作
};

const handleAuth = async () => {
  if (!authForm.value.username || !authForm.value.password) {
    messageUI.warning("请输入完整的账号和密码");
    return;
  }
  isAuthenticating.value = true;

  // 根据当前模式决定请求的接口路径
  const apiEndpoint = isLoginMode.value ? "/api/login" : "/api/register";

  try {
    const res = await axios.post(apiEndpoint, authForm.value);

    if (res.data.status === "success") {
      // 登录或注册成功,保存凭证
      localStorage.setItem("saea_token", res.data.token);
      localStorage.setItem("saea_user", authForm.value.username);
      axios.defaults.headers.common["Authorization"] =
        `Bearer ${res.data.token}`;

      currentUser.value = authForm.value.username;
      showLoginModal.value = false;
      messageUI.success(res.data.message);
    } else {
      // 后端返回业务错误(例如:密码错误、账号不存在等)
      messageUI.error(res.data.message);
    }
  } catch (error) {
    messageUI.error("网络异常,无法连接到身份验证服务器");
  } finally {
    isAuthenticating.value = false;
  }
};

// --- 新增附件相关状态 ---
const showFilePanel = ref(false);
const pendingFiles = ref([]);
const fileInputRef = ref(null);
const isDragging = ref(false);

// 所有会话的文件库:{ [chatId]: [{ id, name, size, file: File, selected }] }
const sessionFilesMap = ref({});

// 当前会话的文件列表
const currentChatFiles = computed(() => {
  return sessionFilesMap.value[currentChatId.value] || [];
});

// 1. 点击触发资源管理器
const triggerFileInput = () => {
  if (fileInputRef.value) fileInputRef.value.click();
};

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files);
  addFiles(files);
  event.target.value = ""; // 清空以允许重复选择同名文件
};

// 2. 拖拽逻辑
const onDragOver = () => {
  isDragging.value = true;
};
const onDragLeave = () => {
  isDragging.value = false;
};
const onDrop = (e) => {
  isDragging.value = false;
  const files = Array.from(e.dataTransfer.files);
  addFiles(files);
};

// 3. 剪贴板粘贴逻辑
const handlePaste = (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;

  const files = [];
  for (let i = 0; i < items.length; i++) {
    if (items[i].kind === "file") {
      files.push(items[i].getAsFile());
    }
  }

  if (files.length > 0) {
    e.preventDefault(); // 拦截默认行为,防止浏览器尝试将图片等塞入输入框
    addFiles(files);
  }
};

// 统一加入待发送队列
const addFiles = (files) => {
  const MAX_FILES = 10;
  const currentCount = pendingFiles.value.length;
  const remaining = MAX_FILES - currentCount;

  if (remaining <= 0) {
    messageUI.warning(`附件已达上限 ${MAX_FILES} 个,请先移除已有附件`);
    return;
  }

  const accepted = files.length > remaining ? files.slice(0, remaining) : files;
  pendingFiles.value.push(...accepted);

  // 同步记录到当前会话的文件库(侧边栏附件管理)
  if (!sessionFilesMap.value[currentChatId.value]) {
    sessionFilesMap.value[currentChatId.value] = [];
  }
  const existingNames = new Set(sessionFilesMap.value[currentChatId.value].map((x) => x.name));
  for (const f of accepted) {
    if (!existingNames.has(f.name)) {
      sessionFilesMap.value[currentChatId.value].push({
        id: Date.now() + "_" + Math.random().toString(36).slice(2, 6),
        name: f.name,
        size: f.size,
        file: f,
        selected: true,
      });
      existingNames.add(f.name);
    }
  }

  messageUI.success(`已添加附件 (${pendingFiles.value.length}/${MAX_FILES})`);
};

// 移除附件
const removeFile = (index) => {
  pendingFiles.value.splice(index, 1);
};

// 从侧边栏附件管理中移除
const removeSessionFile = (fileId) => {
  const list = sessionFilesMap.value[currentChatId.value];
  if (!list) return;
  const idx = list.findIndex((f) => f.id === fileId);
  if (idx !== -1) list.splice(idx, 1);
};

// 清空当前会话的所有附件记录
const clearSessionFiles = () => {
  sessionFilesMap.value[currentChatId.value] = [];
};

// ================= 侧边栏重命名逻辑 =================
const editingChatId = ref(null);
const editingTitle = ref("");

const startEditChat = (chat) => {
  editingChatId.value = chat.id;
  editingTitle.value = chat.title;
};

const saveChatTitle = (chat) => {
  if (editingTitle.value.trim() !== "") {
    chat.title = editingTitle.value.trim();
    syncChatToCloud(chat); // 标题改完立刻同步云端
  }
  editingChatId.value = null;
};

// ================= 云端历史记录接管 =================
const chatHistories = ref([]);
const currentChatId = ref(null);

// 1. 拉取云端历史
const fetchCloudHistories = async () => {
  try {
    const res = await axios.get("/api/chat/history");
    if (res.data.status === "success") {
      chatHistories.value = res.data.data;
      if (chatHistories.value.length === 0) {
        createNewChat(); // 如果是新账号,自动建一个新会话
      } else {
        currentChatId.value = chatHistories.value[0].id;
      }
    }
  } catch (e) {
    messageUI.error("无法拉取云端历史记录,请检查网络");
  }
};

// 2. 同步数据到云端 (替代了原本的 watch + localStorage)
const syncChatToCloud = async (chat) => {
  if (!chat) return;
  try {
    await axios.post("/api/chat/sync", {
      id: chat.id,
      title: chat.title,
      messages: chat.messages,
    });
  } catch (e) {
    console.error("云端同步失败", e);
  }
};

const createNewChat = () => {
  const newId = Date.now().toString();
  const newChat = {
    id: newId,
    title: "新文献研讨",
    timestamp: Date.now(),
    messages: [
      {
        role: "ai",
        content:
          "我是教研室专属文献助手。\n目前已接入 DeepSeek V4.0 Flash模型,你可以随时向我提问。",
      },
    ],
  };
  chatHistories.value.unshift(newChat);
  currentChatId.value = newId;
  syncChatToCloud(newChat); // 创建后立刻上云
};

const selectChat = (id) => {
  if (isLoading.value) return messageUI.warning("请等待当前检索完毕");
  currentChatId.value = id;
};

// 3. 删除云端数据
const deleteChat = async (id) => {
  if (isLoading.value && id === currentChatId.value) return;
  try {
    await axios.delete(`/api/chat/session/${id}`); // 通知后端删除
    chatHistories.value = chatHistories.value.filter((c) => c.id !== id);
    if (chatHistories.value.length === 0) createNewChat();
    else if (currentChatId.value === id)
      currentChatId.value = chatHistories.value[0].id;
    messageUI.success("删除成功");
  } catch (e) {
    messageUI.error("删除失败");
  }
};

const currentMessages = computed(() => {
  const chat = chatHistories.value.find((c) => c.id === currentChatId.value);
  return chat ? chat.messages : [];
});

const scrollToBottom = async () => {
  await nextTick();
  if (scrollbarRef.value)
    scrollbarRef.value.scrollTo({ top: 9999, behavior: "smooth" });
};

const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    messageUI.success("已复制到剪贴板");
  } catch (err) {
    messageUI.error("复制失败,请手动复制");
  }
};

// 删除单条消息功能
const deleteSingleMessage = (index) => {
  const activeChat = chatHistories.value.find(
    (c) => c.id === currentChatId.value,
  );
  if (activeChat && activeChat.messages) {
    activeChat.messages.splice(index, 1);
    syncChatToCloud(activeChat); // <--- 新增:删除后同步
  }
};

const formatMessage = (text) => {
  if (!text) return "";
  return md.render(text).trim(); // 🔴 增加 .trim():暴力砍掉 markdown 自动生成的末尾多余换行符
};

const sendMessage = async () => {
  // 1. 修改拦截逻辑:只要有文字 OR 有附件,都可以发送
  if (
    (!inputText.value.trim() && pendingFiles.value.length === 0) ||
    isLoading.value
  )
    return;

  const userText = inputText.value;
  const activeChat = chatHistories.value.find(
    (c) => c.id === currentChatId.value,
  );

  if (activeChat.title === "新文献研讨") {
    const titleText = userText || pendingFiles.value[0].name;
    activeChat.title =
      titleText.substring(0, 15) + (titleText.length > 15 ? "..." : "");
  }

  // 【关键修复】当用户只传附件没写文字时,提供默认的 Prompt 避免后端 LLM 接收到空消息报错
  const finalMessageText =
    userText.trim() === "" && pendingFiles.value.length > 0
      ? "请帮我分析一下上传的附件内容。"
      : userText;

  // 3. 在前端聊天气泡里展示你发出的文件名称
  let displayContent = userText;
  if (pendingFiles.value.length > 0) {
    const fileTags = pendingFiles.value
      .map((f) => `📄 <b>${f.name}</b>`)
      .join("<br/>");
    displayContent = displayContent
      ? `${displayContent}<br/><br/>${fileTags}`
      : fileTags;
  }

  // 4. 在清空前,先把文件对象存到局部变量
  //    包括:本次新拖拽/粘贴的(pendingFiles)+ 侧边栏历史文件中被勾选的
  const filesToSend = [...pendingFiles.value];
  const pendingNames = new Set(pendingFiles.value.map((f) => f.name));
  for (const sf of currentChatFiles.value) {
    if (sf.selected && !pendingNames.has(sf.name)) {
      filesToSend.push(sf.file);
      pendingNames.add(sf.name);
    }
  }

  // 5. 清空输入框和底部的附件待发送区
  inputText.value = "";
  pendingFiles.value = [];

  // 把处理好的图文内容推入界面
  activeChat.messages.push({ role: "user", content: displayContent });
  isLoading.value = true;
  scrollToBottom();
  // 不同步到 DB--等 API 完成后一并同步,避免后端重复读取当前消息

  abortController = new AbortController();
  activeChat.messages.push({ role: "ai", content: "" });
  const targetMsg = activeChat.messages[activeChat.messages.length - 1];

  try {
    // 6. 构建 FormData - 二进制文件直传,零 Base64 膨胀
    //     不再传 history,由后端从数据库读取并截断
    const token = localStorage.getItem("saea_token");
    const formData = new FormData();
    formData.append("message", finalMessageText);
    formData.append("session_id", activeChat.id);

    // 前端文件尺寸门控
    for (const file of filesToSend) {
      if (file.size > 20 * 1024 * 1024) {
        targetMsg.content += `\n\n⚠️ 文件 "${file.name}" 超过 20MB 限制,已跳过。`;
      }
      formData.append("files", file);
    }

    const response = await fetch("/api/llm/chat/text", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        // 不设 Content-Type,浏览器自动配 multipart boundary
      },
      body: formData,
      signal: abortController.signal,
    });

    // 【修复】HTTP 错误码处理 - 避免 401/422 静默失败
    if (!response.ok) {
      const errText = await response.text();
      targetMsg.content += `\n\n[错误 ${response.status}] ${errText.slice(0, 200)}`;
      scrollToBottom();
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const dataStr = line.replace("data: ", "").trim();
          if (dataStr === "[DONE]") continue;
          try {
            const parsed = JSON.parse(dataStr);
            if (
              parsed.choices &&
              parsed.choices[0].delta &&
              parsed.choices[0].delta.content
            ) {
              targetMsg.content += parsed.choices[0].delta.content;
              scrollToBottom();
            }
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    if (error.name !== "AbortError")
      targetMsg.content += `\n[网络错误] 无法连接到后端。`;
  } finally {
    isLoading.value = false;
    abortController = null;
    syncChatToCloud(activeChat);
  }
};
</script>

<style scoped>
.message-content-wrapper {
  display: flex;
  flex-direction: column;
}

/* 针对用户和AI的气泡对齐方式 */
.message-item.user .message-content-wrapper {
  align-items: flex-end;
}
.message-item.ai .message-content-wrapper {
  align-items: flex-start;
}

/* 消息下方的操作按钮样式 */
.msg-actions {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 12px;
  color: var(--n-text-color-3);
  opacity: 0; /* 默认隐藏 */
  transition: opacity 0.2s ease;
  padding: 0 4px;
}

/* 鼠标悬浮在这一条消息上时,显示操作栏 */
.message-item:hover .msg-actions {
  opacity: 1;
}

.msg-actions span {
  cursor: pointer;
  transition: color 0.2s;
}

.msg-actions span:hover {
  color: #3b82f6;
}

.typing-cursor {
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}

/* ================= 侧边栏操作图标动效 ================= */
.saea-feature-page .chat-actions .action-icon {
  transition: all 0.2s ease;
}

.saea-feature-page .chat-actions .action-icon:hover {
  opacity: 1 !important;
  color: #3b82f6;
  transform: scale(1.1);
}

.saea-feature-page .history-item:hover .chat-actions {
  opacity: 1 !important;
}

/* 强制允许用户框选复制 AI 回答内容 */
.bubble {
  user-select: text !important;
  -webkit-user-select: text !important;
}

/* 确保内部的 span 或 v-html 渲染的子元素也允许被选中 */
.bubble * {
  user-select: text !important;
  -webkit-user-select: text !important;
}
/* 用户气泡:最宽占 900px 容器的 85% */
.message-item.user .bubble {
  max-width: 100% !important;
}

/* AI 气泡:包含代码和长文本,可以允许占满 900px 容器 */
.message-item.ai .bubble {
  max-width: 100% !important;
}

/* ================= Markdown 元素美化 ================= */
/* 强制清除最后一个元素的底部空白，解决气泡底部变"胖"的问题 */
.md-render-box {
  white-space: normal;
  word-break: break-word;
  font-size: 15px;
}

/* 清除最后一个子元素的 margin-bottom */
.md-render-box :deep(*:last-child) {
  margin-bottom: 0 !important;
}

/* 2. 确保首行不会顶开气泡顶部 */
.md-render-box :deep(*:first-child) {
  margin-top: 0 !important;
}

/* 3. 收紧普通段落的行高和段间距 */
.md-render-box :deep(p) {
  margin: 0 0 6px 0;
  line-height: 1.5;
}

/* 4. 收紧各级标题的上下间距 */
.md-render-box :deep(h1),
.md-render-box :deep(h2),
.md-render-box :deep(h3),
.md-render-box :deep(h4),
.md-render-box :deep(h5),
.md-render-box :deep(h6) {
  margin: 10px 0 6px 0;
  line-height: 1.25;
}

/* 5. 收紧分割线间距 */
.md-render-box :deep(hr) {
  margin: 10px 0;
  border: 0;
  border-top: 1px solid rgba(156, 163, 175, 0.2);
}

/* 6. 收紧列表间距 */
.md-render-box :deep(ul),
.md-render-box :deep(ol) {
  margin: 4px 0 8px 20px;
  padding-left: 0;
}
.md-render-box :deep(li) {
  margin-bottom: 2px;
}

/* 优雅的表格 */
.md-render-box :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 0 0 1px rgba(156, 163, 175, 0.2);
}
.md-render-box :deep(th),
.md-render-box :deep(td) {
  border: 1px solid rgba(156, 163, 175, 0.15);
  padding: 8px 12px;
  text-align: left;
}
.md-render-box :deep(th) {
  background-color: rgba(255, 255, 255, 0.05);
  font-weight: bold;
}

/* 代码高亮块修正 */
.md-render-box :deep(pre.hljs) {
  padding: 12px;
  border-radius: 8px;
  margin: 10px 0;
  overflow-x: auto;
  background-color: #1e1e20;
  border: 1px solid rgba(156, 163, 175, 0.1);
}
.md-render-box :deep(code) {
  font-family: Consolas, Monaco, monospace;
  font-size: 14px;
}
.md-render-box :deep(:not(pre) > code) {
  background-color: rgba(156, 163, 175, 0.15);
  padding: 2px 4px;
  border-radius: 4px;
  color: #3b82f6;
}

/* ================= 右侧附件管理面板样式 ================= */
.saea-feature-page {
  display: flex;
}

.feature-filesidebar {
  width: 350px;
  min-width: 350px;
  border-left: 1px solid rgba(156, 163, 175, 0.15);
  background: var(--n-card-color);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.filesidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 14px 8px;
  border-bottom: 1px solid rgba(156, 163, 175, 0.1);
}

.filesidebar-title {
  font-size: 14px;
  font-weight: bold;
  color: var(--n-text-color-2);
}

.filesidebar-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filesidebar-body {
  flex: 1;
  padding: 8px 10px;
  overflow-y: auto;
}

.filesidebar-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 6px;
  border-radius: 6px;
  font-size: 13px;
  transition: background 0.15s;
  margin-bottom: 2px;
}

.filesidebar-item:hover {
  background: rgba(156, 163, 175, 0.08);
}

.filesidebar-item .file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--n-text-color-1);
}

.filesidebar-item .file-size {
  font-size: 11px;
  color: var(--n-text-color-4);
  flex-shrink: 0;
}

.filesidebar-item .file-remove {
  cursor: pointer;
  opacity: 0.4;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.filesidebar-item .file-remove:hover {
  opacity: 1;
  color: #e74c3c;
}

.filesidebar-footer {
  padding: 8px 14px 12px;
  border-top: 1px solid rgba(156, 163, 175, 0.1);
}

.filesidebar-tip {
  font-size: 11px;
  color: var(--n-text-color-4);
  display: block;
  text-align: center;
}

.file-empty-hint {
  font-size: 13px;
  color: var(--n-text-color-4);
  text-align: center;
  padding: 24px 12px;
  line-height: 1.6;
}

/* 右面板滑入动画 */
.file-panel-slide-enter-active,
.file-panel-slide-leave-active {
  transition: all 0.25s ease;
}
.file-panel-slide-enter-from,
.file-panel-slide-leave-to {
  opacity: 0;
  width: 0;
  min-width: 0;
  padding: 0;
  border: none;
  overflow: hidden;
}
</style>
