class RequestDedup {
  private pendingRequests = new Map<string, Promise<any>>()

  // 生成请求键
  private generateKey(config: any): string {
    const { url, method, params, data } = config
    return `${method || 'GET'}:${url}:${JSON.stringify(params)}:${JSON.stringify(data)}`
  }

  // 包装请求
  async wrap<T>(config: any, requestFn: () => Promise<T>): Promise<T> {
    const key = this.generateKey(config)

    // 如果有相同的请求正在进行，返回该Promise
    if (this.pendingRequests.has(key)) {
      console.log(`[Request Dedup] Reusing pending request: ${config.url}`)
      return this.pendingRequests.get(key) as Promise<T>
    }

    // 发起新请求
    const promise = requestFn().finally(() => {
      this.pendingRequests.delete(key)
    })

    this.pendingRequests.set(key, promise)
    return promise
  }

  // 取消请求
  cancel(url?: string): void {
    if (!url) {
      this.pendingRequests.clear()
      console.log('[Request Dedup] All pending requests cleared')
      return
    }

    const keys = Array.from(this.pendingRequests.keys())
    let cancelledCount = 0

    keys.forEach((key) => {
      if (key.includes(url)) {
        this.pendingRequests.delete(key)
        cancelledCount++
      }
    })

    if (cancelledCount > 0) {
      console.log(`[Request Dedup] Cancelled ${cancelledCount} requests for ${url}`)
    }
  }

  // 获取待处理请求数量
  getPendingCount(): number {
    return this.pendingRequests.size
  }

  // 获取待处理请求详情
  getPendingRequests(): string[] {
    return Array.from(this.pendingRequests.keys())
  }

  // 检查是否有待处理的请求
  hasPending(url: string): boolean {
    const keys = Array.from(this.pendingRequests.keys())
    return keys.some((key) => key.includes(url))
  }
}

export const requestDedup = new RequestDedup()
