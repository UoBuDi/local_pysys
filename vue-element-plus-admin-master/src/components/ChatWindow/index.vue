<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { ElScrollbar, ElAvatar } from 'element-plus'
import {
  sendMessage,
  getChatHistory,
  markRoomRead,
  getChatSessions,
  createChatRoom,
  getOnlineUsers,
  uploadChatFile,
  deleteChatMessage,
  type ChatMessage,
  type ChatSession,
  type OnlineUser
} from '@/api/chat'
import { useWebSocket, type WsMessage } from '@/utils/websocket'
import { useUserStore } from '@/store/modules/user'

const props = defineProps<{
  visible: boolean
  lastMessage: WsMessage | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'unread-change', count: number): void
}>()

const ws = useWebSocket()
const userStore = useUserStore()
const currentUserId = computed(() => userStore.getUserInfo?.id || 0)

const sessions = ref<ChatSession[]>([])
const currentRoomId = ref<string | null>(null)
const previousRoomId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const onlineUsers = ref<OnlineUser[]>([])
const showUserList = ref(false)
const messageScrollbar = ref<InstanceType<typeof ElScrollbar> | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const searchText = ref('')
const contextMenu = ref<{ visible: boolean; x: number; y: number; msgId: number }>({
  visible: false,
  x: 0,
  y: 0,
  msgId: 0
})
const isLoadingHistory = ref(false)
const hasMoreHistory = ref(true)
let onlineUsersTimer: ReturnType<typeof setInterval> | null = null

const currentSession = computed(() => sessions.value.find((s) => s.room_id === currentRoomId.value))

const totalUnread = computed(() => sessions.value.reduce((sum, s) => sum + s.unread_count, 0))

const filteredSessions = computed(() => {
  if (!searchText.value.trim()) return sessions.value
  const kw = searchText.value.trim().toLowerCase()
  return sessions.value.filter(
    (s) =>
      (s.room_name || '').toLowerCase().includes(kw) ||
      (s.last_content || '').toLowerCase().includes(kw)
  )
})

watch(totalUnread, (val) => {
  emit('unread-change', val)
})

watch(
  () => props.visible,
  async (val) => {
    if (val) {
      await loadSessions()
      startOnlineUsersPolling()
      if (!currentRoomId.value) {
        const lobby = sessions.value.find((s) => s.room_id === 'lobby')
        if (lobby) {
          currentRoomId.value = 'lobby'
        }
      }
    } else {
      stopOnlineUsersPolling()
    }
  }
)

watch(currentRoomId, async (newVal, oldVal) => {
  if (oldVal) {
    ws.leaveRoom(oldVal)
  }
  previousRoomId.value = oldVal || null
  if (newVal) {
    ws.joinRoom(newVal, { userId: currentUserId.value })
    hasMoreHistory.value = true
    await loadMessages(newVal)
    await markRoomRead(newVal)
    const session = sessions.value.find((s) => s.room_id === newVal)
    if (session) session.unread_count = 0
  }
})

const loadSessions = async () => {
  try {
    const resp = await getChatSessions()
    if (resp?.code === 200 && resp.data) {
      sessions.value = resp.data
    }
  } catch (e) {
    console.error('加载会话列表失败:', e)
  }
}

