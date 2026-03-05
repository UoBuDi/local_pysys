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
              <el-form-item :label="$t('systemTools.selectSyncMonth') ">
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
            
            <div class="month-checkbox-group">
              <el-checkbox 
                v-for="month in availableMonths" 
                :key="month" 
                :model-value="selectedMonths.includes(month)"
                @change="(val) => toggleMonthSelection(month, val)"
                class="month-checkbox"
              >
                {{ month }}
              </el-checkbox>
            </div>
          </div>
          
          <!-- 控制按钮 -->
          <div class="control-buttons">
            <el-button type="primary" @click="startSync" :disabled="syncInProgress">
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
              <el-button size="small" @click="clearLogs">{{ $t('systemTools.clearLogs') }}</el-button>
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

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  name: 'SyncControl'
})
</script>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue';
import { ElMessage, ElMessageBox, ElCard, ElRow, ElCol, ElButton, ElProgress, ElDatePicker, ElForm, ElFormItem, ElDescriptions, ElDescriptionsItem, ElTag, ElCheckbox } from 'element-plus';
import { useI18n } from 'vue-i18n';
import axios from 'axios';

const { t } = useI18n();

// 使用环境变量设置API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_PATH || 'http://localhost:8000';

interface LogEntry {
  timestamp: string;
  type: string;
  message: string;
}

interface SyncStatus {
  status: string;
  progress: string;
  currentMonth: string;
  lastUpdate: string;
}

// 月份选择相关
const availableMonths = ref<string[]>([]);
const selectedMonths = ref<string[]>([]);

// 同步状态
const syncStatus = reactive<SyncStatus>({
  status: 'IDLE',
  progress: '0%',
  currentMonth: '',
  lastUpdate: ''
});

// 日志相关
const logs = ref<LogEntry[]>([]);
const logContainer = ref<HTMLElement | null>(null);

// WebSocket连接
let syncProgressWs: WebSocket | null = null;
let logsWs: WebSocket | null = null;

// 定时器
let statusTimer: number | null = null;

// 获取可用的同步月份列表
const fetchAvailableMonths = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/sync/months/`)
    
    if (response.data.code === 200) {
      availableMonths.value = response.data.data || []
      addLog('INFO', t('systemTools.availableMonthsLoaded'))
    } else {
      throw new Error(response.data.message || t('systemTools.failedToLoadMonths'))
    }
  } catch (error: any) {
    console.error(t('systemTools.fetchMonthsFailed'), error)
    ElMessage.error(error.message || t('systemTools.requestFailed'))
    addLog('ERROR', `${t('systemTools.fetchMonthsFailed')}: ${error.message || t('systemTools.unknownError')}`)
  }
}

// 获取同步状态
const fetchSyncStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/sync/status/`)
    
    if (response.data.code === 200) {
      const statusData = response.data.data
      syncStatus.status = statusData.status || t('systemTools.unknown')
      syncStatus.progress = statusData.progress || '0%'
      syncStatus.currentMonth = statusData.current_month || ''
      syncStatus.lastUpdate = statusData.last_update || ''
    } else {
      throw new Error(response.data.message || t('systemTools.failedToLoadStatus'))
    }
  } catch (error: any) {
    // 静默处理状态获取错误，避免日志刷屏
    console.debug(t('systemTools.fetchStatusFailed'), error)
  }
};

// 添加日志条目
const addLog = (type: string, message: string) => {
  const now = new Date();
  logs.value.push({
    timestamp: now.toISOString().replace('T', ' ').substring(0, 19),
    type: type,
    message: message
  });
  
  // 自动滚动到底部
  setTimeout(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight;
    }
  }, 0);
};

// 开始同步
const startSync = async () => {
  if (selectedMonths.value.length === 0) {
    ElMessage.warning(t('systemTools.selectMonthWarning'))
    return
  }

  try {
    // 更新状态
    syncStatus.status = t('systemTools.running')
    syncStatus.progress = '0%'
    syncStatus.currentMonth = selectedMonths.value[0]
    syncStatus.lastUpdate = new Date().toLocaleString()

    // 发送开始同步请求
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
    
    // 重置状态
    syncStatus.status = t('systemTools.error')
  }
};

