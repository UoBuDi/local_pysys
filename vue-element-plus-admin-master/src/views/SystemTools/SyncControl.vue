<template>
  <div class="sync-control">
    <el-row :gutter="20">
      <!-- 左侧控制面板 -->
      <el-col :span="12">
        <el-card class="control-panel">
          <template #header>
            <div class="card-header">
              <span>{{ $t('systemTools.syncControl') }}</span>
            </div>
          </template>

          <!-- 月份选择 -->
          <div class="month-selection">
            <el-form>
              <el-form-item :label="$t('systemTools.selectSyncMonth')">
                <el-date-picker
                  v-model="selectedMonths"
                  type="months"
                  multiple
                  :placeholder="$t('systemTools.pleaseSelectSyncMonth')"
                  format="YYYY-MM"
                  value-format="YYYY-MM"
                  style="width: 100%"
                />
              </el-form-item>
            </el-form>
          </div>

          <!-- 控制按钮 -->
          <div class="control-buttons">
            <el-button type="primary" @click="startSync" :disabled="syncInProgress" :loading="startSyncLoading">
              {{ $t('systemTools.startSync') }}
            </el-button>
            <el-button @click="pauseSync" :disabled="!syncInProgress">
              {{ $t('systemTools.pauseSync') }}
            </el-button>
            <el-button @click="stopSync" :disabled="!syncInProgress">
              {{ $t('systemTools.stopSync') }}
            </el-button>
            <el-button type="danger" @click="forceStopSync" :disabled="!syncInProgress">
              {{ $t('systemTools.forceStopSync') }}
            </el-button>
          </div>

          <!-- 同步状态显示 -->
          <div class="sync-status">
            <el-descriptions :title="$t('systemTools.syncStatus')" :column="1" border>
              <el-descriptions-item :label="$t('systemTools.currentStatus')">
                <el-tag :type="getStatusTagType(syncStatus.status)">
                  {{ syncStatus.status }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('systemTools.currentMonth')">
                {{ syncStatus.currentMonth || $t('systemTools.none') }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('systemTools.progress')">
                {{ syncStatus.progress }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('systemTools.lastUpdateTime')">
                {{ syncStatus.lastUpdate }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧日志面板 -->
      <el-col :span="12">
        <el-card class="log-panel">
          <template #header>
            <div class="card-header">
              <span>{{ $t('systemTools.syncLogs') }}</span>
              <el-button size="small" @click="clearLogs">{{
                $t('systemTools.clearLogs')
              }}</el-button>
            </div>
          </template>

          <div class="log-content" ref="logContainer">
            <div
              v-for="(log, index) in logs"
              :key="index"
              :class="['log-entry', log.type + '-log']"
            >
              [{{ log.timestamp }}] {{ log.type.toUpperCase() }}: {{ log.message }}
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_PATH || 'http://localhost:8000'
const WS_MAX_RECONNECT = 10
const WS_BASE_DELAY = 3000

const { t } = useI18n()

interface LogEntry {
  timestamp: string
  type: string
  message: string
}

interface SyncStatusData {
  status: string
  progress: string
  currentMonth: string
  lastUpdate: string
}

const selectedMonths = ref<string[]>([])
const startSyncLoading = ref(false)

const syncStatus = reactive<SyncStatusData>({
  status: 'IDLE',
  progress: '0%',
  currentMonth: '',
  lastUpdate: ''
})

const logs = ref<LogEntry[]>([])
const logContainer = ref<HTMLElement | null>(null)

let syncProgressWs: WebSocket | null = null
let logsWs: WebSocket | null = null
let syncWsReconnectAttempts = 0
let logsWsReconnectAttempts = 0
let wsIntentionalClose = false
let statusTimer: number | null = null

const getWsReconnectDelay = (attempts: number) => {
  const delay = WS_BASE_DELAY * Math.pow(2, attempts)
  return Math.min(delay, 60000)
}

const buildWsBaseUrl = () => {
  const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws'
  return `${wsProtocol}://${API_BASE_URL.replace(/^https?:\/\//, '')}`
}

const addLog = (type: string, message: string) => {
  const now = new Date()
  logs.value.push({
    timestamp: now.toISOString().replace('T', ' ').substring(0, 19),
    type,
    message
  })
  setTimeout(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }, 0)
}

const fetchAvailableMonths = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/sync/months/`)
    if (response.data.code === 200) {
      addLog('INFO', t('systemTools.availableMonthsLoaded'))
    }
  } catch (error: any) {
    console.error(t('systemTools.fetchMonthsFailed'), error)
    addLog('ERROR', `${t('systemTools.fetchMonthsFailed')}: ${error.message || t('systemTools.unknownError')}`)
  }
}

const fetchSyncStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/sync/status/`)
    if (response.data.code === 200) {
      const statusData = response.data.data
      syncStatus.status = statusData.status || t('systemTools.unknown')
      syncStatus.progress = statusData.progress || '0%'
      syncStatus.currentMonth = statusData.current_month || ''
      syncStatus.lastUpdate = statusData.last_update || ''
    }
  } catch (error: any) {
    console.debug(t('systemTools.fetchStatusFailed'), error)
  }
}

