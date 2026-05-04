<template>
  <div>
    <Teleport to="body">
      <transition name="window-fade">
        <div
          v-show="isOpen"
          ref="chatWindowRef"
          class="os-chat-window"
          :class="{ 'is-ghost': isGhostMode, 'is-fullscreen': isFullscreen }"
          :style="isFullscreen ? {} : { left: `${x}px`, top: `${y}px` }"
          @paste="handlePaste"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <div ref="dragHandleRef" class="chat-header" @dblclick="toggleFullscreen">
            <div class="header-left">
              <span class="title-text">视觉核心 (Vision)</span>
              <span 
                class="action-btn" 
                :class="{ 'active-btn': showHistoryPanel }" 
                title="历史会话列表" 
                @click.stop="toggleHistoryPanel"
              >📚</span>
            </div>

            <div class="header-model-info">
              Qwen3.5-397B-A17B
            </div>

            <div class="header-right">
              <div class="dot-wrapper" :title="isGhostMode ? '解除穿透' : '开启穿透模式'" @click.stop="toggleGhostMode"><span class="dot yellow"></span></div>
              <div class="dot-wrapper" :title="isFullscreen ? '向下还原' : '全屏展开'" @click.stop="toggleFullscreen"><span class="dot green"></span></div>
              <div class="dot-wrapper" title="关闭" @click.stop="toggleChat"><span class="dot red"></span></div>
            </div>
          </div>

          <div class="chat-container-main">
            <transition name="slide-left">
              <div v-if="showHistoryPanel" class="history-sidebar">
                <div class="sidebar-header">
                  <span class="sidebar-title">对话记录</span>
                  <n-button size="small" type="primary" @click="createNewChat" style="padding: 0 8px;">➕ 新对话</n-button>
                </div>
                <n-scrollbar class="history-list">
                  <div
                    v-for="chat in chatHistories"
                    :key="chat.id"
                    class="history-item"
                    :class="{ 'is-active': chat.id === currentChatId }"
                    @click="selectChat(chat.id)"
                  >
                    <div class="history-item-content">
                      <span class="history-icon">💬</span>
                      <input
                        v-if="editingChatId === chat.id"
                        v-model="editingTitle"
                        class="edit-title-input"
                        @keyup.enter="saveTitle(chat, $event)"
                        @blur="saveTitle(chat, $event)"
                        @click.stop
                        autoFocus
                      />
                      <span v-else class="history-title" :title="chat.title">{{ chat.title }}</span>
                    </div>

                    <div class="history-actions" v-if="editingChatId !== chat.id">
                      <span class="action-icon" title="重命名" @click.stop="startEditTitle(chat, $event)">✏️</span>
                      <span class="action-icon delete-icon" title="删除对话" @click.stop="deleteChat(chat.id)">🗑️</span>
                    </div>
                  </div>
                  <div v-if="chatHistories.length === 0" class="empty-history">暂无历史记录</div>
                </n-scrollbar>
              </div>
            </transition>

            <div class="chat-body" @click="closeHistoryOnBodyClick">
               <n-scrollbar class="message-list" ref="scrollbarRef">
                <div v-for="(msg, index) in currentMessages" :key="index" :class="['message-item', msg.role]">
                  <div class="bubble">
                    <div v-if="msg.images && msg.images.length" class="message-images-grid">
                       <img v-for="(img, idx) in msg.images" :key="idx" :src="img" class="chat-image" @click="previewChatImage(img)" />
                    </div>
                    <div v-if="msg.content" class="text-content">{{ msg.content }}</div>
                    <div v-else-if="isLoading && index === currentMessages.length - 1" class="typing-cursor">█</div>
                  </div>
                </div>
              </n-scrollbar>
            </div>
          </div>

          <div class="chat-footer">
            <transition name="fade">
              <div v-if="isDragging" class="drag-overlay">
                <div class="drag-content">
                  <span style="font-size: 28px;">📥</span>
                  <p style="margin: 4px 0 0 0; font-size: 13px;">松开上传图片</p>
                </div>
              </div>
            </transition>

            <input type="file" ref="fileInputRef" accept="image/*" style="display: none;" @change="handleFileSelect" />

            <div class="input-wrapper">
              <div v-if="pendingImages.length > 0" class="pending-images-container">
                <div v-for="(imgBase64, index) in pendingImages" :key="index" class="pending-image-preview">
                  <img :src="imgBase64" />
                  <span class="remove-btn" @click="removePendingImage(index)">×</span>
                </div>
              </div>

              <div class="input-controls">
                <n-button text style="font-size: 20px; color: rgba(255,255,255,0.7); margin-right: 8px;" title="上传图片" @click="triggerFileInput">📎</n-button>
                <n-input
                  v-model:value="inputText"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 4 }"
                  placeholder="上传图表并描述问题，支持剪切板、拖拽或自动读取底层绘图"
                  @keyup.enter.exact="sendMessage"
                  style="background: transparent; flex: 1;"
                  :disabled="isLoading"
                />
                <n-button v-if="!isLoading" type="primary" @click="sendMessage" style="margin-left: 8px;">发送</n-button>
                <n-button v-else type="error" @click="stopGeneration" style="margin-left: 8px;">■ 停止</n-button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <div 
      ref="fabRef" 
      class="trigger-fab-wrapper"
      :style="{ left: `${fabX}px`, top: `${fabY}px` }"
    >
      <n-button class="trigger-fab" circle type="primary" size="large" @click="handleFabClick">
        <template #icon><span style="font-size: 24px;">{{ isOpen && !isGhostMode ? '×' : '💬' }}</span></template>
      </n-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted, inject } from 'vue'
