import request from '@/axios'

export interface ChatMessage {
  id: number
  room_id: string
  sender_id: number
  sender_name: string
  sender_avatar?: string
  content_type: 'text' | 'file'
  content: string
  file_name?: string
  created_at: string
}

export interface ChatSession {
  room_id: string
  room_name: string | null
  room_type: 'private' | 'group'
  unread_count: number
  last_message_id: number | null
  updated_at: string | null
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

export const deleteChatMessage = (messageId: number) => {
  return request.delete({
    url: `/api/chat/message/${messageId}`
  })
}

export const sendMessage = (params: {
  room_id: string
  content_type?: string
  content: string
}) => {
  return request.post({
    url: '/api/chat/send/',
    params
  })
}

export const getChatHistory = (roomId: string, limit: number = 50, beforeId?: number) => {
  const params: Record<string, any> = { limit }
  if (beforeId) params.before_id = beforeId
  return request.get({
    url: `/api/chat/history/${roomId}`,
    params
  })
}

export const markRoomRead = (roomId: string) => {
  return request.post({
    url: `/api/chat/read/${roomId}`
  })
}

export const getChatSessions = () => {
  return request.get({
    url: '/api/chat/sessions/'
  })
}

export const createChatRoom = (params: {
  target_user_id: number
  room_type?: string
  room_name?: string
}) => {
  return request.post({
    url: '/api/chat/create-room/',
    params
  })
}

export const getOnlineUsers = () => {
  return request.get({
    url: '/api/chat/online-users/'
  })
}

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