const startSync = async () => {
  if (selectedMonths.value.length === 0) {
    ElMessage.warning(t('systemTools.selectMonthWarning'))
    return
  }

  startSyncLoading.value = true
  try {
    syncStatus.status = t('systemTools.running')
    syncStatus.progress = '0%'
    syncStatus.currentMonth = selectedMonths.value[0]
    syncStatus.lastUpdate = new Date().toLocaleString()

    const response = await axios.post(`${API_BASE_URL}/api/start-sync/`, {
      months: selectedMonths.value
    })

    if (response.data.code === 200) {
      ElMessage.success(response.data.message || t('systemTools.syncStarted'))
      addLog('INFO', response.data.message || t('systemTools.syncStarted'))
    } else {
      throw new Error(response.data.message || t('systemTools.unknownError'))
    }
  } catch (error: any) {
    console.error(t('systemTools.syncStartFailed'), error)
    ElMessage.error(error.message || t('systemTools.requestFailed'))
    addLog('ERROR', `${t('systemTools.syncStartFailed')}: ${error.message || t('systemTools.unknownError')}`)
    syncStatus.status = t('systemTools.error')
  } finally {
    startSyncLoading.value = false
  }
}

const pauseSync = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/pause-sync/`)
    if (response.data.code === 200) {
      syncStatus.status = t('systemTools.paused')
      ElMessage.success(response.data.message || t('systemTools.syncPaused'))
      addLog('INFO', response.data.message || t('systemTools.syncPaused'))
    } else {
      throw new Error(response.data.message || t('systemTools.unknownError'))
    }
  } catch (error: any) {
    console.error(t('systemTools.syncPauseFailed'), error)
    ElMessage.error(error.message || t('systemTools.requestFailed'))
    addLog('ERROR', `${t('systemTools.syncPauseFailed')}: ${error.message || t('systemTools.unknownError')}`)
  }
}

const stopSync = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/api/stop-sync/`)
    if (response.data.code === 200) {
      syncStatus.status = t('systemTools.stopped')
      ElMessage.success(response.data.message || t('systemTools.syncStopped'))
      addLog('INFO', response.data.message || t('systemTools.syncStopped'))
    } else {
      throw new Error(response.data.message || t('systemTools.unknownError'))
    }
  } catch (error: any) {
    console.error(t('systemTools.syncStopFailed'), error)
    ElMessage.error(error.message || t('systemTools.requestFailed'))
    addLog('ERROR', `${t('systemTools.syncStopFailed')}: ${error.message || t('systemTools.unknownError')}`)
  }
}