import { useDraggable } from '@vueuse/core'
import { useMessage } from 'naive-ui'

const messageUI = useMessage()

// --- 窗口基础状态 ---
const isOpen = inject('isChatVisible', ref(false))
const isGhostMode = ref(false)
const isFullscreen = ref(false)
const chatWindowRef = ref(null)
const dragHandleRef = ref(null)
const scrollbarRef = ref(null)

const { x, y } = useDraggable(dragHandleRef, {
  initialValue: { x: window.innerWidth - 450, y: window.innerHeight - 620 }
})

// ✨ 新增悬浮球的拖拽逻辑
const fabRef = ref(null)
const isFabDragging = ref(false)
const { x: fabX, y: fabY } = useDraggable(fabRef, {
  // 初始位置计算：屏幕右下角
  initialValue: { x: window.innerWidth - 80, y: window.innerHeight - 80 },
  // 拖拽时标记状态，拖拽结束延迟 50ms 释放，防止误触发点击打开窗口
  onMove: () => { isFabDragging.value = true },
  onEnd: () => { setTimeout(() => { isFabDragging.value = false }, 50) }
})

const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (!isOpen.value) { isGhostMode.value = false; isFullscreen.value = false }
  else { scrollToBottom() }
}
const toggleGhostMode = () => isGhostMode.value = !isGhostMode.value
const toggleFullscreen = () => isFullscreen.value = !isFullscreen.value
const handleFabClick = () => {
  if (isFabDragging.value) return 
  isGhostMode.value ? (isGhostMode.value = false) : toggleChat()
}
const scrollToBottom = async () => {
  await nextTick()
  if (scrollbarRef.value) scrollbarRef.value.scrollTo({ top: 9999, behavior: 'smooth' })
}

// --- 传图逻辑 ---
const fileInputRef = ref(null)
const pendingImages = ref([])
const isDragging = ref(false)

const triggerFileInput = () => fileInputRef.value.click()
const fileToBase64 = (file) => new Promise((resolve, reject) => {
  const reader = new FileReader(); reader.readAsDataURL(file);
  reader.onload = () => resolve(reader.result); reader.onerror = e => reject(e)
})

const processImageFile = async (file) => {
  if (!file || !file.type.startsWith('image/')) return messageUI.error("只能上传图片文件！")
  if (pendingImages.value.length >= 4) return messageUI.warning("一次最多发 4 张图。")
  try { pendingImages.value.push(await fileToBase64(file)) } catch (e) { messageUI.error("图片读取失败") }
}

