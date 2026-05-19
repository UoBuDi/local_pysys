import request from '@/axios'

// 获取配置
export const getConfig = () => {
  return request.get({ url: '/api/config/' })
}

// 保存配置
export const saveConfig = (data: any) => {
  return request.post({ url: '/api/config/', data })
}

// 测试远程数据库连接
export const testRemoteConnection = (data: any) => {
  return request.post({ url: '/api/config/test-remote/', data })
}

// 测试本地数据库连接
export const testLocalConnection = (data: any) => {
  return request.post({ url: '/api/config/test-local/', data })
}

// 获取可选月份列表
export const getSyncMonths = () => {
  return request.get({ url: '/api/sync/months/' })
}

// 开始同步
export const startSync = (data: { months: string[] }) => {
  return request.post({ url: '/api/sync/start/', data })
}

// 停止同步
export const stopSync = () => {
  return request.post({ url: '/api/sync/stop/' })
}

// 获取同步状态
export const getSyncStatus = () => {
  return request.get({ url: '/api/sync/status/' })
}