const forceStopSync = async () => {
  ElMessageBox.confirm(t('systemTools.forceStopConfirm'), t('systemTools.warning'), {
    confirmButtonText: t('systemTools.confirm'),
    cancelButtonText: t('systemTools.cancel'),
    type: 'warning'
  })
    .then(async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/force-stop-sync/`)
        if (response.data.code === 200) {
          syncStatus.status = t('systemTools.stopped')
          ElMessage.success(response.data.message || t('systemTools.syncForceStopped'))
          addLog('INFO', response.data.message || t('systemTools.syncForceStopped'))
        } else {
          throw new Error(response.data.message || t('systemTools.unknownError'))
        }
      } catch (error: any) {
        console.error(t('systemTools.syncForceStopFailed'), error)
        ElMessage.error(error.message || t('systemTools.requestFailed'))
        addLog('ERROR', `${t('systemTools.syncForceStopFailed')}: ${error.message || t('systemTools.unknownError')}`)
      }
    })
    .catch(() => {})
}

const clearLogs = () => {
  logs.value = []
  addLog('INFO', '日志已清空')
}

const connectSyncProgressWs = () => {
  if (wsIntentionalClose) return

  const wsBaseUrl = buildWsBaseUrl()
  syncProgressWs = new WebSocket(`${wsBaseUrl}/ws/sync-progress/`)

  syncProgressWs.onopen = () => {
    syncWsReconnectAttempts = 0
    addLog('INFO', t('systemTools.connectedToSyncProgress'))
  }

  syncProgressWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type === 'progress') {
        syncStatus.progress = data.progress || '0%'
      }
    } catch (e) {
      console.error(t('systemTools.failedToParseWebSocketMessage'), e)
    }
  }

  syncProgressWs.onerror = () => {
    addLog('ERROR', t('systemTools.websocketConnectionError'))
  }

  syncProgressWs.onclose = () => {
    addLog('INFO', t('systemTools.syncProgressServiceDisconnected'))
    if (!wsIntentionalClose && syncWsReconnectAttempts < WS_MAX_RECONNECT) {
      syncWsReconnectAttempts++
      const delay = getWsReconnectDelay(syncWsReconnectAttempts)
      setTimeout(connectSyncProgressWs, delay)
    }
  }
}

const connectLogsWs = () => {
  if (wsIntentionalClose) return

  const wsBaseUrl = buildWsBaseUrl()
  logsWs = new WebSocket(`${wsBaseUrl}/ws/logs/`)

  logsWs.onopen = () => {
    logsWsReconnectAttempts = 0
    addLog('INFO', t('systemTools.connectedToLogService'))
  }

  logsWs.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      if (data.type && data.message) {
        addLog(data.type, data.message)
      }
    } catch (e) {
      console.error(t('systemTools.failedToParseLogMessage'), e)
    }
  }

  logsWs.onerror = () => {
    addLog('ERROR', t('systemTools.logWebsocketError'))
  }

  logsWs.onclose = () => {
    addLog('INFO', t('systemTools.logServiceDisconnected'))
    if (!wsIntentionalClose && logsWsReconnectAttempts < WS_MAX_RECONNECT) {
      logsWsReconnectAttempts++
      const delay = getWsReconnectDelay(logsWsReconnectAttempts)
      setTimeout(connectLogsWs, delay)
    }
  }
}

const disconnectWebSocket = () => {
  wsIntentionalClose = true
  if (syncProgressWs) {
    syncProgressWs.close()
    syncProgressWs = null
  }
  if (logsWs) {
    logsWs.close()
    logsWs = null
  }
}

onMounted(() => {
  fetchAvailableMonths()
  fetchSyncStatus()
  connectSyncProgressWs()
  connectLogsWs()
  statusTimer = window.setInterval(fetchSyncStatus, 3000)
  addLog('INFO', t('systemTools.syncControlPageLoaded'))
})

onBeforeUnmount(() => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  disconnectWebSocket()
})

const syncInProgress = computed(() => {
  return syncStatus.status === t('systemTools.running') || syncStatus.status === t('systemTools.paused')
})

const getStatusTagType = (status: string) => {
  switch (status) {
    case t('systemTools.running'):
      return 'success'
    case t('systemTools.paused'):
      return 'warning'
    case t('systemTools.stopped'):
      return 'info'
    case t('systemTools.error'):
      return 'danger'
    default:
      return 'info'
  }
}
</script>

<style scoped>
.sync-control {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.month-selection {
  margin-bottom: 20px;
}

.control-buttons {
  margin: 20px 0;
}

.control-buttons .el-button {
  margin-right: 10px;
}

.sync-status {
  margin-top: 20px;
}

.log-panel {
  height: 100%;
}

.log-content {
  height: 400px;
  overflow-y: auto;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.log-entry {
  font-family: monospace;
  font-size: 12px;
  margin-bottom: 5px;
  padding: 2px 0;
}

.error-log {
  color: #f56c6c;
}

.info-log {
  color: #409eff;
}

.warn-log {
  color: #e6a23c;
}
</style>
