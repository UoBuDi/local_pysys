<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElScrollbar, ElAvatar, ElDialog, ElPopover, ElMessage } from 'element-plus'
import {
  sendMessage,
  getChatHistory,
  markRoomRead,
  getChatSessions,
  createChatRoom,
  getOnlineUsers,
  uploadChatFile,
  uploadChatImage,
  deleteChatMessage,
  searchMessages,
  recallMessage,
  getReadStatus,
  updateSessionSettings,
  getGroupMembers,
  addGroupMembers,
  updateGroupName,
  leaveGroup,
  exportChatHistory,
  type ChatMessage,
  type ChatSession,
  type OnlineUser,
  type GroupMember,
  type ReadStatus
} from '@/api/chat'
import { useWebSocket, type WsMessage } from '@/utils/websocket'
import { useUserStore } from '@/store/modules/user'

const ws = useWebSocket()
const userStore = useUserStore()
const currentUserId = computed(() => userStore.getUserInfo?.id || 0)

/* ==================== 核心状态 ==================== */
const sessions = ref<ChatSession[]>([])
const currentRoomId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const onlineUsers = ref<OnlineUser[]>([])
const showUserList = ref(false)
const messageScrollbar = ref<InstanceType<typeof ElScrollbar> | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const imageInput = ref<HTMLInputElement | null>(null)
const searchText = ref('')

/* ==================== CH-01: 消息搜索 ==================== */
const showSearchPanel = ref(false)
const searchKeyword = ref('')
const searchResults = ref<
  Array<{
    message_id: number
    room_id: string
    room_name: string
    sender_name: string
    content: string
    created_at: string
  }>
>([])
const searchLoading = ref(false)

const handleSearch = async () => {
  const kw = searchKeyword.value.trim()
  if (!kw) return
  searchLoading.value = true
  try {
    const resp = await searchMessages(kw)
    if (resp?.code === 200 && resp.data) {
      searchResults.value = resp.data
    }
  } catch (e) {
    console.error('搜索消息失败:', e)
  } finally {
    searchLoading.value = false
  }
}

const jumpToSearchResult = async (result: { room_id: string }) => {
  await selectRoom(result.room_id)
  showSearchPanel.value = false
  searchKeyword.value = ''
  searchResults.value = []
}

/* ==================== CH-02: 群聊管理 ==================== */
const showCreateGroup = ref(false)
const groupName = ref('')
const groupMemberIds = ref<number[]>([])
const showGroupInfo = ref(false)
const groupMembers = ref<GroupMember[]>([])
const showAddMember = ref(false)
const addMemberIds = ref<number[]>([])
const showRenameGroup = ref(false)
const renameGroupName = ref('')

const handleCreateGroup = async () => {
  if (!groupName.value.trim()) {
    ElMessage.warning('请输入群名称')
    return
  }
  if (groupMemberIds.value.length === 0) {
    ElMessage.warning('请选择群成员')
    return
  }
  try {
    const resp = await createChatRoom({
      target_user_id: groupMemberIds.value[0],
      room_type: 'group',
      room_name: groupName.value.trim(),
      member_ids: groupMemberIds.value.join(',')
    })
    if (resp?.code === 200 && resp.data) {
      await loadSessions()
      await selectRoom(resp.data.room_id)
      showCreateGroup.value = false
      groupName.value = ''
      groupMemberIds.value = []
      showUserList.value = false
      ElMessage.success('群聊创建成功')
    }
  } catch (e) {
    console.error('创建群聊失败:', e)
  }
}

const loadGroupMembers = async () => {
  if (!currentRoomId.value) return
  try {
    const resp = await getGroupMembers(currentRoomId.value)
    if (resp?.code === 200 && resp.data) {
      groupMembers.value = resp.data
    }
  } catch (e) {
    console.error('加载群成员失败:', e)
  }
}

const openGroupInfo = () => {
  if (!currentSession.value || currentSession.value.room_type !== 'group') return
  loadGroupMembers()
  showGroupInfo.value = true
}

const handleAddMembers = async () => {
  if (!currentRoomId.value || addMemberIds.value.length === 0) return
  try {
    const resp = await addGroupMembers(currentRoomId.value, addMemberIds.value.join(','))
    if (resp?.code === 200) {
      ElMessage.success('添加成员成功')
      addMemberIds.value = []
      showAddMember.value = false
      loadGroupMembers()
    }
  } catch (e) {
    console.error('添加群成员失败:', e)
  }
}

const handleRenameGroup = async () => {
  if (!currentRoomId.value || !renameGroupName.value.trim()) return
  try {
    const resp = await updateGroupName(currentRoomId.value, renameGroupName.value.trim())
    if (resp?.code === 200) {
      ElMessage.success('群名称修改成功')
      showRenameGroup.value = false
      if (currentSession.value) {
        currentSession.value.room_name = renameGroupName.value.trim()
      }
      await loadSessions()
    }
  } catch (e) {
    console.error('修改群名称失败:', e)
  }
}

const handleLeaveGroup = async () => {
  if (!currentRoomId.value) return
  try {
    const resp = await leaveGroup(currentRoomId.value)
    if (resp?.code === 200) {
      ElMessage.success('已退出群聊')
      showGroupInfo.value = false
      currentRoomId.value = null
      messages.value = []
      await loadSessions()
    }
  } catch (e) {
    console.error('退出群聊失败:', e)
  }
}

/* ==================== CH-03: 消息撤回 ==================== */
const contextMenu = ref<{
  visible: boolean
  x: number
  y: number
  msgId: number
  isOwn: boolean
  msgTime: string
}>({ visible: false, x: 0, y: 0, msgId: 0, isOwn: false, msgTime: '' })

const canRecall = computed(() => {
  if (!contextMenu.value.isOwn || !contextMenu.value.msgTime) return false
  const msgTime = new Date(contextMenu.value.msgTime).getTime()
  return Date.now() - msgTime < 2 * 60 * 1000
})

const handleRecallMessage = async () => {
  const msgId = contextMenu.value.msgId
  hideContextMenu()
  try {
    const resp = await recallMessage(msgId)
    if (resp?.code === 200) {
      const msg = messages.value.find((m) => m.id === msgId)
      if (msg) msg.is_recalled = 1
      ElMessage.success('消息已撤回')
    }
  } catch (e) {
    console.error('撤回消息失败:', e)
  }
}

/* ==================== CH-04: 图片消息 ==================== */
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

const handleImageUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file || !currentRoomId.value) return

  // 仅接受图片格式
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请选择图片文件')
    target.value = ''
    return
  }

  try {
    await uploadChatImage(file, currentRoomId.value)
    await loadSessions()
  } catch (e) {
    console.error('上传图片失败:', e)
  } finally {
    target.value = ''
  }
}

const openImagePreview = (url: string) => {
  imagePreviewUrl.value = url
  imagePreviewVisible.value = true
}

/* ==================== CH-05: 已读回执 ==================== */
const readStatusMap = ref<Map<number, ReadStatus>>(new Map())
const readPopoverMsgId = ref<number | null>(null)

const loadReadStatus = async (msgId: number) => {
  if (!currentRoomId.value) return
  try {
    const resp = await getReadStatus(currentRoomId.value, msgId)
    if (resp?.code === 200 && resp.data) {
      readStatusMap.value.set(msgId, resp.data)
    }
  } catch (e) {
    console.error('获取已读状态失败:', e)
  }
}

const getReadBadgeText = (msg: ChatMessage) => {
  const status = readStatusMap.value.get(msg.id)
  if (!status) return ''
  return `${status.read_count}/${status.total_count} 已读`
}

const showReadPopover = (msgId: number) => {
  readPopoverMsgId.value = msgId
  loadReadStatus(msgId)
}

/* ==================== CH-06: 聊天导出 ==================== */
const showExportMenu = ref(false)

