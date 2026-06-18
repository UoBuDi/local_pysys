import request from '@/axios'

/** 全站广播通知 */
export const broadcastNotification = (data: { type: string; title: string; content?: string }) => {
  return request.post({ url: '/api/notifications/broadcast', data })
}

/** 向指定用户推送通知 */
export const sendNotificationToUsers = (data: {
  type: string
  title: string
  content?: string
  target_user_ids: number[]
}) => {
  return request.post({ url: '/api/notifications/send', data })
}

/** 踢出指定在线用户 */
export const kickUser = (data: { user_id: number; reason?: string }) => {
  return request.post({ url: '/api/notifications/kick-user', data })
}

/** 强制刷新前端权限/菜单 */
export const forceRefresh = (data: {
  target_type: 'all' | 'user'
  target_user_ids?: number[]
}) => {
  return request.post({ url: '/api/notifications/force-refresh', data })
}

/** 查询通知历史记录 */
export const getNotificationHistory = (params: { page?: number; page_size?: number }) => {
  return request.get({ url: '/api/notifications/history', params })
}
