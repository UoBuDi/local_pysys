import axios, { AxiosError } from 'axios'
import { defaultRequestInterceptors, defaultResponseInterceptors } from './config'
import { setupTokenRefreshInterceptor } from './refreshInterceptor'

import { AxiosInstance, InternalAxiosRequestConfig, RequestConfig, AxiosResponse } from './types'
import { ElMessage } from 'element-plus'
import { REQUEST_TIMEOUT } from '@/constants'
import { requestCache } from '@/utils/requestCache'
import { requestDedup } from '@/utils/requestDedup'

export const PATH_URL = import.meta.env.VITE_API_BASE_PATH || ''

const abortControllerMap: Map<string, AbortController> = new Map()

const MAX_RETRY_COUNT = 3
const RETRY_DELAY = 1000

const retryDelay = (delay: number) => {
  return new Promise((resolve) => setTimeout(resolve, delay))
}

const axiosInstance: AxiosInstance = axios.create({
  timeout: REQUEST_TIMEOUT,
  baseURL: PATH_URL
})

axiosInstance.interceptors.request.use((res: InternalAxiosRequestConfig) => {
  const controller = new AbortController()
  const url = res.url || ''
  res.signal = controller.signal
  abortControllerMap.set(
    import.meta.env.VITE_USE_MOCK === 'true' ? url.replace('/mock', '') : url,
    controller
  )
  return res
})

axiosInstance.interceptors.response.use(
  (res: AxiosResponse) => {
    const url = res.config.url || ''
    abortControllerMap.delete(url)
    return res
  },
  async (error: AxiosError) => {
    const config = error.config as any

    if (!config) {
      console.log('err： ' + error)
      const errorMsg = error.code === 'ECONNABORTED' && error.message?.includes('timeout')
        ? '请求超时，请稍后重试（无此数据）'
        : error.message
      ElMessage.error(errorMsg)
      return Promise.reject(error)
    }

    config.__retryCount = config.__retryCount || 0

    if (error.response?.status === 429) {
      const url = config.url || ''

      if (url.includes('/api/token/refresh') || url.includes('token/refresh')) {
        console.warn('[HTTP] Token刷新请求被限流(429)，不再重试')
        return Promise.reject(error)
      }

      console.warn('[HTTP] 请求频率限制 (429)，准备重试...')

      if (config.__retryCount < MAX_RETRY_COUNT) {
        config.__retryCount++
        const delay = RETRY_DELAY * Math.pow(2, config.__retryCount - 1)
        console.log(`[HTTP] 第 ${config.__retryCount} 次重试，延迟 ${delay}ms`)

        await retryDelay(delay)

        const retryUrl = config.url || ''
        const controller = new AbortController()
        config.signal = controller.signal
        abortControllerMap.set(retryUrl, controller)

        return axiosInstance.request(config)
      } else {
        ElMessage.error('请求过于频繁，请稍后再试')
        return Promise.reject(error)
      }
    }

    console.log('err： ' + error)
    const errorMsg = error.code === 'ECONNABORTED' && error.message?.includes('timeout')
      ? '请求超时，请稍后重试（无此数据）'
      : error.message
    ElMessage.error(errorMsg)
    return Promise.reject(error)
  }
)

axiosInstance.interceptors.request.use(defaultRequestInterceptors)
axiosInstance.interceptors.response.use(defaultResponseInterceptors)

setupTokenRefreshInterceptor(axiosInstance)

// 缓存配置
const CACHE_ENABLED = true
const CACHE_METHODS = ['GET'] // 只缓存GET请求
const DEFAULT_CACHE_TTL = 5 * 60 * 1000 // 5分钟

const service = {
  request: (config: RequestConfig) => {
    // 检查缓存
    if (CACHE_ENABLED && CACHE_METHODS.includes(config.method?.toUpperCase() || 'GET')) {
      const cached = requestCache.get(config.url || '', config.params)
      if (cached) {
        return Promise.resolve(cached)
      }
    }

    // 请求去重
    return requestDedup.wrap(config, async () => {
      return new Promise((resolve, reject) => {
        if (config.interceptors?.requestInterceptors) {
          config = config.interceptors.requestInterceptors(config as any)
        }

        axiosInstance
          .request(config)
          .then((res) => {
            // 缓存成功的GET请求
            if (CACHE_ENABLED && config.method?.toUpperCase() === 'GET') {
              requestCache.set(
                config.url || '',
                res,
                config.params,
                (config as any).cacheTTL || DEFAULT_CACHE_TTL
              )
            }
            resolve(res)
          })
          .catch((err: any) => {
            reject(err)
          })
      })
    })
  },
  cancelRequest: (url: string | string[]) => {
    const urlList = Array.isArray(url) ? url : [url]
    for (const _url of urlList) {
      abortControllerMap.get(_url)?.abort()
      abortControllerMap.delete(_url)
    }
    // 同时取消去重队列中的请求
    urlList.forEach((url) => requestDedup.cancel(url))
  },
  cancelAllRequest() {
    for (const [_, controller] of abortControllerMap) {
      controller.abort()
    }
    abortControllerMap.clear()
    requestDedup.cancel()
  },
  // 清除缓存
  clearCache: (pattern?: string) => {
    requestCache.clear(pattern)
  },
  // 获取统计信息
  getStats: () => ({
    cache: requestCache.getStats(),
    pending: requestDedup.getPendingCount(),
    pendingRequests: requestDedup.getPendingRequests()
  }),
  // 检查是否有待处理的请求
  hasPending: (url: string) => requestDedup.hasPending(url)
}

export default service
