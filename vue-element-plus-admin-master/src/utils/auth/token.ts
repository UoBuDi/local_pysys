import { useUserStoreWithOut } from '@/store/modules/user'
import { refreshTokenApi } from '@/api/login'
import router from '@/router'

const TOKEN_REFRESH_THRESHOLD = 10 * 60 * 1000
const MIN_REFRESH_INTERVAL = 120 * 1000
const MIN_TOKEN_REMAINING = 60 * 1000
const GLOBAL_LOCK_TTL = 30000

const STORAGE_KEY = '__token_refresh_state__'
const GLOBAL_LOCK_KEY = '__global_token_refresh_lock__'

interface RefreshState {
  isRefreshing: boolean
  lastRefreshTime: number
}

interface JWTPayload {
  exp: number
  sub: string
  type: string
}

type RefreshReason = 'request_interceptor' | 'response_401' | 'route_guard' | 'page_load' | 'manual'

interface TokenRefreshRequest {
  reason: RefreshReason
  timestamp: number
  resolve: (token: string | null) => void
}

function getRefreshState(): RefreshState {
  try {
    if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
      return { isRefreshing: false, lastRefreshTime: 0 }
    }
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : { isRefreshing: false, lastRefreshTime: 0 }
  } catch {
    return { isRefreshing: false, lastRefreshTime: 0 }
  }
}

function setRefreshState(state: Partial<RefreshState>): void {
  try {
    if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
      return
    }
    const current = getRefreshState()
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, ...state }))
  } catch {
    console.warn('写入Token刷新状态失败')
  }
}

function acquireGlobalLock(): boolean {
  try {
    if (typeof window === 'undefined' || typeof window.sessionStorage === 'undefined') {
      return true
    }
    const locked = sessionStorage.getItem(GLOBAL_LOCK_KEY)
    if (locked) {
      const lockTime = parseInt(locked, 10)
      if (!isNaN(lockTime) && Date.now() - lockTime < GLOBAL_LOCK_TTL) {
        return false
      }
    }
    sessionStorage.setItem(GLOBAL_LOCK_KEY, Date.now().toString())
    return true
  } catch {
    return true
  }
}

function releaseGlobalLock(): void {
  try {
    if (typeof window !== 'undefined' && typeof window.sessionStorage !== 'undefined') {
      sessionStorage.removeItem(GLOBAL_LOCK_KEY)
    }
  } catch {
    // ignore
  }
}

class TokenManagerClass {
  private isRefreshing: boolean = false
  private queue: TokenRefreshRequest[] = []
  private pendingPromise: Promise<string | null> | null = null

  async requestRefresh(reason: RefreshReason): Promise<string | null> {
    if (this.pendingPromise) {
      return new Promise((resolve) => {
        this.queue.push({ reason, timestamp: Date.now(), resolve })
      })
    }

    const state = getRefreshState()
    if (state.isRefreshing) {
      return new Promise((resolve) => {
        this.queue.push({ reason, timestamp: Date.now(), resolve })
      })
    }

    if (!acquireGlobalLock()) {
      console.warn('[TokenManager] 全局锁已被占用，跳过刷新')
      return this.getCurrentToken()
    }

    if (!this.shouldRefresh()) {
      releaseGlobalLock()
      return this.getCurrentToken()
    }

    this.pendingPromise = this.executeRefresh(reason)

    try {
      return await this.pendingPromise
    } finally {
      this.pendingPromise = null
    }
  }

  private shouldRefresh(): boolean {
    const userStore = useUserStoreWithOut()

    if (!hasValidRefreshToken()) {
      return false
    }

    if (isTokenExpired()) {
      return true
    }

    if (!isTokenExpiringSoon()) {
      return false
    }

    const remaining = getTokenRemainingTime()
    if (remaining < MIN_TOKEN_REMAINING && remaining > 0) {
      return false
    }

    const state = getRefreshState()
    if (Date.now() - state.lastRefreshTime < MIN_REFRESH_INTERVAL) {
      return false
    }

    return true
  }

  private getCurrentToken(): string | null {
    const userStore = useUserStoreWithOut()
    if (hasValidToken()) {
      return userStore.getToken
    }
    return null
  }

