import { useUserStoreWithOut } from '@/store/modules/user'
import { refreshTokenApi } from '@/api/login'
import router from '@/router'

const TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000

let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []
let lastRefreshTime = 0
const MIN_REFRESH_INTERVAL = 60 * 1000

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

function onRefreshFailed() {
  refreshSubscribers = []
}

export function isTokenExpiringSoon(): boolean {
  const userStore = useUserStoreWithOut()
  const expiresAt = userStore.getTokenExpiresAt
  if (!expiresAt || expiresAt <= 0) return false
  return Date.now() > expiresAt - TOKEN_REFRESH_THRESHOLD
}

export function isTokenExpired(): boolean {
  const userStore = useUserStoreWithOut()
  const expiresAt = userStore.getTokenExpiresAt
  if (!expiresAt || expiresAt <= 0) return false
  return Date.now() >= expiresAt
}

export function isRefreshTokenExpired(): boolean {
  const userStore = useUserStoreWithOut()
  const refreshExpiresAt = userStore.getRefreshExpiresAt
  if (!refreshExpiresAt || refreshExpiresAt <= 0) return false
  return Date.now() >= refreshExpiresAt
}

export function hasValidToken(): boolean {
  const userStore = useUserStoreWithOut()
  const token = userStore.getToken
  return !!token && !isTokenExpired()
}

export function hasValidRefreshToken(): boolean {
  const userStore = useUserStoreWithOut()
  const refreshToken = userStore.getRefreshToken
  return !!refreshToken && !isRefreshTokenExpired()
}

function canRefresh(): boolean {
  return Date.now() - lastRefreshTime >= MIN_REFRESH_INTERVAL
}

export async function refreshTokenIfNeeded(): Promise<string | null> {
  const userStore = useUserStoreWithOut()

  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token) => resolve(token))
    })
  }

  if (!hasValidRefreshToken()) {
    return null
  }

  if (!canRefresh() && hasValidToken()) {
    return userStore.getToken
  }

  isRefreshing = true

  try {
    const refreshToken = userStore.getRefreshToken
    const res = await refreshTokenApi(refreshToken)

    if (res && res.code === 200 && res.data) {
      const { token, refreshToken: newRefreshToken, expiresAt, refreshExpiresAt } = res.data

      userStore.setTokenData({
        token,
        refreshToken: newRefreshToken,
        expiresAt,
        refreshExpiresAt
      })

      lastRefreshTime = Date.now()
      onTokenRefreshed(token)
      return token
    } else {
      onRefreshFailed()
      return null
    }
  } catch (error) {
    console.error('刷新Token失败:', error)
    onRefreshFailed()
    return null
  } finally {
    isRefreshing = false
  }
}

export interface TokenCheckResult {
  valid: boolean
  refreshed: boolean
  shouldLogout: boolean
}

export async function checkAndRefreshToken(): Promise<TokenCheckResult> {
  const userStore = useUserStoreWithOut()
  const token = userStore.getToken

  if (!token) {
    localStorage.removeItem('user')
    return { valid: false, refreshed: false, shouldLogout: true }
  }

  if (isTokenExpired()) {
    if (hasValidRefreshToken()) {
      const newToken = await refreshTokenIfNeeded()
      if (newToken) {
        return { valid: true, refreshed: true, shouldLogout: false }
      } else {
        localStorage.removeItem('user')
        return { valid: false, refreshed: false, shouldLogout: true }
      }
    } else {
      localStorage.removeItem('user')
      return { valid: false, refreshed: false, shouldLogout: true }
    }
  }

  if (isTokenExpiringSoon() && hasValidRefreshToken() && canRefresh()) {
    const newToken = await refreshTokenIfNeeded()
    if (newToken) {
      return { valid: true, refreshed: true, shouldLogout: false }
    }
  }

  return { valid: true, refreshed: false, shouldLogout: false }
}

export async function checkTokenOnPageLoad(): Promise<void> {
  const userStore = useUserStoreWithOut()
  const token = userStore.getToken

  if (!token) return

  if (isTokenExpired()) {
    if (hasValidRefreshToken()) {
      const newToken = await refreshTokenIfNeeded()
      if (!newToken) {
        localStorage.removeItem('user')
        router.push('/login')
      }
    } else {
      localStorage.removeItem('user')
      userStore.logout()
      router.push('/login')
    }
    return
  }

  if (isTokenExpiringSoon() && hasValidRefreshToken()) {
    await refreshTokenIfNeeded()
  }
}

export function getTokenRemainingTime(): number {
  const userStore = useUserStoreWithOut()
  const expiresAt = userStore.getTokenExpiresAt
  if (!expiresAt) return 0
  return Math.max(0, expiresAt - Date.now())
}

export function getTokenRemainingMinutes(): number {
  return Math.floor(getTokenRemainingTime() / 60000)
}

export { isRefreshing }
