<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { ConfigGlobal } from '@/components/ConfigGlobal'
import { useDesign } from '@/hooks/web/useDesign'
import { ElNotification, ElMessageBox } from 'element-plus'
import ChatFloatingIcon from '@/components/ChatFloatingIcon/index.vue'
import ChatWindow from '@/components/ChatWindow/index.vue'
import NotificationCenter from '@/components/NotificationCenter/index.vue'
import { useWebSocket, type WsMessage } from '@/utils/websocket'

const { getPrefixCls } = useDesign()

const prefixCls = getPrefixCls('app')

const appStore = useAppStore()
const userStore = useUserStore()

const currentSize = computed(() => appStore.getCurrentSize)

const greyMode = computed(() => appStore.getGreyMode)

appStore.initTheme()

const ws = useWebSocket()
const chatVisible = ref(false)
const unreadCount = ref(0)
const lastChatMessage = ref<WsMessage | null>(null)

const isLoggedIn = computed(() => !!userStore.getToken)

const toggleChat = () => {
  chatVisible.value = !chatVisible.value
}

const handleUnreadChange = (count: number) => {
  unreadCount.value = count
}

ws.onChat((msg) => {
  if (
    msg.type === 'chat_message' ||
    msg.type === 'chat_room_created' ||
    msg.type === 'chat_message_deleted'
  ) {
    lastChatMessage.value = msg
    if (!chatVisible.value && msg.type !== 'chat_message_deleted') {
      unreadCount.value++
    }
  }
})

// F-11: 系统通知、踢人、强制刷新事件处理
ws.onMessage((msg: WsMessage) => {
  // 系统通知弹窗
  if (msg.type === 'system_notification' && msg.data) {
    const notifyType =
      msg.data.type === 'alert' ? 'error' : msg.data.type === 'approval' ? 'success' : 'info'
    ElNotification({
      title: msg.data.title || '系统通知',
      message: msg.data.content || '',
      type: notifyType as 'success' | 'error' | 'info' | 'warning',
      duration: msg.data.type === 'alert' ? 0 : 5000,
      position: 'top-right'
    })
  }

  // 踢出用户
  if (msg.type === 'kick_user' && msg.data) {
    ElMessageBox.alert(msg.data.reason || '您已被管理员踢出', '连接已断开', {
      type: 'warning',
      showClose: false
    }).then(() => {
      ws.disconnect()
      userStore.logout()
    })
  }

  // 强制刷新权限和菜单
  if (msg.type === 'force_refresh') {
    ElNotification({
      title: '权限更新',
      message: '您的权限已变更，页面即将刷新...',
      type: 'warning',
      duration: 3000
    })
    // 刷新页面以重新获取权限和菜单
    setTimeout(() => {
      window.location.reload()
    }, 2000)
  }
})

watch(
  isLoggedIn,
  (val) => {
    if (val) {
      ws.connect()
    } else {
      ws.disconnect()
    }
  },
  { immediate: true }
)

onUnmounted(() => {
  ws.disconnect()
})
</script>

<template>
  <ConfigGlobal :size="currentSize">
    <RouterView :class="greyMode ? `${prefixCls}-grey-mode` : ''" />
  </ConfigGlobal>
  <NotificationCenter v-if="isLoggedIn" />
  <ChatFloatingIcon
    v-if="isLoggedIn"
    :unread-count="unreadCount"
    :connected="ws.connected.value"
    :connection-state="ws.connectionState.value"
    @toggle-chat="toggleChat"
  />
  <ChatWindow
    v-if="isLoggedIn"
    :visible="chatVisible"
    :last-message="lastChatMessage"
    @close="chatVisible = false"
    @unread-change="handleUnreadChange"
  />
</template>

<style lang="less">
@prefix-cls: ~'@{adminNamespace}-app';

.size {
  width: 100%;
  height: 100%;
}

html,
body {
  padding: 0 !important;
  margin: 0;
  overflow: hidden;
  .size;

  #app {
    .size;
  }
}

.@{prefix-cls}-grey-mode {
  filter: grayscale(100%);
}
</style>
