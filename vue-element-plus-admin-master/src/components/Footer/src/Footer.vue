<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useDesign } from '@/hooks/web/useDesign'
import { useI18n } from '@/hooks/web/useI18n'
import { useWebSocket, WsConnectionStateLabels, WsConnectionStateColors } from '@/utils/websocket'
import type { WsConnectionState } from '@/utils/websocket'

const { getPrefixCls } = useDesign()
const { t } = useI18n()

const prefixCls = getPrefixCls('footer')

const title = computed(() => t('common.systemTitle'))

const { connect, disconnect, connected, connectionState, status } = useWebSocket()

// F-08: 6种连接状态可视化
const connectionStatus = computed(() => {
  return WsConnectionStateLabels[connectionState.value as WsConnectionState] || '未连接'
})

const connectionColor = computed(() => {
  return WsConnectionStateColors[connectionState.value as WsConnectionState] || '#F56C6C'
})

const onlineInfo = computed(() => {
  const frontend = status.frontend_count || 0
  const gui = status.gui_count || 0
  return `前端: ${frontend} | GUI: ${gui}`
})

// 免责声明滚动文本
const disclaimer = '免责声明：本数据管理系统全部界面、文字、影像资料仅供内部业务查阅参考，严禁对外提交、复制、出具作为各类证明、诉讼及仲裁证据使用；擅自对外提供产生的一切法律责任，由使用人自行承担。'

// 鼠标悬停暂停滚动
const marqueePaused = ref(false)
const onMarqueePause = () => { marqueePaused.value = true }
const onMarqueeResume = () => { marqueePaused.value = false }

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
    <!-- 左侧：版权信息 -->
    <div class="text-[var(--el-text-color-placeholder)] text-sm shrink-0">
      Copyright ©2025-present {{ title }}
    </div>
    <!-- 中间：免责声明滚动 -->
    <div class="flex-1 mx-4 overflow-hidden">
      <div class="footer-marquee" :class="{ 'footer-marquee--paused': marqueePaused }" @mouseenter="onMarqueePause" @mouseleave="onMarqueeResume">
        <span class="footer-marquee-text">{{ disclaimer }}</span>
      </div>
    </div>
    <!-- 右侧：WebSocket状态 + 在线人数 -->
    <div class="flex items-center gap-4 text-sm shrink-0">
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

<style scoped>
/* 免责声明跑马灯动画 */
.footer-marquee {
  display: flex;
  width: 100%;
  animation: footer-marquee-scroll 30s linear infinite;
}

.footer-marquee--paused {
  animation-play-state: paused;
}

.footer-marquee-text {
  white-space: nowrap;
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  padding-left: 100%;
}

@keyframes footer-marquee-scroll {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-100%);
  }
}
</style>