const handleFileSelect = (e) => { if (e.target.files[0]) processImageFile(e.target.files[0]); e.target.value = '' }
const handlePaste = (e) => {
  const items = e.clipboardData?.items; if (!items) return;
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) { processImageFile(items[i].getAsFile()); e.preventDefault(); break; }
  }
}
const handleDrop = (e) => { isDragging.value = false; if (e.dataTransfer?.files?.length) Array.from(e.dataTransfer.files).forEach(f => processImageFile(f)) }
const removePendingImage = (index) => pendingImages.value.splice(index, 1)
const previewChatImage = (url) => window.open(url, '_blank')


// --- 🌟 多会话历史记录系统 ---
const currentAgent = ref('vision')
const inputText = ref('')
const isLoading = ref(false)
let abortController = null

const showHistoryPanel = ref(false)
const toggleHistoryPanel = () => showHistoryPanel.value = !showHistoryPanel.value
const closeHistoryOnBodyClick = () => { if (showHistoryPanel.value && window.innerWidth < 800) showHistoryPanel.value = false } // 移动端点击外侧收起

const generateInitialSession = () => [
  { role: 'ai', content: '视觉核心已就绪，请上传图片。' }
]
// 读取本地缓存的整个对话列表
const loadHistories = () => {
  const saved = localStorage.getItem('saea_chat_histories_v2')
  if (saved) {
    try { return JSON.parse(saved) } catch (e) { return null }
  }
  return null
}

const chatHistories = ref(loadHistories() || [])
const currentChatId = ref(null)

const handleGlobalKeyDown = (e) => {
  if (e.key === 'Escape' && isOpen.value) {
    toggleGhostMode()
  }
}
onMounted(() => { window.addEventListener('keydown', handleGlobalKeyDown) })
onUnmounted(() => { window.removeEventListener('keydown', handleGlobalKeyDown) })
const editingChatId = ref(null)
const editingTitle = ref('')

const startEditTitle = (chat, event) => {
  event.stopPropagation() // 防止触发选择对话
  editingChatId.value = chat.id
  editingTitle.value = chat.title
}

const saveTitle = (chat, event) => {
  if (event) event.stopPropagation()
  if (editingTitle.value.trim()) {
    chat.title = editingTitle.value.trim()
  }
  editingChatId.value = null
}

// 创建新对话
const createNewChat = () => {
  const newId = Date.now().toString()
  const newChat = {
    id: newId,
    title: '新视觉分析',
    timestamp: Date.now(),
    sessions: { vision: generateInitialSession() }
  }
  chatHistories.value.unshift(newChat) // 插入到最前面
  currentChatId.value = newId
  if (window.innerWidth < 800) showHistoryPanel.value = false
}

// 初始化兜底逻辑
if (chatHistories.value.length === 0) {
  createNewChat()
} else {
  currentChatId.value = chatHistories.value[0].id // 默认选中最新一条
}

// 选择对话
const selectChat = (id) => {
  if (isLoading.value) return messageUI.warning("请等待当前回答生成完毕")
  currentChatId.value = id
  if (window.innerWidth < 800) showHistoryPanel.value = false
  scrollToBottom()
}

// 删除对话
const deleteChat = (id) => {
  if (isLoading.value && id === currentChatId.value) return messageUI.warning("无法删除正在生成的对话")
  chatHistories.value = chatHistories.value.filter(c => c.id !== id)
  if (chatHistories.value.length === 0) {
    createNewChat()
  } else if (currentChatId.value === id) {
    currentChatId.value = chatHistories.value[0].id // 如果删的是当前看的，自动切到第一个
  }
}

// 持久化监听
watch(chatHistories, (newVal) => {
  localStorage.setItem('saea_chat_histories_v2', JSON.stringify(newVal))
}, { deep: true })

// 智能提取当前选中的对话记录
const activeSessions = computed(() => {
  const chat = chatHistories.value.find(c => c.id === currentChatId.value)
  return chat ? chat.sessions : { vision: [] }
})

const currentMessages = computed(() => activeSessions.value.vision)

// --- 发送与生成逻辑 ---
const stopGeneration = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
    isLoading.value = false
  }
}

