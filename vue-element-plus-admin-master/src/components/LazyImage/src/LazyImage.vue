<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { propTypes } from '@/utils/propTypes'

const props = defineProps({
  src: propTypes.string.def(''),
  alt: propTypes.string.def(''),
  width: propTypes.oneOfType([Number, String]).def('100%'),
  height: propTypes.oneOfType([Number, String]).def('auto'),
  loading: propTypes.string.def(''),
  error: propTypes.string.def(''),
  lazy: propTypes.bool.def(true),
  placeholder: propTypes.string.def('')
})

const emit = defineEmits(['load', 'error'])

const imageRef = ref<HTMLImageElement>()
const isLoading = ref(true)
const hasError = ref(false)
const imageSrc = ref('')

const defaultLoading =
  'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2YwZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iIzk5OSI+TG9hZGluZy4uLjwvdGV4dD48L3N2Zz4='

const defaultError =
  'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48cmVjdCB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgZmlsbD0iI2ZmZjBmMCIvPjx0ZXh0IHg9IjUwIiB5PSI1MCIgZm9udC1zaXplPSIxMiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgZmlsbD0iI2ZmNmI2YiI+RXJyb3I8L3RleHQ+PC9zdmc+'

const styles = computed(() => {
  const width = typeof props.width === 'number' ? `${props.width}px` : props.width
  const height = typeof props.height === 'number' ? `${props.height}px` : props.height

  return {
    width,
    height
  }
})

let observer: IntersectionObserver | null = null

const loadImage = () => {
  if (!props.src) return

  isLoading.value = true
  hasError.value = false

  const img = new Image()
  img.onload = () => {
    imageSrc.value = props.src
    isLoading.value = false
    emit('load')
  }
  img.onerror = () => {
    imageSrc.value = props.error || defaultError
    hasError.value = true
    isLoading.value = false
    emit('error')
  }
  img.src = props.src
}

const handleIntersect = (entries: IntersectionObserverEntry[]) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      loadImage()
      if (observer && imageRef.value) {
        observer.unobserve(imageRef.value)
      }
    }
  })
}

const setupObserver = () => {
  if (!props.lazy) {
    loadImage()
    return
  }

  observer = new IntersectionObserver(handleIntersect, {
    root: null,
    rootMargin: '50px',
    threshold: 0.01
  })

  if (imageRef.value) {
    observer.observe(imageRef.value)
  }
}

onMounted(() => {
  setupObserver()
})

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect()
  }
})

watch(
  () => props.src,
  () => {
    if (observer && imageRef.value) {
      observer.unobserve(imageRef.value)
    }
    setupObserver()
  }
)
</script>

<template>
  <div class="lazy-image-container" :style="styles">
    <img
      ref="imageRef"
      :src="imageSrc || (isLoading ? loading || defaultLoading : '')"
      :alt="alt"
      :style="styles"
      class="lazy-image"
      :class="{
        'lazy-image-loading': isLoading,
        'lazy-image-error': hasError
      }"
    />
    <div v-if="isLoading" class="lazy-image-placeholder">
      <slot name="placeholder">
        <div class="lazy-image-loading-text">加载中...</div>
      </slot>
    </div>
    <div v-if="hasError" class="lazy-image-error-overlay">
      <slot name="error">
        <div class="lazy-image-error-text">加载失败</div>
      </slot>
    </div>
  </div>
</template>

<style scoped lang="less">
.lazy-image-container {
  position: relative;
  display: inline-block;
  overflow: hidden;
}

.lazy-image {
  display: block;
  object-fit: cover;
  transition: opacity 0.3s ease;

  &.lazy-image-loading {
    opacity: 0.3;
  }

  &.lazy-image-error {
    opacity: 0.5;
  }
}

.lazy-image-placeholder,
.lazy-image-error-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.lazy-image-loading-text,
.lazy-image-error-text {
  font-size: 12px;
  color: #999;
}

.lazy-image-error-text {
  color: #ff6b6b;
}
</style>