const loadMessages = async (roomId: string) => {
  try {
    const resp = await getChatHistory(roomId, 50)
    if (resp?.code === 200 && resp.data) {
      messages.value = resp.data
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    console.error('加载消息失败:', e)
  }
}

const loadOlderMessages = async () => {
  if (isLoadingHistory.value || !hasMoreHistory.value || !currentRoomId.value) return
  if (messages.value.length === 0) return

  isLoadingHistory.value = true
  const oldestId = messages.value[0]?.id
  if (!oldestId || oldestId < 0) {
    isLoadingHistory.value = false
    return
  }

  try {
    const resp = await getChatHistory(currentRoomId.value, 50, oldestId)
    if (resp?.code === 200 && resp.data) {
      if (resp.data.length === 0) {
        hasMoreHistory.value = false
      } else {
        const scrollbar = messageScrollbar.value?.wrapRef
        const prevScrollHeight = scrollbar?.scrollHeight || 0

        messages.value = [...resp.data, ...messages.value]

        await nextTick()
        if (scrollbar) {
          scrollbar.scrollTop = scrollbar.scrollHeight - prevScrollHeight
        }
      }
    }
  } catch (e) {
    console.error('加载历史消息失败:', e)
  } finally {
    isLoadingHistory.value = false
  }
}

const loadOnlineUsers = async () => {
  try {
    const resp = await getOnlineUsers()
    if (resp?.code === 200 && resp.data) {
      onlineUsers.value = resp.data
    }
  } catch (e) {
    console.error('加载在线用户失败:', e)
  }
}

const startOnlineUsersPolling = () => {
  stopOnlineUsersPolling()
  loadOnlineUsers()
  onlineUsersTimer = setInterval(loadOnlineUsers, 15000)
}

const stopOnlineUsersPolling = () => {
  if (onlineUsersTimer) {
    clearInterval(onlineUsersTimer)
    onlineUsersTimer = null
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || !currentRoomId.value) return

  const tempId = -Date.now()
  const optimisticMsg: ChatMessage = {
    id: tempId,
    room_id: currentRoomId.value,
    sender_id: currentUserId.value,
    sender_name: userStore.getUserInfo?.username || '',
    content_type: 'text',
    content: text,
    created_at: new Date().toISOString()
  }

  messages.value.push(optimisticMsg)
  inputText.value = ''
  scrollToBottom()

  try {
    const resp = await sendMessage({
      room_id: currentRoomId.value,
      content_type: 'text',
      content: text
    })
    if (resp?.code === 200 && resp.data) {
      const idx = messages.value.findIndex((m) => m.id === tempId)
      if (idx !== -1) {
        messages.value[idx] = {
          ...optimisticMsg,
          id: resp.data.id,
          created_at: resp.data.created_at || optimisticMsg.created_at
        }
      }
    }
    loadSessions()
  } catch (e) {
    console.error('发送消息失败:', e)
    const idx = messages.value.findIndex((m) => m.id === tempId)
    if (idx !== -1) {
      messages.value[idx] = { ...messages.value[idx], _failed: true } as any
    }
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.ctrlKey && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleFileUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !currentRoomId.value) return

  try {
    await uploadChatFile(file, currentRoomId.value)
    await loadMessages(currentRoomId.value)
    await loadSessions()
  } catch (e) {
    console.error('上传文件失败:', e)
  } finally {
    target.value = ''
  }
}

const startChat = async (targetUserId: number) => {
  try {
    const resp = await createChatRoom({
      target_user_id: targetUserId,
      room_type: 'private'
    })
    if (resp?.code === 200 && resp.data) {
      currentRoomId.value = resp.data.room_id
      showUserList.value = false
      await loadSessions()
    }
  } catch (e) {
    console.error('创建聊天房间失败:', e)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messageScrollbar.value) {
      const inner = messageScrollbar.value.wrapRef
      if (inner) {
        inner.scrollTop = inner.scrollHeight
      }
    }
  })
}

const handleScroll = ({ scrollTop }: { scrollTop: number }) => {
  if (scrollTop < 50 && !isLoadingHistory.value && hasMoreHistory.value) {
    loadOlderMessages()
  }
}

const formatMsgTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const formatSessionTime = (dateStr: string | null) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) return '昨天'
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const shouldShowTimeDivider = (index: number) => {
  if (index === 0) return true
  const curr = new Date(messages.value[index].created_at).getTime()
  const prev = new Date(messages.value[index - 1].created_at).getTime()
  return curr - prev > 5 * 60 * 1000
}