const autoCaptureCanvas = () => {
  // 1. 扫描网页底层所有的 canvas 元素 (Echarts 默认渲染引擎)
  const canvases = Array.from(document.querySelectorAll('canvas'))
  if (canvases.length === 0) return null

  // 2. 智能筛选：找到面积最大的 Canvas（通常就是主图表，排除掉其他 UI 小图标）
  let largestCanvas = canvases[0]
  let maxArea = largestCanvas.width * largestCanvas.height

  for (let i = 1; i < canvases.length; i++) {
    const area = canvases[i].width * canvases[i].height
    if (area > maxArea) {
      largestCanvas = canvases[i]
      maxArea = area
    }
  }

  // 3. 防误触：如果最大的画布尺寸也极小，说明页面上没图表
  if (maxArea < 20000) return null

  // 4. 瞬间提取为 Base64 图像
  try {
    // 采用浅色背景填充，防止图表是透明背景导致 AI 看起来是全黑的
    const tempCanvas = document.createElement('canvas')
    tempCanvas.width = largestCanvas.width
    tempCanvas.height = largestCanvas.height
    const ctx = tempCanvas.getContext('2d')
    ctx.fillStyle = '#18181c' // 配合你的深色平台背景
    ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height)
    ctx.drawImage(largestCanvas, 0, 0)

    return tempCanvas.toDataURL('image/png')
  } catch (e) {
    console.warn('Canvas 截取失败', e)
    return null
  }
}

