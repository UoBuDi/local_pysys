<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useAppStore } from '@/store/modules/app'
import { useUserStore } from '@/store/modules/user'
import { ConfigGlobal } from '@/components/ConfigGlobal'
import { useDesign } from '@/hooks/web/useDesign'
import ChatFloatingIcon from '@/components/ChatFloatingIcon/index.vue'
import ChatWindow from '@/components/ChatWindow/index.vue'
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
  if (msg.type === 'chat_message' || msg.type === 'chat_room_created') {
    lastChatMessage.value = msg
    if (!chatVisible.value) {
      unreadCount.value++
    }
  }
})

watch(isLoggedIn, (val) => {
  if (val) {
    ws.connect()
  } else {
    ws.disconnect()
  }
}, { immediate: true })

onUnmounted(() => {
  ws.disconnect()
})
</script>

<template>
  <ConfigGlobal :size="currentSize">
    <RouterView :class="greyMode ? `${prefixCls}-grey-mode` : ''" />
  </ConfigGlobal>
  <ChatFloatingIcon
    v-if="isLoggedIn"
    :unread-count="unreadCount"
    :connected="ws.connected.value"
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
