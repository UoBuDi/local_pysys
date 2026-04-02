<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useDesign } from '@/hooks/web/useDesign'
import { useI18n } from '@/hooks/web/useI18n'
import { useWebSocket } from '@/utils/websocket'

const { getPrefixCls } = useDesign()
const { t } = useI18n()

const prefixCls = getPrefixCls('footer')

const title = computed(() => t('common.systemTitle'))

const { connect, disconnect, connected, status } = useWebSocket()

const connectionStatus = computed(() => {
  return connected.value ? '已连接' : '未连接'
})

const connectionColor = computed(() => {
  return connected.value ? '#67C23A' : '#F56C6C'
})

const onlineInfo = computed(() => {
  const frontend = status.frontend_count || 0
  const gui = status.gui_count || 0
  return `前端: ${frontend} | GUI: ${gui}`
})

onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<template>
  <div
    :class="prefixCls"
    class="flex items-center justify-between px-4 bg-[var(--app-content-bg-color)] h-[var(--app-footer-height)] dark:bg-[var(--el-bg-color)] overflow-hidden border-t border-[var(--el-border-color-lighter)]"
  >
    <div class="text-[var(--el-text-color-placeholder)] text-sm">
      Copyright ©2025-present {{ title }}
    </div>
    <div class="flex items-center gap-4 text-sm">
      <div class="flex items-center gap-2">
        <span class="text-[var(--el-text-color-regular)]">WebSocket:</span>
        <span :style="{ color: connectionColor }" class="font-medium">
          {{ connectionStatus }}
        </span>
      </div>
      <div class="flex items-center gap-2 text-[var(--el-text-color-regular)]">
        <span>在线:</span>
        <span class="text-[var(--el-color-primary)] font-medium">{{ onlineInfo }}</span>
      </div>
    </div>
  </div>
</template>