const sendMessage = async () => {
  if ((!inputText.value.trim() && pendingImages.value.length === 0) || isLoading.value) return

  const activeAgent = currentAgent.value
  const userText = inputText.value
  let imagesToSend = [...pendingImages.value]

  if (activeAgent === 'vision' && imagesToSend.length === 0) {
    // 触发词库：用户的话里包含这些字眼，就激发自动截图
    const triggerWords = ['图', '曲线', '箱型', '参数', '分析', '看看', '走势', '结果']
    const shouldCapture = triggerWords.some(word => userText.includes(word))

    if (shouldCapture) {
      const autoCapturedB64 = autoCaptureCanvas()
      if (autoCapturedB64) {
        imagesToSend.push(autoCapturedB64)
        messageUI.success('视觉核心已自动读取底层图表数据')
      }
    }
  }

  // ✨ 智能标题提取：如果是这个模型的第一句话，取前12个字作为历史列表的标题
  const currentChatObj = chatHistories.value.find(c => c.id === currentChatId.value)
  if (currentChatObj && currentChatObj.title === '新对话' && userText) {
    currentChatObj.title = userText.substring(0, 12) + (userText.length > 12 ? '...' : '')
  }

  activeSessions.value[activeAgent].push({ role: 'user', content: userText, images: imagesToSend })
  inputText.value = ''; pendingImages.value = []
  isLoading.value = true
  scrollToBottom()

  abortController = new AbortController()

  activeSessions.value[activeAgent].push({ role: 'ai', content: '' })
  const targetMsg = activeSessions.value[activeAgent][activeSessions.value[activeAgent].length - 1]

  try {
    const history = activeSessions.value[activeAgent].slice(1, -2).map(m => ({ role: m.role === 'ai' ? 'assistant' : 'user', content: m.content || '[图片已发送]' }))
    const payload = { message: userText || "请分析", history: history, agent_id: activeAgent }
    if (imagesToSend.length > 0) payload.images_base64_list = imagesToSend

    const response = await fetch('/api/llm/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: abortController.signal
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.replace('data: ', '').trim()
          if (dataStr === '[DONE]') continue
          try {
            const parsed = JSON.parse(dataStr)
            if (parsed.choices && parsed.choices[0].delta && parsed.choices[0].delta.content) {
              targetMsg.content += parsed.choices[0].delta.content
              scrollToBottom()
            } else if (parsed.error) {
              targetMsg.content += `\n[系统错误] ${parsed.error}`
            }
          } catch (e) { }
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') targetMsg.content += ' 🛑 [已终止输出]'
    else targetMsg.content += `\n[网络错误] 无法连接到后端。`
  } finally {
    isLoading.value = false
    abortController = null
    scrollToBottom()
  }
}
</script>

<style scoped>
/* OS 窗口与基础定位 */
.os-chat-window {
  position: fixed; width: 420px; height: 550px; z-index: 9000; display: flex; flex-direction: column;
  background: rgba(30, 30, 30, 0.4) !important; 
  
  /* 显著提升模糊半径 */
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  
  /* 增强边框的亮部细线条，这是毛玻璃高级感的来源 */
  border: 1px solid rgba(255, 255, 255, 0.15);
  
  /* 增加一个非常淡的阴影，模拟环境遮挡 */
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
  border-radius: 8px; 
  overflow: hidden; 
  
  /* ✨ 修改点：将 filter 改为 backdrop-filter，防止动画冲突导致毛玻璃失效 */
  transition: opacity 0.3s ease, backdrop-filter 0.3s ease, -webkit-backdrop-filter 0.3s ease;
}
.os-chat-window:not(.is-fullscreen) { resize: both; }

.is-fullscreen { top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border-radius: 0; resize: none !important; }
.is-ghost {
  /* 把背景调得更透一点，或者直接写 transparent */
  background: rgba(30, 30, 30, 0.05) !important; 
  pointer-events: none !important;
  
  backdrop-filter: none !important;  
  -webkit-backdrop-filter: none !important;
  border: 1px solid rgba(24, 160, 88, 0.6) !important;
  
  /* ✨ 核心修复：强制整个窗口 DOM 树（包括内部的文字、气泡、滚动条全部半透明化） */
  opacity: 0.35 !important; 
  
  /* 启动呼吸灯动画 */
  animation: ghost-breathe 3s ease-in-out infinite alternate;
}

@keyframes ghost-breathe {
  0% { box-shadow: 0 0 10px rgba(24, 160, 88, 0.1), inset 0 0 10px rgba(24, 160, 88, 0.05); }
  100% { box-shadow: 0 0 25px rgba(24, 160, 88, 0.7), inset 0 0 20px rgba(24, 160, 88, 0.4); }
}
/* 头部 UI */
.chat-header { height: 44px; display: flex; align-items: center; justify-content: space-between; background: rgba(0, 0, 0, 0.3); border-bottom: 1px solid rgba(255, 255, 255, 0.05); cursor: grab; user-select: none; z-index: 10; }
.chat-header:active { cursor: grabbing; }
.header-left { display: flex; align-items: center; padding-left: 16px; }
.title-text { color: rgba(255,255,255,0.9); font-size: 13px; font-weight: bold; letter-spacing: 0.5px; }

.action-btn { margin-left: 10px; cursor: pointer; font-size: 15px; opacity: 0.5; transition: all 0.2s; filter: grayscale(100%); }
.action-btn:hover, .action-btn.active-btn { opacity: 1; filter: grayscale(0%); transform: scale(1.1); }

.header-model-info { flex: 1; text-align: center; font-size: 16px; color: rgba(255, 255, 255, 0.7); font-family: Consolas, monospace; pointer-events: none; }
.header-right { display: flex; align-items: center; height: 100%; padding-right: 12px; gap: 8px; }
.dot-wrapper { display: flex; align-items: center; justify-content: center; width: 24px; height: 24px; cursor: pointer; border-radius: 50%; transition: background 0.2s; }
.dot-wrapper:hover { background: rgba(255, 255, 255, 0.1); }
.dot { width: 12px; height: 12px; border-radius: 50%; transition: filter 0.2s; }
.dot-wrapper:hover .dot { filter: brightness(1.2); }
.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }
.history-actions { display: flex; gap: 6px; opacity: 0; transition: opacity 0.2s; }
.history-item:hover .history-actions { opacity: 1; }
.action-icon { font-size: 12px; opacity: 0.6; transition: all 0.2s; }
.action-icon:hover { opacity: 1; transform: scale(1.1); }
.delete-icon:hover { color: #ff5f56; }
.edit-title-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid #18a058;
  color: #fff;
  font-size: 13px;
  border-radius: 4px;
  padding: 2px 6px;
  width: 110px;
  outline: none;
}

/* ✨ 聊天区域主体结构 */
.chat-container-main { display: flex; flex: 1; overflow: hidden; position: relative; }