// 暂停同步
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

// 停止同步
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

// 强制停止同步
const forceStopSync = async () => {
  ElMessageBox.confirm(
    t('systemTools.forceStopConfirm'),
    t('systemTools.warning'),
    {
      confirmButtonText: t('systemTools.confirm'),
      cancelButtonText: t('systemTools.cancel'),
      type: 'warning'
    }
  ).then(async () => {
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
  }).catch(() => {
    // 用户取消操作
  })
}

// 刷新日志
const refreshLogs = () => {
  addLog('INFO', '手动刷新日志');
};

// 清空日志
const clearLogs = () => {
  logs.value = [];
  addLog('INFO', '日志已清空');
};

// 导出日志
const exportLogs = () => {
  const logText = logs.value.map(log => `[${log.timestamp}] ${log.type}: ${log.message}`).join('\n')
  const blob = new Blob([logText], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `sync_logs_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
  addLog('INFO', t('systemTools.logsExported'))
}

// 连接WebSocket
const connectWebSocket = () => {
  // 同步进度WebSocket
  syncProgressWs = new WebSocket(`ws://${window.location.hostname}:8003/ws/sync-progress/`)
  
  syncProgressWs.onopen = () => {
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
  
  syncProgressWs.onerror = (error: Event) => {
    console.error(t('systemTools.websocketConnectionError'), error)
    const errorMessage = (error as any).message || t('systemTools.unknownError')
    addLog('ERROR', `${t('systemTools.websocketConnectionError')}: ${errorMessage}`)
  }
  
  syncProgressWs.onclose = () => {
    console.log(t('systemTools.websocketConnectionClosed'))
    addLog('INFO', t('systemTools.syncProgressServiceDisconnected'))
  }
  
  // 日志WebSocket
  logsWs = new WebSocket(`ws://${window.location.hostname}:8003/ws/logs/`)
  
  logsWs.onopen = () => {
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
  
  logsWs.onerror = (error: Event) => {
    console.error(t('systemTools.logWebsocketError'), error)
    const errorMessage = (error as any).message || t('systemTools.unknownError')
    addLog('ERROR', `${t('systemTools.logWebsocketError')}: ${errorMessage}`)
  }
  
  logsWs.onclose = () => {
    console.log(t('systemTools.logWebsocketClosed'))
    addLog('INFO', t('systemTools.logServiceDisconnected'))
  }
};

// 断开WebSocket连接
const disconnectWebSocket = () => {
  if (syncProgressWs) {
    syncProgressWs.close()
    syncProgressWs = null
  }
  
  if (logsWs) {
    logsWs.close()
    logsWs = null
  }
}

// 组件挂载时的操作
onMounted(() => {
  // 获取可用月份和同步状态
  fetchAvailableMonths()
  fetchSyncStatus()
  
  // 连接WebSocket
  connectWebSocket()
  
  // 定时更新状态
  statusTimer = window.setInterval(fetchSyncStatus, 3000)
  
  // 添加初始日志
  addLog('INFO', t('systemTools.syncControlPageLoaded'))
});

// 组件卸载前的操作
onBeforeUnmount(() => {
  // 清除定时器
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  
  // 断开WebSocket连接
  disconnectWebSocket()
});

// 计算属性
const syncInProgress = computed(() => {
  return syncStatus.status === t('systemTools.running') || 
         syncStatus.status === t('systemTools.paused');
});

// 辅助函数
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
};

// 切换月份选择
const toggleMonthSelection = (month: string, checked: any) => {
  if (checked) {
    // 添加月份到选中列表
    if (!selectedMonths.value.includes(month)) {
      selectedMonths.value.push(month);
    }
  } else {
    // 从选中列表中移除月份
    const index = selectedMonths.value.indexOf(month);
    if (index > -1) {
      selectedMonths.value.splice(index, 1);
    }
  }
};

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

.month-checkbox-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 10px;
}

.month-checkbox {
  margin-right: 0;
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

.status-message {
  margin-top: 10px;
  font-weight: bold;
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