import request from '@/axios'

export interface ChatMessage {
  id: number
  room_id: string
  sender_id: number
  sender_name: string
  sender_avatar?: string
  content_type: 'text' | 'file' | 'image'
  content: string
  file_name?: string
  is_recalled?: number
  mentioned_user_ids?: number[]
  created_at: string
}

export interface ChatSession {
  room_id: string
  room_name: string | null
  room_type: 'private' | 'group'
  unread_count: number
  last_message_id: number | null
  updated_at: string | null
  is_pinned?: number
  is_muted?: number
  last_content: string | null
  last_content_type: string | null
  last_sender_name: string | null
  last_created_at: string | null
  avatar?: string
}

export interface OnlineUser {
  id: number
  username: string
  avatar?: string
  online?: boolean
}

export interface GroupMember {
  user_id: number
  role: 'owner' | 'admin' | 'member'
  joined_at: string | null
  username: string
  avatar: string
}

export interface ReadStatus {
  message_id: number
  read_count: number
  total_count: number
  readers: { user_id: number; username: string }[]
}

// CH-01: 搜索消息
export const searchMessages = (keyword: string, roomId?: string, limit: number = 50) => {
  const params: Record<string, any> = { keyword, limit }
  if (roomId) params.room_id = roomId
  return request.get({ url: '/api/chat/search/', params })
}

// 发送消息（含 CH-08 @提及）
export const sendMessage = (params: {
  room_id: string
  content_type?: string
  content: string
  mentioned_user_ids?: string
}) => {
  return request.post({ url: '/api/chat/send/', params })
}

// 获取聊天历史
export const getChatHistory = (roomId: string, limit: number = 50, beforeId?: number) => {
  const params: Record<string, any> = { limit }
  if (beforeId) params.before_id = beforeId
  return request.get({ url: `/api/chat/history/${roomId}`, params })
}

// 标记已读
export const markRoomRead = (roomId: string) => {
  return request.post({ url: `/api/chat/read/${roomId}` })
}

// CH-05: 获取已读状态
export const getReadStatus = (roomId: string, messageId?: number) => {
  const params: Record<string, any> = {}
  if (messageId) params.message_id = messageId
  return request.get({ url: `/api/chat/read-status/${roomId}`, params })
}

// 获取会话列表
export const getChatSessions = () => {
  return request.get({ url: '/api/chat/sessions/' })
}

// CH-07: 更新会话设置（置顶/免打扰）
export const updateSessionSettings = (params: {
  room_id: string
  is_pinned?: number
  is_muted?: number
}) => {
  return request.put({ url: '/api/chat/session-settings/', params })
}

// 创建聊天房间（含 CH-02 群聊）
export const createChatRoom = (params: {
  target_user_id: number
  room_type?: string
  room_name?: string
  member_ids?: string
}) => {
  return request.post({ url: '/api/chat/create-room/', params })
}

// CH-02: 获取群成员列表
export const getGroupMembers = (roomId: string) => {
  return request.get({ url: `/api/chat/group-members/${roomId}` })
}

// CH-02: 添加群成员
export const addGroupMembers = (roomId: string, memberIds: string) => {
  return request.post({
    url: '/api/chat/add-group-members/',
    params: { room_id: roomId, member_ids: memberIds }
  })
}

// CH-02: 修改群名称
export const updateGroupName = (roomId: string, roomName: string) => {
  return request.put({
    url: '/api/chat/group-name/',
    params: { room_id: roomId, room_name: roomName }
  })
}

// CH-02: 退出群聊
export const leaveGroup = (roomId: string) => {
  return request.post({ url: `/api/chat/leave-group/${roomId}` })
}

// CH-03: 撤回消息
export const recallMessage = (messageId: number) => {
  return request.post({ url: `/api/chat/recall/${messageId}` })
}

// 获取在线用户
export const getOnlineUsers = () => {
  return request.get({ url: '/api/chat/online-users/' })
}

// 上传文件（CH-04 自动识别图片类型）
export const uploadChatFile = (file: File, roomId: string) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post({
    url: '/api/chat/upload/',
    data: formData,
    params: { room_id: roomId },
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// CH-04: 上传图片
export const uploadChatImage = (file: File, roomId: string) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post({
    url: '/api/chat/upload-image/',
    data: formData,
    params: { room_id: roomId },
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// CH-06: 导出聊天记录
export const exportChatHistory = (roomId: string, format: string = 'text') => {
  return request.get({
    url: `/api/chat/export/${roomId}`,
    params: { format },
    responseType: format === 'html' ? 'text' : 'text'
  })
}

// 删除消息
export const deleteChatMessage = (messageId: number) => {
  return request.delete({ url: `/api/chat/message/${messageId}` })
}