const formatTimeDivider = (dateStr: string) => {
  const d = new Date(dateStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const isYesterday = d.toDateString() === yesterday.toDateString()
  if (isToday) return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  if (isYesterday)
    return '昨天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  return d.getFullYear() + '年' + (d.getMonth() + 1) + '月' + d.getDate() + '日'
}

const showContextMenu = (e: MouseEvent, msgId: number) => {
  e.preventDefault()
  contextMenu.value = { visible: true, x: e.clientX, y: e.clientY, msgId }
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

const handleDeleteMessage = async () => {
  const msgId = contextMenu.value.msgId
  hideContextMenu()
  try {
    await deleteChatMessage(msgId)
    const idx = messages.value.findIndex((m) => m.id === msgId)
    if (idx !== -1) {
      messages.value.splice(idx, 1)
    }
  } catch (e) {
    console.error('删除消息失败:', e)
  }
}

watch(
  () => props.lastMessage,
  (msg) => {
    if (!msg) return
    if (msg.type === 'chat_message' && msg.data) {
      const data = msg.data as ChatMessage
      if (data.room_id === currentRoomId.value) {
        const exists = messages.value.some((m) => m.id === data.id || m.id === -data.id)
        if (!exists) {
          messages.value.push(data)
          scrollToBottom()
        } else {
          const tempIdx = messages.value.findIndex((m) => m.id === -data.id || m.id < 0)
          if (tempIdx !== -1 && data.id > 0) {
            messages.value[tempIdx] = data
          }
        }
        markRoomRead(data.room_id)
        const session = sessions.value.find((s) => s.room_id === data.room_id)
        if (session) session.unread_count = 0
      }
      loadSessions()
    } else if (msg.type === 'chat_room_created' && msg.data) {
      loadSessions()
    } else if (msg.type === 'chat_message_deleted' && msg.data) {
      const deletedId = msg.data.id
      if (deletedId) {
        const idx = messages.value.findIndex((m) => m.id === deletedId)
        if (idx !== -1) {
          messages.value.splice(idx, 1)
        }
      }
    }
  }
)

onMounted(() => {
  loadSessions()
  document.addEventListener('click', hideContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
  stopOnlineUsersPolling()
  if (currentRoomId.value) {
    ws.leaveRoom(currentRoomId.value)
  }
})

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.visible) {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>

<template>
  <Transition name="wc-window">
    <div v-show="visible" class="wc-window">
      <div class="wc-layout">
        <!-- 左栏：会话列表 -->
        <div class="wc-sidebar">
          <!-- 搜索栏 + 新建按钮 -->
          <div class="wc-sidebar__top">
            <div class="wc-sidebar__search">
              <svg
                viewBox="0 0 24 24"
                width="14"
                height="14"
                fill="none"
                stroke="#999"
                stroke-width="2"
              >
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                v-model="searchText"
                type="text"
                placeholder="搜索"
                class="wc-sidebar__search-input"
              />
            </div>
            <button
              class="wc-sidebar__add-btn"
              title="新建聊天"
              @click="showUserList = !showUserList"
            >
              <svg
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="none"
                stroke="#666"
                stroke-width="2"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          </div>

          <!-- 会话列表 -->
          <ElScrollbar class="wc-sidebar__list">
            <div
              v-for="session in filteredSessions"
              :key="session.room_id"
              class="wc-session"
              :class="{ 'wc-session--active': currentRoomId === session.room_id }"
              @click="currentRoomId = session.room_id"
            >
              <div class="wc-session__avatar">
                <ElAvatar
                  v-if="session.room_id === 'lobby'"
                  :size="40"
                  :style="{ background: '#07C160', borderRadius: '6px' }"
                  >大</ElAvatar
                >
                <ElAvatar
                  v-else-if="session.avatar"
                  :size="40"
                  :src="session.avatar"
                  :style="{ borderRadius: '6px' }"
                />
                <ElAvatar
                  v-else
                  :size="40"
                  :style="{ background: '#7EB7E5', borderRadius: '6px' }"
                  >{{ (session.room_name || '?')[0] }}</ElAvatar
                >
                <span v-if="session.unread_count > 0" class="wc-session__badge"></span>
              </div>
              <div class="wc-session__body">
                <div class="wc-session__top">
                  <span class="wc-session__name">{{ session.room_name || '未知会话' }}</span>
                  <span class="wc-session__time">{{
                    formatSessionTime(session.last_created_at)
                  }}</span>
                </div>
                <div class="wc-session__preview">
                  {{ session.last_sender_name ? session.last_sender_name + ': ' : '' }}
                  {{ session.last_content_type === 'file' ? '[文件]' : session.last_content || '' }}
                </div>
              </div>
            </div>

            <div v-if="filteredSessions.length === 0" class="wc-sidebar__empty">暂无会话</div>
          </ElScrollbar>
        </div>

        <!-- 右栏：聊天主窗口 -->
        <div class="wc-main">
          <!-- 新建聊天用户列表（覆盖层） -->
          <Transition name="wc-slide">
            <div v-if="showUserList" class="wc-user-panel">
              <div class="wc-user-panel__header">
                <span>选择联系人</span>
                <button class="wc-icon-btn" @click="showUserList = false">
                  <svg
                    viewBox="0 0 24 24"
                    width="14"
                    height="14"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
              <div class="wc-user-panel__list">
                <div
                  v-for="u in onlineUsers"
                  :key="u.id"
                  class="wc-user-panel__item"
                  @click="startChat(u.id)"
                >
                  <ElAvatar v-if="u.avatar" :size="36" :src="u.avatar" style="border-radius: 6px" />
                  <ElAvatar v-else :size="36" style="background: #7eb7e5; border-radius: 6px">{{
                    u.username[0]
                  }}</ElAvatar>
                  <span class="wc-user-panel__name">{{ u.username }}</span>
                </div>
                <div v-if="onlineUsers.length === 0" class="wc-user-panel__empty">暂无在线用户</div>
              </div>
            </div>
          </Transition>

          <template v-if="currentRoomId">
            <!-- 顶部标题栏 -->
            <div class="wc-main__header">
              <span class="wc-main__header-name">{{ currentSession?.room_name || '聊天' }}</span>
              <div class="wc-main__header-actions">
                <button class="wc-icon-btn" title="视频通话">
                  <svg
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#666"
                    stroke-width="2"
                  >
                    <polygon points="23 7 16 12 23 17 23 7" />
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="语音通话">
                  <svg
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#666"
                    stroke-width="2"
                  >
                    <path
                      d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72 12.84 12.84 0 00.7 2.81 2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45 12.84 12.84 0 002.81.7A2 2 0 0122 16.92z"
                    />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="更多">
                  <svg
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#666"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="1" />
                    <circle cx="19" cy="12" r="1" />
                    <circle cx="5" cy="12" r="1" />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="关闭" @click="emit('close')">
                  <svg
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#666"
                    stroke-width="2"
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- 消息区域 -->
            <ElScrollbar ref="messageScrollbar" class="wc-main__messages" @scroll="handleScroll">
              <div class="wc-msg-list">
                <template v-for="(msg, idx) in messages" :key="msg.id">
                  <div v-if="shouldShowTimeDivider(idx)" class="wc-time-divider">
                    {{ formatTimeDivider(msg.created_at) }}
                  </div>
                  <div
                    class="wc-msg"
                    :class="{ 'wc-msg--self': msg.sender_id === currentUserId }"
                    @contextmenu="showContextMenu($event, msg.id)"
                  >
                    <div class="wc-msg__avatar">
                      <ElAvatar
                        v-if="msg.sender_avatar"
                        :size="38"
                        :src="msg.sender_avatar"
                        :style="{ borderRadius: '6px' }"
                      />
                      <ElAvatar
                        v-else
                        :size="38"
                        :style="{ background: '#7EB7E5', borderRadius: '6px' }"
                      >
                        {{ msg.sender_name?.[0] || '?' }}
                      </ElAvatar>
                    </div>
                    <div class="wc-msg__body">
                      <div v-if="msg.content_type === 'text'" class="wc-msg__bubble">{{
                        msg.content
                      }}</div>
                      <div v-else class="wc-msg__bubble wc-msg__bubble--file">
                        <a :href="msg.content" target="_blank" rel="noopener">
                          <svg
                            viewBox="0 0 24 24"
                            width="14"
                            height="14"
                            fill="none"
                            stroke="currentColor"
                            stroke-width="2"
                            style="vertical-align: middle; margin-right: 4px"
                          >
                            <path
                              d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"
                            /></svg
                          >文件
                        </a>
                      </div>
                      <span class="wc-msg__time">{{ formatMsgTime(msg.created_at) }}</span>
                    </div>
                  </div>
                </template>
              </div>
            </ElScrollbar>

            <!-- 输入区域 -->
            <div class="wc-main__input-area">
              <div class="wc-main__toolbar">
                <button class="wc-icon-btn" title="表情">
                  <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="#666"
                    stroke-width="1.8"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                    <line x1="9" y1="9" x2="9.01" y2="9" />
                    <line x1="15" y1="9" x2="15.01" y2="9" />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="上传文件" @click="fileInput?.click()">
                  <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="#666"
                    stroke-width="1.8"
                  >
                    <path
                      d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
                    />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="截图">
                  <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="#666"
                    stroke-width="1.8"
                  >
                    <path d="M17 3H5a2 2 0 00-2 2v14a2 2 0 002 2h14c1.1 0 2-.9 2-2V7l-4-4z" />
                    <polyline points="15 3 15 7 19 7" />
                    <line x1="9" y1="13" x2="15" y2="13" />
                  </svg>
                </button>
                <button class="wc-icon-btn" title="语音消息">
                  <svg
                    viewBox="0 0 24 24"
                    width="20"
                    height="20"
                    fill="none"
                    stroke="#666"
                    stroke-width="1.8"
                  >
                    <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
                    <path d="M19 10v2a7 7 0 01-14 0v-2" />
                    <line x1="12" y1="19" x2="12" y2="23" />
                    <line x1="8" y1="23" x2="16" y2="23" />
                  </svg>
                </button>
              </div>
              <div class="wc-main__input-box">
                <textarea
                  v-model="inputText"
                  class="wc-main__textarea"
                  placeholder=""
                  rows="3"
                  @keydown="handleKeyDown"
                ></textarea>
              </div>
              <div class="wc-main__send-row">
                <button class="wc-send-btn" :disabled="!inputText.trim()" @click="handleSend"
                  >发送</button
                >
              </div>
            </div>

            <input ref="fileInput" type="file" style="display: none" @change="handleFileUpload" />
          </template>

          <!-- 未选择会话 -->
          <div v-else class="wc-main__placeholder">
            <svg
              viewBox="0 0 24 24"
              width="56"
              height="56"
              fill="none"
              stroke="#c0c4cc"
              stroke-width="1"
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            <p>选择会话开始聊天</p>
          </div>
        </div>
      </div>

      <!-- 右键菜单 -->
      <Transition name="wc-menu">
        <div
          v-if="contextMenu.visible"
          class="wc-context-menu"
          :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
          @click.stop
        >
          <div class="wc-context-menu__item" @click="handleDeleteMessage">
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="3 6 5 6 21 6" />
              <path
                d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
              /></svg
            ><span>删除</span>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style lang="less" scoped>
.wc-window {
  position: fixed;
  right: 24px;
  bottom: 90px;
  width: 720px;
  height: 560px;
  background: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.18);
  z-index: 9998;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid #d9d9d9;

  @media (max-width: 768px) {
    width: 100vw;
    height: 100vh;
    right: 0;
    bottom: 0;
    border-radius: 0;
  }
}

.wc-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ==================== 左栏：会话列表 ==================== */
.wc-sidebar {
  width: 272px;
  min-width: 272px;
  background: #f0f0f0;
  border-right: 1px solid #d6d6d6;
  display: flex;
  flex-direction: column;

  &__top {
    display: flex;
    align-items: center;
    padding: 10px 8px;
    gap: 6px;
  }

  &__search {
    display: flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    padding: 5px 10px;
    background: #e6e6e6;
    border-radius: 4px;
  }

  &__search-input {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    font-size: 13px;
    color: #333;

    &::placeholder {
      color: #999;
    }
  }

  &__add-btn {
    width: 28px;
    height: 28px;
    border-radius: 4px;
    border: none;
    background: transparent;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666;
    transition: background 0.15s;
    flex-shrink: 0;

    &:hover {
      background: #ddd;
    }
  }

  &__list {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  &__empty {
    padding: 32px;
    text-align: center;
    color: #999;
    font-size: 13px;
  }
}

/* 会话列表项 */
.wc-session {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  cursor: pointer;
  gap: 10px;
  transition: all 0.12s ease;
  position: relative;

  &:hover {
    background: #e8e8e8;
  }

  &--active {
    background: #1aad19 !important;

    .wc-session__name {
      color: #fff;
      font-weight: 600;
    }

    .wc-session__time {
      color: rgba(255, 255, 255, 0.75);
    }

    .wc-session__preview {
      color: rgba(255, 255, 255, 0.85);
    }
  }

  &__avatar {
    position: relative;
    flex-shrink: 0;
  }

  &__badge {
    position: absolute;
    top: -2px;
    right: -2px;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #fa5151;
    border: 2px solid #f0f0f0;
  }

  &__body {
    flex: 1;
    overflow: hidden;
    min-width: 0;
  }

  &__top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 3px;
  }

  &__name {
    font-size: 14px;
    font-weight: 500;
    color: #191919;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  &__time {
    font-size: 11px;
    color: #b2b2b2;
    flex-shrink: 0;
    margin-left: 8px;
  }

  &__preview {
    font-size: 12px;
    color: #b2b2b2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

/* ==================== 右栏：聊天主窗口 ==================== */
.wc-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  background: #f5f5f5;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: #f5f5f5;
    border-bottom: 1px solid #d6d6d6;
    flex-shrink: 0;
  }

  &__header-name {
    font-size: 16px;
    font-weight: 500;
    color: #191919;
  }

  &__header-actions {
    display: flex;
    gap: 2px;
  }

  &__messages {
    flex: 1;
    min-height: 0;
    background: #ededed;
    overflow: hidden;

    :deep(.el-scrollbar__wrap) {
      overflow-x: hidden;
    }

    :deep(.el-scrollbar__view) {
      min-height: 100%;
    }
  }

  &__placeholder {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #999;
    gap: 12px;

    p {
      font-size: 14px;
    }
  }

  &__input-area {
    background: #f5f5f5;
    border-top: 1px solid #d6d6d6;
    flex-shrink: 0;
    padding: 6px 16px 10px;
  }

  &__toolbar {
    display: flex;
    gap: 2px;
    padding-bottom: 4px;
  }

  &__input-box {
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px 8px;
  }

  &__textarea {
    width: 100%;
    min-height: 64px;
    max-height: 120px;
    border: none;
    outline: none;
    background: transparent;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
    resize: none;
    font-family: inherit;

    &::placeholder {
      color: #bfbfbf;
    }
  }

  &__send-row {
    display: flex;
    justify-content: flex-end;
    padding-top: 6px;
  }
}

/* 发送按钮 */
.wc-send-btn {
  padding: 5px 28px;
  background: #07c160;
  color: #fff;
  border: 1px solid #07c160;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;

  &:hover:not(:disabled) {
    background: #06ad56;
  }

  &:disabled {
    background: #a0e8b8;
    border-color: #a0e8b8;
    cursor: not-allowed;
  }
}

/* 图标按钮 */
.wc-icon-btn {
  width: 30px;
  height: 30px;
  border-radius: 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  color: #666;

  &:hover {
    background: #e0e0e0;
  }
}

/* ==================== 消息气泡 ==================== */
.wc-msg-list {
  padding: 12px 20px;
}

.wc-time-divider {
  text-align: center;
  padding: 10px 0;
  font-size: 12px;
  color: #999;
}

.wc-msg {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  align-items: flex-start;

  &--self {
    flex-direction: row-reverse;

    .wc-msg__bubble {
      background: #95ec69;
      color: #000;

      &--file a {
        color: #333;
      }
    }

    .wc-msg__time {
      float: left;
      margin-left: 8px;
    }
  }

  &__avatar {
    flex-shrink: 0;
    margin-top: 2px;
  }

  &__body {
    max-width: 420px;
    position: relative;
    min-width: 0;
  }

  &__bubble {
    background: #fff;
    color: #191919;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 14px;
    line-height: 1.55;
    word-break: break-word;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);

    &--file a {
      color: #576b95;
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }
  }

  &__time {
    display: block;
    font-size: 11px;
    color: #b2b2b2;
    margin-top: 4px;
    float: right;
    margin-left: 8px;
  }
}

/* ==================== 新建聊天用户面板 ==================== */
.wc-user-panel {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: #f5f5f5;
  z-index: 10;
  display: flex;
  flex-direction: column;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid #d6d6d6;
    font-size: 14px;
    color: #333;
    font-weight: 500;
  }

  &__list {
    flex: 1;
    overflow-y: auto;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 16px;
    cursor: pointer;
    transition: background 0.15s;

    &:hover {
      background: #ebebeb;
    }
  }

  &__name {
    font-size: 14px;
    color: #333;
  }

  &__empty {
    padding: 32px;
    text-align: center;
    color: #999;
    font-size: 13px;
  }
}

/* ==================== 右键菜单 ==================== */
.wc-context-menu {
  position: fixed;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 100px;
  padding: 4px 0;

  &__item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 13px;
    color: #333;
    transition: background 0.15s;

    &:hover {
      background: #f5f5f5;
    }
  }
}

/* ==================== 动画 ==================== */
.chat-window-enter-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-window-leave-active {
  transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-window-enter-from {
  opacity: 0;
  transform: scale(0.96) translateY(16px);
}

.chat-window-leave-to {
  opacity: 0;
  transform: scale(0.96) translateY(8px);
}

.wc-slide-enter-active {
  transition: all 0.2s ease-out;
}

.wc-slide-leave-active {
  transition: all 0.15s ease-in;
}

.wc-slide-enter-from {
  opacity: 0;
  transform: translateX(-16px);
}

.wc-slide-leave-to {
  opacity: 0;
  transform: translateX(-16px);
}

.wc-menu-enter-active {
  transition: opacity 0.1s ease-out;
}

.wc-menu-leave-active {
  transition: opacity 0.08s ease-in;
}

.wc-menu-enter-from,
.wc-menu-leave-to {
  opacity: 0;
}
</style>