  private async executeRefresh(reason: RefreshReason): Promise<string | null> {
    setRefreshState({ isRefreshing: true })
    this.isRefreshing = true

    try {
      console.log(`[TokenManager] 开始执行Token刷新，原因: ${reason}`)
      const token = await this.doRefreshToken()

      while (this.queue.length > 0) {
        const request = this.queue.shift()
        request?.resolve(token)
      }

      return token
    } catch (error) {
      console.error('[TokenManager] Token刷新失败:', error)

      while (this.queue.length > 0) {
        const request = this.queue.shift()
        request?.resolve(null)
      }

      return null
    } finally {
      setRefreshState({ isRefreshing: false })
      this.isRefreshing = false
      releaseGlobalLock()
    }
  }

  private async doRefreshToken(): Promise<string | null> {
    try {
      const userStore = useUserStoreWithOut()
      const refreshToken = userStore.getRefreshToken

      if (!refreshToken) {
        console.warn('[TokenManager] 无有效的Refresh Token')
        return null
      }

      const res = await refreshTokenApi(refreshToken)

      if (res && res.code === 200 && res.data) {
        const { token, refreshToken: newRefreshToken, expiresAt, refreshExpiresAt } = res.data

        userStore.setTokenData({
          token,
          refreshToken: newRefreshToken,
          expiresAt,
          refreshExpiresAt
        })

        setRefreshState({
          isRefreshing: false,
          lastRefreshTime: Date.now()
        })

        console.log(
          `[TokenManager] Token刷新成功，新Token有效期至: ${new Date(expiresAt).toLocaleString()}`
        )
        return token
      } else {
        console.warn('[TokenManager] Token刷新返回异常:', res)
        return null
      }
    } catch (error) {
      console.error('[TokenManager] Token刷新请求异常:', error)
      return null
    }
  }

  getIsRefreshing(): boolean {
    return this.isRefreshing || getRefreshState().isRefreshing
  }

  clearQueue(): void {
    this.queue.forEach((request) => {
      try {
        request.resolve(null)
      } catch {
        // ignore
      }
    })
    this.queue = []
  }
}

export const TokenManager = new TokenManagerClass()

function decodeJWTPayload(token: string): JWTPayload | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null

    const payload = parts[1]
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )

    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

function getTokenExpFromJWT(): number | null {
  try {
    const userStore = useUserStoreWithOut()
    const token = userStore.getToken
    if (!token) return null

    const payload = decodeJWTPayload(token)
    if (!payload || !payload.exp) return null

    return payload.exp * 1000
  } catch {
    return null
  }
}

export function isTokenExpiringSoon(): boolean {
  const jwtExp = getTokenExpFromJWT()
  if (jwtExp) {
    return Date.now() > jwtExp - TOKEN_REFRESH_THRESHOLD
  }

  const userStore = useUserStoreWithOut()
  const expiresAt = userStore.getTokenExpiresAt
  if (!expiresAt || expiresAt <= 0) return false
  return Date.now() > expiresAt - TOKEN_REFRESH_THRESHOLD
}

export function isTokenExpired(): boolean {
  const jwtExp = getTokenExpFromJWT()
  if (jwtExp) {
    return Date.now() >= jwtExp
  }

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

export async function refreshTokenIfNeeded(): Promise<string | null> {
  return TokenManager.requestRefresh('request_interceptor')
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
      const newToken = await TokenManager.requestRefresh('route_guard')
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

  if (isTokenExpiringSoon() && hasValidRefreshToken()) {
    const newToken = await TokenManager.requestRefresh('route_guard')
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
      const newToken = await TokenManager.requestRefresh('page_load')
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
    await TokenManager.requestRefresh('page_load')
  }
}

export function getTokenRemainingTime(): number {
  const jwtExp = getTokenExpFromJWT()
  if (jwtExp) {
    return Math.max(0, jwtExp - Date.now())
  }

  const userStore = useUserStoreWithOut()
  const expiresAt = userStore.getTokenExpiresAt
  if (!expiresAt) return 0
  return Math.max(0, expiresAt - Date.now())
}

export function getTokenRemainingMinutes(): number {
  return Math.floor(getTokenRemainingTime() / 60000)
}
