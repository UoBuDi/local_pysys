import { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useUserStoreWithOut } from '@/store/modules/user'
import { refreshTokenIfNeeded, isTokenExpiringSoon, hasValidToken } from '@/utils/auth'
import router from '@/router'

const TOKEN_REFRESH_URLS = ['/api/token/refresh', '/api/login/', '/api/register/']

function shouldSkipTokenRefresh(url: string): boolean {
  return TOKEN_REFRESH_URLS.some((skipUrl) => url.includes(skipUrl))
}

export function setupTokenRefreshInterceptor(axiosInstance: AxiosInstance): void {
  axiosInstance.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      const url = config.url || ''

      if (shouldSkipTokenRefresh(url)) {
        return config
      }

      const userStore = useUserStoreWithOut()
      const token = userStore.getToken

      if (!token) {
        return config
      }

      if (!hasValidToken() || isTokenExpiringSoon()) {
        try {
          const newToken = await refreshTokenIfNeeded()
          if (newToken && config.headers) {
            config.headers.Authorization = `Bearer ${newToken}`
          }
        } catch (error) {
          console.error('请求前刷新Token失败:', error)
        }
      }

      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  axiosInstance.interceptors.response.use(
    (response: AxiosResponse) => {
      return response
    },
    async (error: AxiosError) => {
      const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

      if (!originalRequest) {
        return Promise.reject(error)
      }

      const url = originalRequest.url || ''

      if (shouldSkipTokenRefresh(url)) {
        return Promise.reject(error)
      }

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true

        try {
          const newToken = await refreshTokenIfNeeded()

          if (newToken && originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return axiosInstance(originalRequest)
          }
        } catch (refreshError) {
          console.error('401响应后刷新Token失败:', refreshError)
        }

        const userStore = useUserStoreWithOut()
        userStore.logout()
        router.push('/login')
      }

      return Promise.reject(error)
    }
  )
}