const handleExport = async (format: string) => {
  if (!currentRoomId.value) return
  showExportMenu.value = false
  try {
    const resp = await exportChatHistory(currentRoomId.value, format)
    if (resp) {
      const content = typeof resp === 'string' ? resp : resp.data || JSON.stringify(resp)
      const blob = new Blob([content], {
        type: format === 'html' ? 'text/html' : 'text/plain;charset=utf-8'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `chat_${currentRoomId.value}.${format === 'html' ? 'html' : 'txt'}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      ElMessage.success('导出成功')
    }
  } catch (e) {
    console.error('导出聊天记录失败:', e)
  }
}

/* ==================== CH-07: 置顶/免打扰 ==================== */
const sessionContextMenu = ref<{
  visible: boolean
  x: number
  y: number
  roomId: string
  isPinned: boolean
  isMuted: boolean
}>({ visible: false, x: 0, y: 0, roomId: '', isPinned: false, isMuted: false })

const showSessionContextMenu = (e: MouseEvent, session: ChatSession) => {
  e.preventDefault()
  e.stopPropagation()
  sessionContextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    roomId: session.room_id,
    isPinned: !!session.is_pinned,
    isMuted: !!session.is_muted
  }
}

const hideSessionContextMenu = () => {
  sessionContextMenu.value.visible = false
}

const handleTogglePin = async () => {
  const { roomId, isPinned } = sessionContextMenu.value
  hideSessionContextMenu()
  try {
    const resp = await updateSessionSettings({ room_id: roomId, is_pinned: isPinned ? 0 : 1 })
    if (resp?.code === 200) {
      const session = sessions.value.find((s) => s.room_id === roomId)
      if (session) session.is_pinned = isPinned ? 0 : 1
      ElMessage.success(isPinned ? '已取消置顶' : '已置顶')
    }
  } catch (e) {
    console.error('更新会话设置失败:', e)
  }
}

const handleToggleMute = async () => {
  const { roomId, isMuted } = sessionContextMenu.value
  hideSessionContextMenu()
  try {
    const resp = await updateSessionSettings({ room_id: roomId, is_muted: isMuted ? 0 : 1 })
    if (resp?.code === 200) {
      const session = sessions.value.find((s) => s.room_id === roomId)
      if (session) session.is_muted = isMuted ? 0 : 1
      ElMessage.success(isMuted ? '已取消免打扰' : '已设为免打扰')
    }
  } catch (e) {
    console.error('更新会话设置失败:', e)
  }
}

/* ==================== CH-08: @提及 ==================== */
const showMentionDropdown = ref(false)
const mentionFilter = ref('')
const mentionStartIndex = ref(-1)
const mentionSelectedIndex = ref(0)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const groupMemberUsers = computed(() => {
  return groupMembers.value.map((m) => ({
    id: m.user_id,
    username: m.username,
    avatar: m.avatar
  }))
})

const mentionCandidates = computed(() => {
  const list =
    currentSession.value?.room_type === 'group' ? groupMemberUsers.value : onlineUsers.value
  if (!mentionFilter.value) return list
  const kw = mentionFilter.value.toLowerCase()
  return list.filter((u) => u.username.toLowerCase().includes(kw))
})

const handleTextareaInput = (e: Event) => {
  const textarea = e.target as HTMLTextAreaElement
  const text = textarea.value
  const cursorPos = textarea.selectionStart

  // 检测是否正在输入 @mention
  const textBeforeCursor = text.substring(0, cursorPos)
  const atMatch = textBeforeCursor.match(/@([^\s@]*)$/)

  if (atMatch && currentSession.value?.room_type === 'group') {
    mentionStartIndex.value = textBeforeCursor.lastIndexOf('@')
    mentionFilter.value = atMatch[1]
    showMentionDropdown.value = true
    mentionSelectedIndex.value = 0
  } else {
    showMentionDropdown.value = false
    mentionStartIndex.value = -1
    mentionFilter.value = ''
  }
}

const selectMention = (user: { id: number; username: string }) => {
  if (!textareaRef.value || mentionStartIndex.value < 0) return
  const text = inputText.value
  const before = text.substring(0, mentionStartIndex.value)
  const after = text.substring(textareaRef.value.selectionStart)
  inputText.value = before + `@${user.username} ` + after

  showMentionDropdown.value = false
  mentionStartIndex.value = -1
  mentionFilter.value = ''

  nextTick(() => {
    if (textareaRef.value) {
      const newPos = before.length + user.username.length + 2
      textareaRef.value.focus()
      textareaRef.value.setSelectionRange(newPos, newPos)
    }
  })
}

const handleMentionKeydown = (e: KeyboardEvent) => {
  if (!showMentionDropdown.value) return
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    mentionSelectedIndex.value = Math.min(
      mentionSelectedIndex.value + 1,
      mentionCandidates.value.length - 1
    )
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    mentionSelectedIndex.value = Math.max(mentionSelectedIndex.value - 1, 0)
  } else if (e.key === 'Enter' && mentionCandidates.value.length > 0) {
    e.preventDefault()
    selectMention(mentionCandidates.value[mentionSelectedIndex.value])
  } else if (e.key === 'Escape') {
    showMentionDropdown.value = false
  }
}

/* ==================== 计算属性 ==================== */
const currentSession = computed(() => sessions.value.find((s) => s.room_id === currentRoomId.value))

const sortedSessions = computed(() => {
  const pinned = sessions.value.filter((s) => s.is_pinned)
  const unpinned = sessions.value.filter((s) => !s.is_pinned)
  return [...pinned, ...unpinned]
})

const filteredSessions = computed(() => {
  const list = sortedSessions.value
  if (!searchText.value.trim()) return list
  const kw = searchText.value.trim().toLowerCase()
  return list.filter(
    (s) =>
      (s.room_name || '').toLowerCase().includes(kw) ||
      (s.last_content || '').toLowerCase().includes(kw)
  )
})

/* ==================== 核心方法 ==================== */
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
    const resp = await getChatHistory(roomId, 100)
    if (resp?.code === 200 && resp.data) {
      messages.value = resp.data
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    console.error('加载消息失败:', e)
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

const selectRoom = async (roomId: string) => {
  currentRoomId.value = roomId
  await loadMessages(roomId)
  await markRoomRead(roomId)
  const session = sessions.value.find((s) => s.room_id === roomId)
  if (session) session.unread_count = 0

  // 群聊加载成员列表供 @提及 使用
  if (session?.room_type === 'group') {
    loadGroupMembers()
  }

  // 加载已读回执
  loadAllReadStatus()
}

const loadAllReadStatus = async () => {
  if (!currentRoomId.value) return
  const ownMsgs = messages.value.filter((m) => m.sender_id === currentUserId.value)
  for (const msg of ownMsgs.slice(-20)) {
    try {
      const resp = await getReadStatus(currentRoomId.value, msg.id)
      if (resp?.code === 200 && resp.data) {
        readStatusMap.value.set(msg.id, resp.data)
      }
    } catch {
      // 静默处理
    }
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || !currentRoomId.value) return

  // CH-08: 解析 @提及
  const mentionRegex = /@(\S+)/g
  const mentionedIds: number[] = []
  let match: RegExpExecArray | null
  while ((match = mentionRegex.exec(text)) !== null) {
    const username = match[1]
    const user =
      onlineUsers.value.find((u) => u.username === username) ||
      groupMemberUsers.value.find((u) => u.username === username)
    if (user && !mentionedIds.includes(user.id)) {
      mentionedIds.push(user.id)
    }
  }

  try {
    await sendMessage({
      room_id: currentRoomId.value,
      content_type: 'text',
      content: text,
      mentioned_user_ids: mentionedIds.length > 0 ? mentionedIds.join(',') : undefined
    })
    inputText.value = ''
    await loadSessions()
  } catch (e) {
    console.error('发送消息失败:', e)
  }
}

const handleKeyDown = (e: KeyboardEvent) => {
  // @提及下拉框拦截方向键和回车
  if (showMentionDropdown.value) {
    handleMentionKeydown(e)
    if (e.defaultPrevented) return
  }
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
      await loadSessions()
      await selectRoom(resp.data.room_id)
      showUserList.value = false
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

/* ==================== 工具方法 ==================== */
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

/* 渲染带 @mention 高亮的文本 */
const renderMentionText = (content: string) => {
  const parts: Array<{ text: string; isMention: boolean }> = []
  const regex = /@(\S+)/g
  let lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ text: content.substring(lastIndex, match.index), isMention: false })
    }
    parts.push({ text: match[0], isMention: true })
    lastIndex = regex.lastIndex
  }
  if (lastIndex < content.length) {
    parts.push({ text: content.substring(lastIndex), isMention: false })
  }
  return parts
}

/* ==================== 右键菜单 ==================== */
const showContextMenu = (e: MouseEvent, msg: ChatMessage) => {
  e.preventDefault()
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    msgId: msg.id,
    isOwn: msg.sender_id === currentUserId.value,
    msgTime: msg.created_at
  }
}

const hideContextMenu = () => {
  contextMenu.value.visible = false
}

const handleDeleteMessage = async () => {
  const msgId = contextMenu.value.msgId
  hideContextMenu()
  try {
    const resp = await deleteChatMessage(msgId)
    if (resp?.code === 200) {
      const idx = messages.value.findIndex((m) => m.id === msgId)
      if (idx !== -1) messages.value.splice(idx, 1)
    }
  } catch (e) {
    console.error('删除消息失败:', e)
  }
}

/* ==================== WebSocket 事件处理 ==================== */
const onWsChat = (msg: WsMessage) => {
  if (msg.type === 'chat_message' && msg.data) {
    const data = msg.data as ChatMessage
    if (data.room_id === currentRoomId.value) {
      const exists = messages.value.some((m) => m.id === data.id)
      if (!exists) {
        messages.value.push(data)
        scrollToBottom()
      }
      markRoomRead(data.room_id)
    }
    loadSessions()
  } else if (msg.type === 'chat_room_created' && msg.data) {
    loadSessions()
  } else if (msg.type === 'chat_message_deleted' && msg.data) {
    const idx = messages.value.findIndex((m) => m.id === msg.data.message_id)
    if (idx !== -1) messages.value.splice(idx, 1)
  } else if (msg.type === 'chat_message_recalled' && msg.data) {
    // CH-03: 消息撤回实时更新
    const target = messages.value.find((m) => m.id === msg.data.message_id)
    if (target) target.is_recalled = 1
  } else if (msg.type === 'chat_message_read' && msg.data) {
    // CH-05: 已读状态实时更新
    const { message_id, read_count, total_count, readers } = msg.data
    if (message_id) {
      readStatusMap.value.set(message_id, {
        message_id,
        read_count,
        total_count,
        readers: readers || []
      })
    }
  } else if (msg.type === 'chat_mentioned' && msg.data) {
    // CH-08: @提及通知
    const { room_name, sender_name } = msg.data
    ElMessage.info(`${sender_name} 在 ${room_name || '群聊'} 中@了你`)
    loadSessions()
  } else if (msg.type === 'chat_group_renamed' && msg.data) {
    // CH-02: 群名变更
    const { room_id, room_name } = msg.data
    const session = sessions.value.find((s) => s.room_id === room_id)
    if (session) session.room_name = room_name
    if (currentRoomId.value === room_id && currentSession.value) {
      currentSession.value.room_name = room_name
    }
  }
}

/* ==================== 生命周期 ==================== */
let removeChatCallback: (() => void) | null = null

onMounted(() => {
  loadSessions()
  loadOnlineUsers()
  removeChatCallback = ws.onChat(onWsChat)
  document.addEventListener('click', hideContextMenu)
  document.addEventListener('click', hideSessionContextMenu)
})

onUnmounted(() => {
  if (removeChatCallback) {
    removeChatCallback()
    removeChatCallback = null
  }
  document.removeEventListener('click', hideContextMenu)
  document.removeEventListener('click', hideSessionContextMenu)
})
</script>

<template>
  <div class="wc-page">
    <div class="wc-page__layout">
      <!-- 左栏：会话列表 -->
      <div class="wc-page__sidebar">
        <!-- 搜索栏 + 新建按钮 -->
        <div class="wc-page__sidebar-top">
          <div class="wc-page__search">
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
              class="wc-page__search-input"
            />
            <!-- CH-01: 消息搜索按钮 -->
            <button
              class="wc-page__icon-btn--sm"
              title="搜索消息"
              @click="showSearchPanel = !showSearchPanel"
            >
              <svg
                viewBox="0 0 24 24"
                width="12"
                height="12"
                fill="none"
                stroke="#999"
                stroke-width="2"
              >
                <path d="M4 4h16v16H4z" />
                <line x1="8" y1="9" x2="16" y2="9" />
                <line x1="8" y1="13" x2="13" y2="13" />
              </svg>
            </button>
          </div>
          <button class="wc-page__add-btn" title="新建聊天" @click="showUserList = !showUserList">
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

        <!-- CH-01: 消息搜索面板 -->
        <Transition name="wc-slide">
          <div v-if="showSearchPanel" class="wc-page__search-panel">
            <div class="wc-page__search-panel-header">
              <span>搜索消息</span>
              <button class="wc-page__icon-btn" @click="showSearchPanel = false">
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
            <div class="wc-page__search-panel-input">
              <input
                v-model="searchKeyword"
                type="text"
                placeholder="输入关键词搜索消息"
                class="wc-page__search-panel-field"
                @keydown.enter="handleSearch"
              />
              <button
                class="wc-page__search-panel-btn"
                @click="handleSearch"
                :disabled="searchLoading"
              >
                {{ searchLoading ? '搜索中...' : '搜索' }}
              </button>
            </div>
            <div class="wc-page__search-panel-results">
              <div
                v-for="result in searchResults"
                :key="result.message_id"
                class="wc-page__search-result-item"
                @click="jumpToSearchResult(result)"
              >
                <div class="wc-page__search-result-room">{{ result.room_name }}</div>
                <div class="wc-page__search-result-sender">{{ result.sender_name }}</div>
                <div class="wc-page__search-result-content">{{ result.content }}</div>
              </div>
              <div
                v-if="searchResults.length === 0 && searchKeyword && !searchLoading"
                class="wc-page__empty-text"
              >
                未找到相关消息
              </div>
            </div>
          </div>
        </Transition>

        <!-- 新建聊天用户选择 -->
        <Transition name="wc-slide">
          <div v-if="showUserList && !showSearchPanel" class="wc-page__user-picker">
            <div class="wc-page__user-picker-header">
              <span>选择联系人</span>
              <button class="wc-page__icon-btn" @click="showUserList = false">
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
            <!-- CH-02: 创建群聊按钮 -->
            <button class="wc-page__create-group-btn" @click="showCreateGroup = true">
              <svg
                viewBox="0 0 24 24"
                width="16"
                height="16"
                fill="none"
                stroke="#07c160"
                stroke-width="2"
              >
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 00-3-3.87" />
                <path d="M16 3.13a4 4 0 010 7.75" />
              </svg>
              <span>创建群聊</span>
            </button>
            <div class="wc-page__user-picker-list">
              <div
                v-for="u in onlineUsers"
                :key="u.id"
                class="wc-page__user-item"
                @click="startChat(u.id)"
              >
                <ElAvatar v-if="u.avatar" :size="36" :src="u.avatar" style="border-radius: 6px" />
                <ElAvatar v-else :size="36" style="background: #7eb7e5; border-radius: 6px">{{
                  u.username[0]
                }}</ElAvatar>
                <span class="wc-page__user-name">{{ u.username }}</span>
              </div>
              <div v-if="onlineUsers.length === 0" class="wc-page__empty-text">暂无在线用户</div>
            </div>
          </div>
        </Transition>

        <!-- 会话列表 -->
        <ElScrollbar v-if="!showUserList && !showSearchPanel" class="wc-page__session-list">
          <div
            v-for="session in filteredSessions"
            :key="session.room_id"
            class="wc-page__session"
            :class="{ 'wc-page__session--active': currentRoomId === session.room_id }"
            @click="selectRoom(session.room_id)"
            @contextmenu="showSessionContextMenu($event, session)"
          >
            <div class="wc-page__session-avatar">
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
              <ElAvatar v-else :size="40" :style="{ background: '#7EB7E5', borderRadius: '6px' }">{{
                (session.room_name || '?')[0]
              }}</ElAvatar>
              <!-- CH-07: 未读角标（免打扰时不显示） -->
              <span
                v-if="session.unread_count > 0 && !session.is_muted"
                class="wc-page__session-badge"
                >{{ session.unread_count > 99 ? '99+' : session.unread_count }}</span
              >
              <!-- CH-07: 免打扰角标 -->
              <span
                v-if="session.is_muted && session.unread_count > 0"
                class="wc-page__session-badge--muted"
              ></span>
            </div>
            <div class="wc-page__session-body">
              <div class="wc-page__session-top">
                <div class="wc-page__session-name-row">
                  <!-- CH-07: 置顶图标 -->
                  <svg
                    v-if="session.is_pinned"
                    viewBox="0 0 24 24"
                    width="12"
                    height="12"
                    fill="#07c160"
                    stroke="none"
                    class="wc-page__session-pin-icon"
                  >
                    <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
                  </svg>
                  <!-- CH-07: 免打扰图标 -->
                  <svg
                    v-if="session.is_muted"
                    viewBox="0 0 24 24"
                    width="12"
                    height="12"
                    fill="none"
                    stroke="#b2b2b2"
                    stroke-width="2"
                    class="wc-page__session-mute-icon"
                  >
                    <path d="M11 5L6 9H2v6h4l5 4V5z" />
                    <line x1="23" y1="9" x2="17" y2="15" />
                    <line x1="17" y1="9" x2="23" y2="15" />
                  </svg>
                  <span class="wc-page__session-name">{{ session.room_name || '未知会话' }}</span>
                </div>
                <span class="wc-page__session-time">{{
                  formatSessionTime(session.last_created_at)
                }}</span>
              </div>
              <div class="wc-page__session-preview">
                {{ session.last_sender_name ? session.last_sender_name + ': ' : '' }}
                {{
                  session.last_content_type === 'file'
                    ? '[文件]'
                    : session.last_content_type === 'image'
                      ? '[图片]'
                      : session.last_content || ''
                }}
              </div>
            </div>
          </div>
          <div v-if="filteredSessions.length === 0" class="wc-page__empty-text">暂无会话</div>
        </ElScrollbar>
      </div>

      <!-- 右栏：聊天主窗口 -->
      <div class="wc-page__main">
        <template v-if="currentRoomId">
          <!-- 顶部标题栏 -->
          <div class="wc-page__main-header">
            <!-- CH-02: 群聊名称可点击查看群信息 -->
            <span
              class="wc-page__main-header-name"
              :class="{
                'wc-page__main-header-name--clickable': currentSession?.room_type === 'group'
              }"
              @click="openGroupInfo"
            >
              {{ currentSession?.room_name || '聊天' }}
              <svg
                v-if="currentSession?.room_type === 'group'"
                viewBox="0 0 24 24"
                width="14"
                height="14"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                style="vertical-align: middle; margin-left: 2px"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </span>
            <div class="wc-page__main-header-actions">
              <!-- CH-06: 导出按钮 -->
              <div class="wc-page__export-wrapper">
                <button
                  class="wc-page__icon-btn"
                  title="导出聊天记录"
                  @click="showExportMenu = !showExportMenu"
                >
                  <svg
                    viewBox="0 0 24 24"
                    width="16"
                    height="16"
                    fill="none"
                    stroke="#666"
                    stroke-width="2"
                  >
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </button>
                <Transition name="wc-menu">
                  <div v-if="showExportMenu" class="wc-page__export-dropdown" @click.stop>
                    <div class="wc-page__export-item" @click="handleExport('text')">
                      <svg
                        viewBox="0 0 24 24"
                        width="14"
                        height="14"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                      <span>导出为文本</span>
                    </div>
                    <div class="wc-page__export-item" @click="handleExport('html')">
                      <svg
                        viewBox="0 0 24 24"
                        width="14"
                        height="14"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <polyline points="16 18 22 12 16 6" />
                        <polyline points="8 6 2 12 8 18" />
                      </svg>
                      <span>导出为HTML</span>
                    </div>
                  </div>
                </Transition>
              </div>
              <button class="wc-page__icon-btn" title="视频通话">
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
              <button class="wc-page__icon-btn" title="语音通话">
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
            </div>
          </div>

          <!-- 消息区域 -->
          <ElScrollbar ref="messageScrollbar" class="wc-page__main-messages">
            <div class="wc-page__msg-list">
              <template v-for="(msg, idx) in messages" :key="msg.id">
                <div v-if="shouldShowTimeDivider(idx)" class="wc-page__time-divider">
                  {{ formatTimeDivider(msg.created_at) }}
                </div>
                <div
                  class="wc-page__msg"
                  :class="{ 'wc-page__msg--self': msg.sender_id === currentUserId }"
                  @contextmenu="showContextMenu($event, msg)"
                >
                  <div class="wc-page__msg-avatar">
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
                  <div class="wc-page__msg-body">
                    <!-- CH-03: 撤回消息显示 -->
                    <template v-if="msg.is_recalled">
                      <div class="wc-page__msg-recalled">
                        {{ msg.sender_id === currentUserId ? '你' : msg.sender_name }}撤回了一条消息
                      </div>
                    </template>
                    <!-- CH-04: 图片消息 -->
                    <template v-else-if="msg.content_type === 'image'">
                      <div class="wc-page__msg-bubble wc-page__msg-bubble--image">
                        <img
                          :src="msg.content"
                          class="wc-page__msg-image"
                          @click="openImagePreview(msg.content)"
                          alt="图片"
                        />
                      </div>
                    </template>
                    <!-- 文本消息（含 CH-08 @mention 高亮） -->
                    <template v-else-if="msg.content_type === 'text'">
                      <div class="wc-page__msg-bubble">
                        <template
                          v-for="(part, pIdx) in renderMentionText(msg.content)"
                          :key="pIdx"
                        >
                          <span v-if="part.isMention" class="wc-page__mention-highlight">{{
                            part.text
                          }}</span>
                          <span v-else>{{ part.text }}</span>
                        </template>
                      </div>
                    </template>
                    <!-- 文件消息 -->
                    <template v-else>
                      <div class="wc-page__msg-bubble wc-page__msg-bubble--file">
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
                    </template>
                    <div class="wc-page__msg-meta">
                      <span class="wc-page__msg-time">{{ formatMsgTime(msg.created_at) }}</span>
                      <!-- CH-05: 已读回执（仅自己发送的消息） -->
                      <ElPopover
                        v-if="msg.sender_id === currentUserId && !msg.is_recalled"
                        :visible="readPopoverMsgId === msg.id"
                        placement="top"
                        :width="200"
                        trigger="click"
                        @before-enter="showReadPopover(msg.id)"
                      >
                        <template #reference>
                          <span
                            class="wc-page__read-badge"
                            @click.stop="
                              readPopoverMsgId = readPopoverMsgId === msg.id ? null : msg.id
                            "
                          >
                            {{ getReadBadgeText(msg) }}
                          </span>
                        </template>
                        <div class="wc-page__read-popover">
                          <div class="wc-page__read-popover-title">已读列表</div>
                          <div
                            v-for="reader in readStatusMap.get(msg.id)?.readers || []"
                            :key="reader.user_id"
                            class="wc-page__read-popover-item"
                          >
                            {{ reader.username }}
                          </div>
                          <div
                            v-if="(readStatusMap.get(msg.id)?.readers || []).length === 0"
                            class="wc-page__read-popover-empty"
                          >
                            暂无已读
                          </div>
                        </div>
                      </ElPopover>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </ElScrollbar>

          <!-- 输入区域 -->
          <div class="wc-page__input-area">
            <div class="wc-page__toolbar">
              <button class="wc-page__icon-btn" title="表情">
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
              <!-- CH-04: 图片上传按钮 -->
              <button class="wc-page__icon-btn" title="发送图片" @click="imageInput?.click()">
                <svg
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="#666"
                  stroke-width="1.8"
                >
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
              </button>
              <button class="wc-page__icon-btn" title="上传文件" @click="fileInput?.click()">
                <svg
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="#666"
                  stroke-width="1.8"
                >
                  <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
                </svg>
              </button>
              <button class="wc-page__icon-btn" title="截图">
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
            </div>
            <div class="wc-page__input-box">
              <!-- CH-08: @提及下拉框 -->
              <div
                v-if="showMentionDropdown && mentionCandidates.length > 0"
                class="wc-page__mention-dropdown"
              >
                <div
                  v-for="(user, uIdx) in mentionCandidates"
                  :key="user.id"
                  class="wc-page__mention-item"
                  :class="{ 'wc-page__mention-item--active': uIdx === mentionSelectedIndex }"
                  @mousedown.prevent="selectMention(user)"
                >
                  <ElAvatar
                    v-if="user.avatar"
                    :size="24"
                    :src="user.avatar"
                    style="border-radius: 4px"
                  />
                  <ElAvatar
                    v-else
                    :size="24"
                    style="background: #7eb7e5; border-radius: 4px; font-size: 12px"
                    >{{ user.username[0] }}</ElAvatar
                  >
                  <span>{{ user.username }}</span>
                </div>
              </div>
              <textarea
                ref="textareaRef"
                v-model="inputText"
                class="wc-page__textarea"
                placeholder=""
                rows="3"
                @keydown="handleKeyDown"
                @input="handleTextareaInput"
              ></textarea>
            </div>
            <div class="wc-page__send-row">
              <button class="wc-page__send-btn" :disabled="!inputText.trim()" @click="handleSend"
                >发送</button
              >
            </div>
          </div>

          <input ref="fileInput" type="file" style="display: none" @change="handleFileUpload" />
          <input
            ref="imageInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleImageUpload"
          />
        </template>

        <!-- 未选择会话 -->
        <div v-else class="wc-page__placeholder">
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

    <!-- 右键菜单（消息） -->
    <Transition name="wc-menu">
      <div
        v-if="contextMenu.visible"
        class="wc-page__context-menu"
        :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
        @click.stop
      >
        <!-- CH-03: 撤回选项 -->
        <div v-if="canRecall" class="wc-page__context-menu-item" @click="handleRecallMessage">
          <svg
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
          </svg>
          <span>撤回</span>
        </div>
        <div class="wc-page__context-menu-item" @click="handleDeleteMessage">
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
            />
          </svg>
          <span>删除</span>
        </div>
      </div>
    </Transition>

    <!-- CH-07: 会话右键菜单 -->
    <Transition name="wc-menu">
      <div
        v-if="sessionContextMenu.visible"
        class="wc-page__context-menu"
        :style="{ left: sessionContextMenu.x + 'px', top: sessionContextMenu.y + 'px' }"
        @click.stop
      >
        <div class="wc-page__context-menu-item" @click="handleTogglePin">
          <svg
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              v-if="sessionContextMenu.isPinned"
              d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z"
              fill="currentColor"
            />
            <template v-else>
              <path d="M16 12V4h1V2H7v2h1v8l-2 2v2h5.2v6h1.6v-6H18v-2l-2-2z" />
            </template>
          </svg>
          <span>{{ sessionContextMenu.isPinned ? '取消置顶' : '置顶' }}</span>
        </div>
        <div class="wc-page__context-menu-item" @click="handleToggleMute">
          <svg
            viewBox="0 0 24 24"
            width="14"
            height="14"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <template v-if="sessionContextMenu.isMuted">
              <path d="M11 5L6 9H2v6h4l5 4V5z" />
              <path d="M19.07 4.93a10 10 0 010 14.14" />
              <path d="M15.54 8.46a5 5 0 010 7.07" />
            </template>
            <template v-else>
              <path d="M11 5L6 9H2v6h4l5 4V5z" />
              <line x1="23" y1="9" x2="17" y2="15" />
              <line x1="17" y1="9" x2="23" y2="15" />
            </template>
          </svg>
          <span>{{ sessionContextMenu.isMuted ? '取消免打扰' : '免打扰' }}</span>
        </div>
      </div>
    </Transition>

    <!-- CH-04: 图片预览弹窗 -->
    <ElDialog
      v-model="imagePreviewVisible"
      :show-close="true"
      width="auto"
      class="wc-page__image-preview-dialog"
      @close="imagePreviewVisible = false"
    >
      <img :src="imagePreviewUrl" class="wc-page__image-preview-img" alt="预览" />
    </ElDialog>

    <!-- CH-02: 创建群聊弹窗 -->
    <ElDialog
      v-model="showCreateGroup"
      title="创建群聊"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="wc-page__dialog-form">
        <div class="wc-page__dialog-field">
          <label>群名称</label>
          <input
            v-model="groupName"
            type="text"
            placeholder="请输入群名称"
            class="wc-page__dialog-input"
          />
        </div>
        <div class="wc-page__dialog-field">
          <label>选择成员</label>
          <div class="wc-page__dialog-member-list">
            <label v-for="u in onlineUsers" :key="u.id" class="wc-page__dialog-member-item">
              <input type="checkbox" :value="u.id" v-model="groupMemberIds" />
              <ElAvatar v-if="u.avatar" :size="24" :src="u.avatar" style="border-radius: 4px" />
              <ElAvatar
                v-else
                :size="24"
                style="background: #7eb7e5; border-radius: 4px; font-size: 12px"
                >{{ u.username[0] }}</ElAvatar
              >
              <span>{{ u.username }}</span>
            </label>
            <div v-if="onlineUsers.length === 0" class="wc-page__empty-text">暂无在线用户</div>
          </div>
        </div>
      </div>
      <template #footer>
        <button class="wc-page__send-btn" @click="handleCreateGroup">创建</button>
      </template>
    </ElDialog>

    <!-- CH-02: 群信息弹窗 -->
    <ElDialog v-model="showGroupInfo" title="群聊信息" width="400px">
      <div class="wc-page__group-info">
        <div class="wc-page__group-info-header">
          <span class="wc-page__group-info-name">{{ currentSession?.room_name }}</span>
          <button
            class="wc-page__icon-btn"
            title="修改群名"
            @click="((renameGroupName = currentSession?.room_name || ''), (showRenameGroup = true))"
          >
            <svg
              viewBox="0 0 24 24"
              width="14"
              height="14"
              fill="none"
              stroke="#666"
              stroke-width="2"
            >
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
          </button>
        </div>
        <div class="wc-page__group-info-members">
          <div class="wc-page__group-info-members-header">
            <span>群成员 ({{ groupMembers.length }})</span>
            <button class="wc-page__group-info-add-btn" @click="showAddMember = true"
              >添加成员</button
            >
          </div>
          <div class="wc-page__group-info-member-list">
            <div v-for="m in groupMembers" :key="m.user_id" class="wc-page__group-info-member">
              <ElAvatar v-if="m.avatar" :size="28" :src="m.avatar" style="border-radius: 4px" />
              <ElAvatar
                v-else
                :size="28"
                style="background: #7eb7e5; border-radius: 4px; font-size: 12px"
                >{{ m.username[0] }}</ElAvatar
              >
              <span class="wc-page__group-info-member-name">{{ m.username }}</span>
              <span class="wc-page__group-info-member-role">{{
                m.role === 'owner' ? '群主' : ''
              }}</span>
            </div>
          </div>
        </div>
        <button class="wc-page__leave-group-btn" @click="handleLeaveGroup">退出群聊</button>
      </div>
    </ElDialog>

    <!-- CH-02: 修改群名弹窗 -->
    <ElDialog
      v-model="showRenameGroup"
      title="修改群名称"
      width="360px"
      :close-on-click-modal="false"
    >
      <input
        v-model="renameGroupName"
        type="text"
        placeholder="请输入新群名称"
        class="wc-page__dialog-input"
      />
      <template #footer>
        <button class="wc-page__send-btn" @click="handleRenameGroup">确认</button>
      </template>
    </ElDialog>

    <!-- CH-02: 添加群成员弹窗 -->
    <ElDialog
      v-model="showAddMember"
      title="添加群成员"
      width="360px"
      :close-on-click-modal="false"
    >
      <div class="wc-page__dialog-member-list">
        <label v-for="u in onlineUsers" :key="u.id" class="wc-page__dialog-member-item">
          <input type="checkbox" :value="u.id" v-model="addMemberIds" />
          <ElAvatar v-if="u.avatar" :size="24" :src="u.avatar" style="border-radius: 4px" />
          <ElAvatar
            v-else
            :size="24"
            style="background: #7eb7e5; border-radius: 4px; font-size: 12px"
            >{{ u.username[0] }}</ElAvatar
          >
          <span>{{ u.username }}</span>
        </label>
      </div>
      <template #footer>
        <button class="wc-page__send-btn" @click="handleAddMembers">添加</button>
      </template>
    </ElDialog>
  </div>
</template>

<style lang="less" scoped>
.wc-page {
  height: calc(100vh - var(--top-tool-height) - var(--tags-view-height) - 40px);
  margin: -20px;
  background: #f5f5f5;
  overflow: hidden;

  &__layout {
    display: flex;
    height: 100%;
    border: 1px solid #d6d6d6;
    overflow: hidden;
  }
}

/* ==================== 左栏：会话列表 ==================== */
.wc-page__sidebar {
  width: 272px;
  min-width: 272px;
  background: #f0f0f0;
  border-right: 1px solid #d6d6d6;
  display: flex;
  flex-direction: column;
}

.wc-page__sidebar-top {
  display: flex;
  align-items: center;
  padding: 10px 8px;
  gap: 6px;
}

.wc-page__search {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  padding: 5px 10px;
  background: #e6e6e6;
  border-radius: 4px;

  svg {
    flex-shrink: 0;
  }
}

.wc-page__search-input {
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

.wc-page__add-btn {
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

.wc-page__icon-btn--sm {
  width: 20px;
  height: 20px;
  border-radius: 3px;
  border: none;
  background: transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
  flex-shrink: 0;

  &:hover {
    background: #d0d0d0;
  }
}

.wc-page__session-list {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 会话列表项 */
.wc-page__session {
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

    .wc-page__session-name {
      color: #fff;
      font-weight: 600;
    }

    .wc-page__session-time {
      color: rgba(255, 255, 255, 0.75);
    }

    .wc-page__session-preview {
      color: rgba(255, 255, 255, 0.85);
    }

    .wc-page__session-badge {
      border-color: #1aad19;
    }

    .wc-page__session-pin-icon {
      fill: #fff;
    }

    .wc-page__session-mute-icon {
      stroke: rgba(255, 255, 255, 0.7);
    }
  }
}

.wc-page__session-avatar {
  position: relative;
  flex-shrink: 0;
}

.wc-page__session-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  background: #fa5151;
  border: 2px solid #f0f0f0;
  font-size: 10px;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 3px;
  line-height: 1;
}

.wc-page__session-badge--muted {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #b2b2b2;
  border: 2px solid #f0f0f0;
}

.wc-page__session-body {
  flex: 1;
  overflow: hidden;
  min-width: 0;
}

.wc-page__session-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.wc-page__session-name-row {
  display: flex;
  align-items: center;
  gap: 3px;
  overflow: hidden;
  min-width: 0;
}

.wc-page__session-pin-icon {
  flex-shrink: 0;
}

.wc-page__session-mute-icon {
  flex-shrink: 0;
}

.wc-page__session-name {
  font-size: 14px;
  font-weight: 500;
  color: #191919;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wc-page__session-time {
  font-size: 11px;
  color: #b2b2b2;
  flex-shrink: 0;
  margin-left: 8px;
}

.wc-page__session-preview {
  font-size: 12px;
  color: #b2b2b2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wc-page__empty-text {
  padding: 32px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

/* ==================== CH-01: 消息搜索面板 ==================== */
.wc-page__search-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f0f0f0;
}

.wc-page__search-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #d6d6d6;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.wc-page__search-panel-input {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
}

.wc-page__search-panel-field {
  flex: 1;
  border: 1px solid #d6d6d6;
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 13px;
  outline: none;
  background: #fff;

  &:focus {
    border-color: #07c160;
  }
}

.wc-page__search-panel-btn {
  padding: 6px 16px;
  background: #07c160;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;

  &:disabled {
    background: #a0e8b8;
    cursor: not-allowed;
  }
}

.wc-page__search-panel-results {
  flex: 1;
  overflow-y: auto;
}

.wc-page__search-result-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #e8e8e8;

  &:hover {
    background: #e8e8e8;
  }
}

.wc-page__search-result-room {
  font-size: 12px;
  color: #07c160;
  font-weight: 500;
  margin-bottom: 2px;
}

.wc-page__search-result-sender {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.wc-page__search-result-content {
  font-size: 13px;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ==================== 新建聊天用户选择 ==================== */
.wc-page__user-picker {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wc-page__user-picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #d6d6d6;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.wc-page__user-picker-list {
  flex: 1;
  overflow-y: auto;
}

.wc-page__user-item {
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

.wc-page__user-name {
  font-size: 14px;
  color: #333;
}

/* CH-02: 创建群聊按钮 */
.wc-page__create-group-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #07c160;
  width: 100%;
  text-align: left;
  transition: background 0.15s;

  &:hover {
    background: #e0f5e8;
  }

  span {
    font-weight: 500;
  }
}

/* ==================== 右栏：聊天主窗口 ==================== */
.wc-page__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  background: #f5f5f5;
}

.wc-page__main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #f5f5f5;
  border-bottom: 1px solid #d6d6d6;
  flex-shrink: 0;
}

.wc-page__main-header-name {
  font-size: 16px;
  font-weight: 500;
  color: #191919;

  &--clickable {
    cursor: pointer;

    &:hover {
      color: #07c160;
    }
  }
}

.wc-page__main-header-actions {
  display: flex;
  gap: 2px;
  align-items: center;
}

.wc-page__main-messages {
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

.wc-page__placeholder {
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

/* ==================== 消息气泡 ==================== */
.wc-page__msg-list {
  padding: 12px 20px;
}

.wc-page__time-divider {
  text-align: center;
  padding: 10px 0;
  font-size: 12px;
  color: #999;
}

.wc-page__msg {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  align-items: flex-start;

  &--self {
    flex-direction: row-reverse;

    .wc-page__msg-bubble {
      background: #95ec69;
      color: #000;

      &--file a {
        color: #333;
      }

      &--image {
        background: transparent;
        padding: 0;
        box-shadow: none;
      }
    }

    .wc-page__msg-meta {
      justify-content: flex-end;
    }
  }
}

.wc-page__msg-avatar {
  flex-shrink: 0;
  margin-top: 2px;
}

.wc-page__msg-body {
  max-width: 420px;
  position: relative;
  min-width: 0;
}

.wc-page__msg-bubble {
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

  &--image {
    background: transparent;
    padding: 0;
    box-shadow: none;
    border-radius: 6px;
    overflow: hidden;
  }
}

/* CH-03: 撤回消息 */
.wc-page__msg-recalled {
  font-size: 12px;
  color: #999;
  font-style: italic;
  padding: 4px 0;
}

/* CH-04: 图片消息 */
.wc-page__msg-image {
  max-width: 240px;
  max-height: 240px;
  border-radius: 6px;
  cursor: pointer;
  display: block;
  object-fit: cover;

  &:hover {
    opacity: 0.9;
  }
}

.wc-page__msg-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.wc-page__msg-time {
  font-size: 11px;
  color: #b2b2b2;
}

/* CH-05: 已读回执 */
.wc-page__read-badge {
  font-size: 11px;
  color: #b2b2b2;
  cursor: pointer;

  &:hover {
    color: #07c160;
  }
}

.wc-page__read-popover {
  max-height: 200px;
  overflow-y: auto;
}

.wc-page__read-popover-title {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #eee;
}

.wc-page__read-popover-item {
  font-size: 13px;
  color: #666;
  padding: 4px 0;
}

.wc-page__read-popover-empty {
  font-size: 13px;
  color: #999;
  padding: 8px 0;
}

/* CH-08: @提及高亮 */
.wc-page__mention-highlight {
  color: #576b95;
  font-weight: 500;
}

/* ==================== 输入区域 ==================== */
.wc-page__input-area {
  background: #f5f5f5;
  border-top: 1px solid #d6d6d6;
  flex-shrink: 0;
  padding: 6px 16px 10px;
}

.wc-page__toolbar {
  display: flex;
  gap: 2px;
  padding-bottom: 4px;
}

.wc-page__input-box {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 4px 8px;
  position: relative;
}

.wc-page__textarea {
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

/* CH-08: @提及下拉框 */
.wc-page__mention-dropdown {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  max-height: 200px;
  overflow-y: auto;
  z-index: 100;
}

.wc-page__mention-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #333;

  &:hover,
  &--active {
    background: #f0f0f0;
  }
}

.wc-page__send-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 6px;
}

.wc-page__send-btn {
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

.wc-page__icon-btn {
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

/* ==================== CH-06: 导出下拉 ==================== */
.wc-page__export-wrapper {
  position: relative;
}

.wc-page__export-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 140px;
  padding: 4px 0;
  margin-top: 4px;
}

.wc-page__export-item {
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

/* ==================== 右键菜单 ==================== */
.wc-page__context-menu {
  position: fixed;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
  z-index: 10000;
  min-width: 100px;
  padding: 4px 0;
}

.wc-page__context-menu-item {
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

/* ==================== CH-04: 图片预览弹窗 ==================== */
.wc-page__image-preview-dialog {
  :deep(.el-dialog) {
    background: transparent;
    box-shadow: none;
    max-width: 90vw;
  }

  :deep(.el-dialog__header) {
    display: none;
  }

  :deep(.el-dialog__body) {
    padding: 0;
  }
}

.wc-page__image-preview-img {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 4px;
}

/* ==================== CH-02: 群聊弹窗样式 ==================== */
.wc-page__dialog-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wc-page__dialog-field {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 13px;
    color: #666;
    font-weight: 500;
  }
}

.wc-page__dialog-input {
  border: 1px solid #d6d6d6;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  outline: none;

  &:focus {
    border-color: #07c160;
  }
}

.wc-page__dialog-member-list {
  max-height: 240px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.wc-page__dialog-member-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 13px;
  color: #333;

  &:hover {
    background: #f5f5f5;
  }

  input[type='checkbox'] {
    accent-color: #07c160;
  }
}

.wc-page__group-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.wc-page__group-info-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.wc-page__group-info-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.wc-page__group-info-members {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wc-page__group-info-members-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #666;
}

.wc-page__group-info-add-btn {
  font-size: 12px;
  color: #07c160;
  background: none;
  border: none;
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.wc-page__group-info-member-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.wc-page__group-info-member {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: #333;
}

.wc-page__group-info-member-name {
  flex: 1;
}

.wc-page__group-info-member-role {
  font-size: 11px;
  color: #07c160;
  font-weight: 500;
}

.wc-page__leave-group-btn {
  padding: 8px 0;
  background: none;
  border: 1px solid #fa5151;
  border-radius: 4px;
  color: #fa5151;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #fa5151;
    color: #fff;
  }
}

/* ==================== 动画 ==================== */
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
