import type { App } from 'vue'

interface LazyLoadOptions {
  root?: Element | null
  rootMargin?: string
  threshold?: number | number[]
  loading?: string
  error?: string
}

const defaultOptions: LazyLoadOptions = {
  root: null,
  rootMargin: '50px',
  threshold: 0.01,
  loading:
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzk5OSI+TG9hZGluZy4uLjwvdGV4dD48L3N2Zz4=',
  error:
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iI2ZmNmI2YiI+RXJyb3I8L3RleHQ+PC9zdmc+'
}

class LazyLoader {
  private observer: IntersectionObserver
  private options: LazyLoadOptions

  constructor(options: LazyLoadOptions = {}) {
    this.options = { ...defaultOptions, ...options }
    this.observer = new IntersectionObserver(this.handleIntersect.bind(this), {
      root: this.options.root,
      rootMargin: this.options.rootMargin,
      threshold: this.options.threshold
    })
  }

  private handleIntersect(entries: IntersectionObserverEntry[]) {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement
        this.loadImage(img)
        this.observer.unobserve(img)
      }
    })
  }

  private loadImage(img: HTMLImageElement) {
    const src = img.dataset.src
    if (!src) return

    img.src = this.options.loading || ''

    const tempImg = new Image()
    tempImg.onload = () => {
      img.src = src
      img.classList.remove('lazy-loading')
      img.classList.add('lazy-loaded')
    }
    tempImg.onerror = () => {
      img.src = this.options.error || ''
      img.classList.remove('lazy-loading')
      img.classList.add('lazy-error')
    }
    tempImg.src = src
  }

  observe(img: HTMLImageElement) {
    img.classList.add('lazy-loading')
    this.observer.observe(img)
  }

  disconnect() {
    this.observer.disconnect()
  }
}

let lazyLoader: LazyLoader | null = null

export const lazyLoadDirective = {
  mounted(el: HTMLImageElement, binding: any) {
    if (!lazyLoader) {
      lazyLoader = new LazyLoader(binding.value)
    }

    el.dataset.src = el.src
    el.src = lazyLoader['options'].loading || ''
    lazyLoader.observe(el)
  },

  unmounted() {
    if (lazyLoader) {
      lazyLoader.disconnect()
    }
  }
}

export const setupLazyLoad = (app: App<Element>, options?: LazyLoadOptions) => {
  if (!lazyLoader) {
    lazyLoader = new LazyLoader(options)
  }

  app.directive('lazy', lazyLoadDirective)
}

export { LazyLoader }
