<script setup lang="ts">
/**
 * 全局通知中心组件
 * 职责：通知铃铛图标 + 通知历史弹窗
 * 注意：system_notification/kick_user/force_refresh 事件处理在 App.vue 中统一管理，
 * 本组件仅负责展示通知历史和未读计数
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useWebSocket, type WsMessage } from '@/utils/websocket'
import { getNotificationHistory } from '@/api/notifications'

const ws = useWebSocket()

// 通知历史
const historyVisible = ref(false)
const historyList = ref<any[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const historyLoading = ref(false)

// 未读通知计数（仅统计 system_notification 事件）
const unreadCount = ref(0)

/** 加载通知历史 */
const loadHistory = async (page = 1) => {
  historyLoading.value = true
  historyPage.value = page
  try {
    const resp = await getNotificationHistory({ page, page_size: 10 })
    if (resp?.code === 200 && resp.data) {
      historyList.value = resp.data.records || []
      historyTotal.value = resp.data.total || 0
    }
  } catch (e) {
    console.error('加载通知历史失败:', e)
  } finally {
    historyLoading.value = false
  }
}

/** 打开通知历史（同时清零未读计数） */
const openHistory = () => {
  historyVisible.value = true
  unreadCount.value = 0
  loadHistory(1)
}

/** 通知类型映射 */
const typeMap: Record<string, { label: string; type: 'success' | 'warning' | 'error' | 'info' }> = {
  system: { label: '系统', type: 'info' },
  approval: { label: '审批', type: 'warning' },
  alert: { label: '告警', type: 'error' }
}

// 监听系统通知事件，仅更新未读计数（弹窗由 App.vue 处理）
const onMessage = (message: WsMessage) => {
  if (message.type === 'system_notification') {
    unreadCount.value++
  }
}

ws.onMessage(onMessage)
</script>

<template>
  <!-- 通知铃铛图标 -->
  <div class="notification-center" @click="openHistory">
    <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
      <el-icon :size="20" class="notification-bell">
        <svg viewBox="0 0 1024 1024" xmlns="http://www.w3.org/2000/svg">
          <path
            d="M512 64c181 0 328 147 328 328v224l64 64v32H120v-32l64-64V392C184 211 331 64 512 64zm0 64c-145.6 0-264 118.4-264 264v248H776V392c0-145.6-118.4-264-264-264zm128 672H384c0 70.7 57.3 128 128 128s128-57.3 128-128z"
            fill="currentColor"
          />
        </svg>
      </el-icon>
    </el-badge>
  </div>

  <!-- 通知历史弹窗 -->
  <el-dialog v-model="historyVisible" title="通知中心" width="600px" :append-to-body="true">
    <el-table :data="historyList" v-loading="historyLoading" stripe max-height="400" style="width: 100%">
      <el-table-column prop="type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="(typeMap[row.type]?.type as any) || 'info'" size="small">
            {{ typeMap[row.type]?.label || row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
      <el-table-column prop="content" label="内容" min-width="200" show-overflow-tooltip />
      <el-table-column prop="target_type" label="范围" width="80">
        <template #default="{ row }">
          {{ row.target_type === 'all' ? '全员' : '定向' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160" show-overflow-tooltip />
    </el-table>
    <div v-if="historyTotal > 10" style="margin-top: 12px; text-align: right">
      <el-pagination
        :current-page="historyPage"
        :page-size="10"
        :total="historyTotal"
        layout="prev, pager, next"
        @current-change="(page: number) => loadHistory(page)"
      />
    </div>
  </el-dialog>
</template>

<style scoped>
.notification-center {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 0 8px;
}

.notification-bell {
  color: var(--el-text-color-regular);
  transition: color 0.2s;
}

.notification-center:hover .notification-bell {
  color: var(--el-color-primary);
}
</style>
