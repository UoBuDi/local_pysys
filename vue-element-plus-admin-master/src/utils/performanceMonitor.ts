interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  type: 'navigation' | 'resource' | 'paint' | 'custom'
}

interface PerformanceReport {
  metrics: PerformanceMetric[]
  summary: {
    totalLoadTime: number
    domContentLoaded: number
    firstPaint: number
    firstContentfulPaint: number
    resourceCount: number
    resourceSize: number
  }
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = []
  private observers: PerformanceObserver[] = []
  private enabled = true

  constructor() {
    this.init()
  }

  private init() {
    if (typeof window === 'undefined' || !window.performance) {
      console.warn('[PerformanceMonitor] Performance API not available')
      this.enabled = false
      return
    }

    this.observeNavigation()
    this.observeResources()
    this.observePaint()
  }

  private observeNavigation() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'navigation') {
            const navEntry = entry as PerformanceNavigationTiming
            this.recordMetric(
              'page_load_time',
              navEntry.loadEventEnd - navEntry.fetchStart,
              'navigation'
            )
            this.recordMetric(
              'dom_content_loaded',
              navEntry.domContentLoadedEventEnd - navEntry.fetchStart,
              'navigation'
            )
            this.recordMetric(
              'dom_complete',
              navEntry.domComplete - navEntry.fetchStart,
              'navigation'
            )
            this.recordMetric(
              'first_byte',
              navEntry.responseStart - navEntry.fetchStart,
              'navigation'
            )
          }
        })
      })
      observer.observe({ entryTypes: ['navigation'] })
      this.observers.push(observer)
    } catch (error) {
      console.warn('[PerformanceMonitor] Navigation observer not supported')
    }
  }

  private observeResources() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'resource') {
            const resourceEntry = entry as PerformanceResourceTiming
            this.recordMetric(`resource_${resourceEntry.name}`, resourceEntry.duration, 'resource')
          }
        })
      })
      observer.observe({ entryTypes: ['resource'] })
      this.observers.push(observer)
    } catch (error) {
      console.warn('[PerformanceMonitor] Resource observer not supported')
    }
  }

  private observePaint() {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          if (entry.entryType === 'paint') {
            this.recordMetric(entry.name.replace('-', '_'), entry.startTime, 'paint')
          }
        })
      })
      observer.observe({ entryTypes: ['paint'] })
      this.observers.push(observer)
    } catch (error) {
      console.warn('[PerformanceMonitor] Paint observer not supported')
    }
  }

  recordMetric(
    name: string,
    value: number,
    type: 'navigation' | 'resource' | 'paint' | 'custom' = 'custom'
  ) {
    if (!this.enabled) return

    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      type
    }

    this.metrics.push(metric)
    console.log(`[PerformanceMonitor] ${name}: ${value.toFixed(2)}ms`)
  }

  startMeasure(name: string): () => void {
    const startTime = performance.now()

    return () => {
      const endTime = performance.now()
      const duration = endTime - startTime
      this.recordMetric(name, duration, 'custom')
    }
  }

  getMetrics(): PerformanceMetric[] {
    return [...this.metrics]
  }

  getReport(): PerformanceReport {
    const navigationTiming = performance.getEntriesByType(
      'navigation'
    )[0] as PerformanceNavigationTiming
    const paintEntries = performance.getEntriesByType('paint')
    const resourceEntries = performance.getEntriesByType('resource')

    const firstPaint = paintEntries.find((e) => e.name === 'first-paint')?.startTime || 0
    const firstContentfulPaint =
      paintEntries.find((e) => e.name === 'first-contentful-paint')?.startTime || 0

    const summary = {
      totalLoadTime: navigationTiming?.loadEventEnd || 0,
      domContentLoaded: navigationTiming?.domContentLoadedEventEnd || 0,
      firstPaint,
      firstContentfulPaint,
      resourceCount: resourceEntries.length,
      resourceSize: resourceEntries.reduce((total, entry) => {
        return total + ((entry as PerformanceResourceTiming).encodedBodySize || 0)
      }, 0)
    }

    return {
      metrics: this.getMetrics(),
      summary
    }
  }

  clearMetrics() {
    this.metrics = []
  }

  destroy() {
    this.observers.forEach((observer) => observer.disconnect())
    this.observers = []
    this.metrics = []
  }

  // 获取Web Vitals指标
  getWebVitals() {
    const navigationTiming = performance.getEntriesByType(
      'navigation'
    )[0] as PerformanceNavigationTiming
    const paintEntries = performance.getEntriesByType('paint')

    return {
      // 首次内容绘制 (FCP)
      FCP: paintEntries.find((e) => e.name === 'first-contentful-paint')?.startTime || 0,

      // 首次绘制 (FP)
      FP: paintEntries.find((e) => e.name === 'first-paint')?.startTime || 0,

      // DOM内容加载完成时间
      DCL: navigationTiming?.domContentLoadedEventEnd || 0,

      // 页面完全加载时间
      Load: navigationTiming?.loadEventEnd || 0,

      // 首字节时间 (TTFB)
      TTFB: navigationTiming?.responseStart || 0,

      // DOM交互时间
      TTI: navigationTiming?.domInteractive || 0
    }
  }

  // 获取资源加载统计
  getResourceStats() {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]

    const stats = {
      total: resources.length,
      byType: {} as Record<string, { count: number; size: number; duration: number }>,
      slowest: [] as Array<{ name: string; duration: number; size: number }>,
      largest: [] as Array<{ name: string; size: number; duration: number }>
    }

    resources.forEach((resource) => {
      const type = this.getResourceType(resource.name)

      if (!stats.byType[type]) {
        stats.byType[type] = { count: 0, size: 0, duration: 0 }
      }

      stats.byType[type].count++
      stats.byType[type].size += resource.encodedBodySize || 0
      stats.byType[type].duration += resource.duration || 0
    })

    // 最慢的资源
    stats.slowest = resources
      .map((r) => ({ name: r.name, duration: r.duration, size: r.encodedBodySize }))
      .sort((a, b) => b.duration - a.duration)
      .slice(0, 10)

    // 最大的资源
    stats.largest = resources
      .map((r) => ({ name: r.name, size: r.encodedBodySize, duration: r.duration }))
      .sort((a, b) => b.size - a.size)
      .slice(0, 10)

    return stats
  }

  private getResourceType(url: string): string {
    const ext = url.split('.').pop()?.toLowerCase() || ''

    const typeMap: Record<string, string> = {
      js: 'script',
      css: 'stylesheet',
      png: 'image',
      jpg: 'image',
      jpeg: 'image',
      gif: 'image',
      svg: 'image',
      webp: 'image',
      woff: 'font',
      woff2: 'font',
      ttf: 'font',
      eot: 'font',
      mp4: 'video',
      webm: 'video',
      mp3: 'audio',
      wav: 'audio'
    }

    return typeMap[ext] || 'other'
  }
}

export const performanceMonitor = new PerformanceMonitor()

// 导出便捷方法
export const startMeasure = (name: string) => performanceMonitor.startMeasure(name)
export const recordMetric = (name: string, value: number) =>
  performanceMonitor.recordMetric(name, value)
export const getPerformanceReport = () => performanceMonitor.getReport()
export const getWebVitals = () => performanceMonitor.getWebVitals()
export const getResourceStats = () => performanceMonitor.getResourceStats()