/* ✨ 侧边栏样式 */
.history-sidebar { width: 220px; background: rgba(15, 15, 18, 0.95); border-right: 1px solid rgba(255, 255, 255, 0.08); display: flex; flex-direction: column; z-index: 5; }
.sidebar-header { padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.sidebar-title { color: rgba(255,255,255,0.6); font-size: 12px; font-weight: bold; }
.history-list { flex: 1; padding: 8px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 8px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; transition: background 0.2s; }
.history-item:hover { background: rgba(255, 255, 255, 0.05); }
.history-item.is-active { background: rgba(24, 160, 88, 0.2); border-left: 3px solid #18a058; border-radius: 2px 6px 6px 2px; }
.history-item-content { display: flex; align-items: center; overflow: hidden; flex: 1; }
.history-icon { font-size: 14px; margin-right: 8px; opacity: 0.8; }
.history-title { color: rgba(255,255,255,0.85); font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 110px; }
.delete-btn { font-size: 12px; opacity: 0; transition: opacity 0.2s; }
.history-item:hover .delete-btn { opacity: 0.6; }
.delete-btn:hover { opacity: 1 !important; }
.empty-history { text-align: center; color: rgba(255,255,255,0.3); font-size: 12px; margin-top: 20px; }

/* 侧边栏动画 */
.slide-left-enter-active, .slide-left-leave-active { transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-left-enter-from, .slide-left-leave-to { opacity: 0; transform: translateX(-20px); width: 0; margin-right: -220px; } /* 负边距防止推挤主界面过硬 */

/* 内容区 */
.chat-body { flex: 1; padding: 16px; overflow: hidden; }
.message-list { height: 100%; }
.message-item { display: flex; margin-bottom: 16px; width: 100%; }
.message-item.user { justify-content: flex-end; }
.message-item.user .bubble { background: rgba(24, 160, 88, 0.8); color: #fff; border-radius: 12px 2px 12px 12px; padding: 10px 14px; white-space: pre-wrap;}
.message-item.ai { justify-content: flex-start; }
.message-item.ai .bubble { background: rgba(255, 255, 255, 0.1); color: #eee; border-radius: 2px 12px 12px 12px; padding: 10px 14px; white-space: pre-wrap; line-height: 1.6;}
.typing-cursor { display: inline-block; width: 8px; height: 16px; background: rgba(255, 255, 255, 0.8); animation: blink 1s step-end infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.chat-image { max-width: 100%; max-height: 200px; border-radius: 6px; margin-bottom: 8px; cursor: pointer; object-fit: contain; }
.message-images-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 4px; }

/* 底部输入与拖拽蒙层 */
.chat-footer { position: relative; padding: 12px 16px; background: rgba(0, 0, 0, 0.2); border-top: 1px solid rgba(255, 255, 255, 0.05); }
.drag-overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(24, 160, 88, 0.45); backdrop-filter: blur(4px); z-index: 9999; display: flex; align-items: center; justify-content: center; border: 2px dashed rgba(255, 255, 255, 0.6); border-radius: 0 0 8px 8px; }
.drag-content { text-align: center; color: white; font-weight: bold; pointer-events: none; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.input-wrapper { display: flex; flex-direction: column; width: 100%; }
.pending-images-container { display: flex; gap: 12px; margin-bottom: 8px; flex-wrap: wrap; }
.pending-image-preview { position: relative; width: 60px; height: 60px; margin-bottom: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.5); }
.pending-image-preview img { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }
.remove-btn { position: absolute; top: -6px; right: -6px; width: 18px; height: 18px; background: #ff5f56; color: white; border-radius: 50%; font-size: 14px; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
.input-controls { display: flex; align-items: flex-end; width: 100%; }
.trigger-fab-wrapper {
  position: fixed;
  z-index: 9999;
  cursor: move; /* 鼠标悬浮显示移动图标 */
  touch-action: none; /* 适配触屏设备的拖拽 */
}

/* 去掉原本写死的 bottom 和 right */
.trigger-fab { 
  box-shadow: 0 4px 16px rgba(24, 160, 88, 0.4); 
}
.window-fade-enter-active, .window-fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.window-fade-enter-from, .window-fade-leave-to { opacity: 0; transform: translateY(20px) scale(0.97); }
.is-ghost .chat-footer { display: none !important; }
.is-ghost .header-left .action-btn { display: none !important; }
</style>