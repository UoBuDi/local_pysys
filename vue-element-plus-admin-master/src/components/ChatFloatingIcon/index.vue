<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { WsConnectionStateColors, WsConnectionStateLabels } from '@/utils/websocket'
import type { WsConnectionState } from '@/utils/websocket'

const props = defineProps<{
  unreadCount: number
  connected: boolean
  connectionState?: string
}>()

const emit = defineEmits<{
  (e: 'toggle-chat'): void
}>()

const isDragging = ref(false)
const hasDragged = ref(false)
const position = reactive({ x: 0, y: 0 })
const dragStart = reactive({ x: 0, y: 0 })

const STORAGE_KEY = 'chat_icon_position'

// F-08: 使用6种连接状态的颜色和标签
const connectionClass = computed(() => {
  const state = (props.connectionState || 'disconnected') as WsConnectionState
  switch (state) {
    case 'connected':
      return 'chat-floating-icon--connected'
    case 'connecting':
    case 'reconnecting':
      return 'chat-floating-icon--connecting'
    case 'ssl_error':
    case 'protocol_mismatch':
      return 'chat-floating-icon--error'
    default:
      return 'chat-floating-icon--disconnected'
  }
})

const glowColor = computed(() => {
  const state = (props.connectionState || 'disconnected') as WsConnectionState
  return WsConnectionStateColors[state] || '#F56C6C'
})

const connectionTooltip = computed(() => {
  const state = (props.connectionState || 'disconnected') as WsConnectionState
  return WsConnectionStateLabels[state] || '未连接'
})

const loadPosition = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      position.x = parsed.x
      position.y = parsed.y
      return
    }
  } catch {
    /* ignore */
  }
  position.x = window.innerWidth - 80
  position.y = window.innerHeight - 100
}

const savePosition = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ x: position.x, y: position.y }))
}

const snapToEdge = () => {
  const threshold = window.innerWidth / 2
  const edgeMargin = 16
  if (position.x < threshold) {
    position.x = edgeMargin
  } else {
    position.x = window.innerWidth - 52 - edgeMargin
  }
  if (position.y < 16) position.y = 16
  if (position.y > window.innerHeight - 68) position.y = window.innerHeight - 68
  savePosition()
}

const onMouseDown = (e: MouseEvent) => {
  hasDragged.value = false
  dragStart.x = e.clientX - position.x
  dragStart.y = e.clientY - position.y
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  e.preventDefault()
}

const onMouseMove = (e: MouseEvent) => {
  const dx = e.clientX - dragStart.x - position.x
  const dy = e.clientY - dragStart.y - position.y
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    hasDragged.value = true
    isDragging.value = true
  }
  position.x = e.clientX - dragStart.x
  position.y = e.clientY - dragStart.y
}

const onMouseUp = () => {
  document.removeEventListener('mousemove', onMouseMove)
  document.removeEventListener('mouseup', onMouseUp)
  if (hasDragged.value) {
    snapToEdge()
  }
  setTimeout(() => {
    isDragging.value = false
  }, 100)
}

const onTouchStart = (e: TouchEvent) => {
  hasDragged.value = false
  const touch = e.touches[0]
  dragStart.x = touch.clientX - position.x
  dragStart.y = touch.clientY - position.y
  document.addEventListener('touchmove', onTouchMove, { passive: false })
  document.addEventListener('touchend', onTouchEnd)
}

const onTouchMove = (e: TouchEvent) => {
  e.preventDefault()
  const touch = e.touches[0]
  const dx = touch.clientX - dragStart.x - position.x
  const dy = touch.clientY - dragStart.y - position.y
  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
    hasDragged.value = true
    isDragging.value = true
  }
  position.x = touch.clientX - dragStart.x
  position.y = touch.clientY - dragStart.y
}

const onTouchEnd = () => {
  document.removeEventListener('touchmove', onTouchMove)
  document.removeEventListener('touchend', onTouchEnd)
  if (hasDragged.value) {
    snapToEdge()
  }
  setTimeout(() => {
    isDragging.value = false
  }, 100)
}

const onClick = () => {
  if (!hasDragged.value) {
    emit('toggle-chat')
  }
}

const handleResize = () => {
  if (position.x > window.innerWidth - 52) {
    position.x = window.innerWidth - 52 - 16
  }
  if (position.y > window.innerHeight - 68) {
    position.y = window.innerHeight - 68
  }
}

onMounted(() => {
  loadPosition()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div
    class="chat-floating-icon"
    :class="[connectionClass, { 'chat-floating-icon--dragging': isDragging }]"
    :style="{ left: position.x + 'px', top: position.y + 'px', '--glow-color': glowColor }"
    :title="connectionTooltip"
    @mousedown="onMouseDown"
    @touchstart="onTouchStart"
    @click="onClick"
  >
    <svg
      viewBox="0 0 24 24"
      width="26"
      height="26"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
    <span v-if="unreadCount > 0" class="chat-floating-icon__badge">
      {{ unreadCount > 99 ? '99+' : unreadCount }}
    </span>
  </div>
</template>

<style lang="less" scoped>
.chat-floating-icon {
  position: fixed;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  cursor: grab;
  user-select: none;
  transition:
    box-shadow 0.3s,
    transform 0.2s;
  z-index: 9999;

  &:active,
  &--dragging {
    cursor: grabbing;
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.35);
  }

  &--connected {
    box-shadow:
      0 0 0 3px rgba(103, 194, 58, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.25);
  }

  &--connecting {
    background: var(--el-color-warning);
    box-shadow:
      0 0 0 3px rgba(230, 162, 60, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.25);
    animation: pulse-glow 1.5s ease-in-out infinite;
  }

  &--error {
    background: #e6a23c;
    box-shadow:
      0 0 0 3px rgba(230, 162, 60, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.25);
  }

  &--disconnected {
    background: #909399;
    box-shadow:
      0 0 0 3px rgba(245, 108, 108, 0.3),
      0 4px 12px rgba(0, 0, 0, 0.2);
  }

  &__badge {
    position: absolute;
    top: -4px;
    right: -4px;
    min-width: 18px;
    height: 18px;
    line-height: 18px;
    border-radius: 9px;
    background: #f56c6c;
    color: #fff;
    font-size: 11px;
    text-align: center;
    padding: 0 4px;
    pointer-events: none;
  }
}

@keyframes pulse-glow {
  0%,
  100% {
    box-shadow:
      0 0 0 3px rgba(230, 162, 60, 0.4),
      0 4px 12px rgba(0, 0, 0, 0.25);
  }
  50% {
    box-shadow:
      0 0 0 6px rgba(230, 162, 60, 0.2),
      0 4px 16px rgba(0, 0, 0, 0.3);
  }
}
</style>
