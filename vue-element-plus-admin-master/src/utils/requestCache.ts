interface CacheItem<T> {
  data: T
  timestamp: number
  expires: number
}

class RequestCache {
  private cache = new Map<string, CacheItem<any>>()
  private defaultTTL = 5 * 60 * 1000 // 5分钟

  // 生成缓存键
  private generateKey(url: string, params?: any): string {
    const paramsStr = params ? JSON.stringify(params) : ''
    return `${url}:${paramsStr}`
  }

  // 获取缓存
  get<T>(url: string, params?: any): T | null {
    const key = this.generateKey(url, params)
    const item = this.cache.get(key)

    if (!item) return null

    // 检查是否过期
    if (Date.now() > item.timestamp + item.expires) {
      this.cache.delete(key)
      return null
    }

    console.log(`[Cache Hit] ${url}`)
    return item.data
  }

  // 设置缓存
  set<T>(url: string, data: T, params?: any, ttl?: number): void {
    const key = this.generateKey(url, params)
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expires: ttl || this.defaultTTL
    })
  }

  // 清除缓存
  clear(pattern?: string): void {
    if (!pattern) {
      this.cache.clear()
      return
    }

    const keys = Array.from(this.cache.keys())
    keys.forEach((key) => {
      if (key.includes(pattern)) {
        this.cache.delete(key)
      }
    })
  }

  // 获取缓存统计
  getStats() {
    const now = Date.now()
    let validCount = 0
    let expiredCount = 0

    this.cache.forEach((item) => {
      if (now > item.timestamp + item.expires) {
        expiredCount++
      } else {
        validCount++
      }
    })

    return {
      total: this.cache.size,
      valid: validCount,
      expired: expiredCount,
      keys: Array.from(this.cache.keys())
    }
  }

  // 清理过期缓存
  cleanup(): void {
    const now = Date.now()
    const keysToDelete: string[] = []

    this.cache.forEach((item, key) => {
      if (now > item.timestamp + item.expires) {
        keysToDelete.push(key)
      }
    })

    keysToDelete.forEach((key) => this.cache.delete(key))

    if (keysToDelete.length > 0) {
      console.log(`[Cache Cleanup] Removed ${keysToDelete.length} expired items`)
    }
  }
}

export const requestCache = new RequestCache()

// 定期清理过期缓存 (每10分钟)
if (typeof window !== 'undefined') {
  setInterval(
    () => {
      requestCache.cleanup()
    },
    10 * 60 * 1000
  )
}
