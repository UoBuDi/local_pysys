import axios, { AxiosError } from 'axios'
import { defaultRequestInterceptors, defaultResponseInterceptors } from './config'
import { setupTokenRefreshInterceptor } from './refreshInterceptor'

import { AxiosInstance, InternalAxiosRequestConfig, RequestConfig, AxiosResponse } from './types'
import { ElMessage } from 'element-plus'
import { REQUEST_TIMEOUT } from '@/constants'

export const PATH_URL = import.meta.env.VITE_API_BASE_PATH

const abortControllerMap: Map<string, AbortController> = new Map()

const MAX_RETRY_COUNT = 3
const RETRY_DELAY = 1000

const retryDelay = (delay: number) => {
  return new Promise(resolve => setTimeout(resolve, delay))
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
      ElMessage.error(error.message)
      return Promise.reject(error)
    }
    
    config.__retryCount = config.__retryCount || 0
    
    if (error.response?.status === 429) {
      console.warn('[HTTP] 请求频率限制 (429)，准备重试...')
      
      if (config.__retryCount < MAX_RETRY_COUNT) {
        config.__retryCount++
        const delay = RETRY_DELAY * Math.pow(2, config.__retryCount - 1)
        console.log(`[HTTP] 第 ${config.__retryCount} 次重试，延迟 ${delay}ms`)
        
        await retryDelay(delay)
        
        const url = config.url || ''
        const controller = new AbortController()
        config.signal = controller.signal
        abortControllerMap.set(url, controller)
        
        return axiosInstance.request(config)
      } else {
        ElMessage.error('请求过于频繁，请稍后再试')
        return Promise.reject(error)
      }
    }
    
    console.log('err： ' + error)
    ElMessage.error(error.message)
    return Promise.reject(error)
  }
)

axiosInstance.interceptors.request.use(defaultRequestInterceptors)
axiosInstance.interceptors.response.use(defaultResponseInterceptors)

setupTokenRefreshInterceptor(axiosInstance)

const service = {
  request: (config: RequestConfig) => {
    return new Promise((resolve, reject) => {
      if (config.interceptors?.requestInterceptors) {
        config = config.interceptors.requestInterceptors(config as any)
      }

      axiosInstance
        .request(config)
        .then((res) => {
          resolve(res)
        })
        .catch((err: any) => {
          reject(err)
        })
    })
  },
  cancelRequest: (url: string | string[]) => {
    const urlList = Array.isArray(url) ? url : [url]
    for (const _url of urlList) {
      abortControllerMap.get(_url)?.abort()
      abortControllerMap.delete(_url)
    }
  },
  cancelAllRequest() {
    for (const [_, controller] of abortControllerMap) {
      controller.abort()
    }
    abortControllerMap.clear()
  }
}

export default service
