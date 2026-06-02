<template>
  <div class="sync-config">
    <el-tabs v-model="activeTab" type="card">
      <!-- 数据库配置标签页 -->
      <el-tab-pane :label="$t('systemTools.dbConfig')" name="database">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="database-card">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('systemTools.sourceDb') }}</span>
                </div>
              </template>

              <el-form
                label-width="120px"
                :model="remoteDbForm"
                ref="remoteFormRef"
                :rules="dbFormRules"
              >
                <el-form-item :label="$t('systemTools.host')" prop="host">
                  <el-input v-model="remoteDbForm.host" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.port')" prop="port">
                  <el-input-number
                    v-model="remoteDbForm.port"
                    controls-position="right"
                    :min="1"
                    :max="65535"
                  />
                </el-form-item>
                <el-form-item :label="$t('systemTools.username')" prop="username">
                  <el-input v-model="remoteDbForm.username" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.password')">
                  <el-input
                    v-model="remoteDbForm.password"
                    type="password"
                    show-password
                    :placeholder="remotePasswordMasked ? $t('systemTools.passwordMaskedHint') : ''"
                    @input="onPasswordInput('remote')"
                  />
                </el-form-item>
                <el-form-item :label="$t('systemTools.database')" prop="database">
                  <el-input v-model="remoteDbForm.database" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.charset')">
                  <el-select
                    v-model="remoteDbForm.charset"
                    :placeholder="$t('systemTools.selectCharset')"
                  >
                    <el-option label="UTF-8" value="utf8mb4" />
                    <el-option label="UTF-8 (兼容)" value="utf8" />
                    <el-option label="GBK" value="gbk" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    @click="testRemoteConnection"
                    :loading="remoteTestLoading"
                    v-hasPermi="'system:sync:config'"
                  >
                    {{ $t('systemTools.testConnection') }}
                  </el-button>
                  <el-button
                    @click="showRemoteTables"
                    :loading="remoteTablesLoading"
                    v-hasPermi="'system:sync:view'"
                  >
                    {{ $t('systemTools.showTableList') }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card class="database-card">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('systemTools.targetDb') }}</span>
                </div>
              </template>

              <el-form
                :model="localDbForm"
                ref="localFormRef"
                :rules="dbFormRules"
                label-width="120px"
              >
                <el-form-item :label="$t('systemTools.host')" prop="host">
                  <el-input v-model="localDbForm.host" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.port')" prop="port">
                  <el-input-number
                    v-model="localDbForm.port"
                    controls-position="right"
                    :min="1"
                    :max="65535"
                  />
                </el-form-item>
                <el-form-item :label="$t('systemTools.username')" prop="username">
                  <el-input v-model="localDbForm.username" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.password')">
                  <el-input
                    v-model="localDbForm.password"
                    type="password"
                    show-password
                    :placeholder="localPasswordMasked ? $t('systemTools.passwordMaskedHint') : ''"
                    @input="onPasswordInput('local')"
                  />
                </el-form-item>
                <el-form-item :label="$t('systemTools.database')" prop="database">
                  <el-input v-model="localDbForm.database" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.charset')">
                  <el-select
                    v-model="localDbForm.charset"
                    :placeholder="$t('systemTools.selectCharset')"
                  >
                    <el-option label="UTF-8" value="utf8mb4" />
                    <el-option label="UTF-8 (兼容)" value="utf8" />
                    <el-option label="GBK" value="gbk" />
                  </el-select>
                </el-form-item>
                <el-form-item>
                  <el-button
                    type="primary"
                    @click="testLocalConnection"
                    :loading="localTestLoading"
                  >
                    {{ $t('systemTools.testConnection') }}
                  </el-button>
                  <el-button @click="showLocalTables" :loading="localTablesLoading">
                    {{ $t('systemTools.showTableList') }}
                  </el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>
        </el-row>

        <!-- 远程数据库表列表对话框 -->
        <el-dialog
          v-model="remoteTablesDialogVisible"
          :title="$t('systemTools.sourceDb') + $t('systemTools.showTableList')"
          width="60%"
          top="5vh"
        >
          <el-table :data="remoteTables" style="width: 100%" height="400">
            <el-table-column prop="name" :label="$t('systemTools.tableName')" />
          </el-table>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="remoteTablesDialogVisible = false">{{
                $t('common.close')
              }}</el-button>
            </span>
          </template>
        </el-dialog>

        <!-- 本地数据库表列表对话框 -->
        <el-dialog
          v-model="localTablesDialogVisible"
          :title="$t('systemTools.targetDb') + $t('systemTools.showTableList')"
          width="60%"
          top="5vh"
        >
          <el-table :data="localTables" style="width: 100%" height="400">
            <el-table-column prop="name" :label="$t('systemTools.tableName')" />
          </el-table>
          <template #footer>
            <span class="dialog-footer">
              <el-button @click="localTablesDialogVisible = false">{{
                $t('common.close')
              }}</el-button>
            </span>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- 同步参数配置标签页 -->
      <el-tab-pane :label="$t('systemTools.syncConfig')" name="sync">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>{{ $t('systemTools.syncConfig') }}</span>
            </div>
          </template>

          <el-form :model="syncParams" label-width="150px">
            <el-form-item :label="$t('systemTools.defaultSyncMonth')">
              <el-date-picker
                v-model="syncParams.defaultMonth"
                type="month"
                :placeholder="$t('systemTools.selectDefaultSyncMonth')"
                value-format="YYYY-MM"
              />
            </el-form-item>
            <el-form-item :label="$t('systemTools.batchSize')">
              <el-slider v-model="syncParams.batchSize" :min="100" :max="5000" show-input />
            </el-form-item>
            <el-form-item :label="$t('systemTools.retryCount')">
              <el-slider v-model="syncParams.retryCount" :min="0" :max="10" show-input />
            </el-form-item>
            <el-form-item :label="$t('systemTools.timeoutSeconds')">
              <el-slider v-model="syncParams.timeoutSeconds" :min="10" :max="300" show-input />
            </el-form-item>
            <el-form-item :label="$t('systemTools.primaryKeys')">
              <el-input
                v-model="syncParams.primaryKeys"
                :placeholder="$t('systemTools.enterPrimaryKeys')"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" @click="saveConfig" :loading="saveLoading">
        {{ $t('systemTools.saveConfig') }}
      </el-button>
      <el-button @click="resetConfig" :disabled="saveLoading">
        {{ $t('systemTools.resetConfig') }}
      </el-button>
    </div>

    <!-- 配置状态 -->
    <el-alert
      v-if="configStatus.message"
      :title="configStatus.message"
      :type="configStatus.type"
      show-icon
      closable
      style="margin-top: 20px"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_PATH || ''
const PASSWORD_MASK = '***'

const { t } = useI18n()

const activeTab = ref('database')

const remoteFormRef = ref<FormInstance>()
const localFormRef = ref<FormInstance>()

const configStatus = reactive({
  message: '',
  type: 'success' as 'success' | 'warning' | 'info' | 'error'
})

const remoteTablesDialogVisible = ref(false)
const remoteTables = ref<{ name: string }[]>([])
const localTablesDialogVisible = ref(false)
const localTables = ref<{ name: string }[]>([])

const remoteDbForm = reactive({
  host: '',
  port: 3306,
  username: '',
  password: '',
  database: '',
  charset: 'utf8mb4'
})

const localDbForm = reactive({
  host: '',
  port: 3306,
  username: '',
  password: '',
  database: '',
  charset: 'utf8mb4'
})

const syncParams = reactive({
  defaultMonth: '',
  batchSize: 1000,
  retryCount: 3,
  timeoutSeconds: 30,
  primaryKeys: 'dataId'
})

const remotePasswordMasked = ref(false)
const localPasswordMasked = ref(false)

const remoteTestLoading = ref(false)
const localTestLoading = ref(false)
const remoteTablesLoading = ref(false)
const localTablesLoading = ref(false)
const saveLoading = ref(false)

const dbFormRules = reactive<FormRules>({
  host: [{ required: true, message: '请输入主机地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  database: [{ required: true, message: '请输入数据库名', trigger: 'blur' }]
})

const onPasswordInput = (type: 'remote' | 'local') => {
  if (type === 'remote') {
    remotePasswordMasked.value = false
  } else {
    localPasswordMasked.value = false
  }
}

let ws: WebSocket | null = null
const wsConnected = ref(false)
let wsReconnectAttempts = 0
const WS_MAX_RECONNECT = 10
const WS_BASE_DELAY = 3000
let wsIntentionalClose = false

const getWsReconnectDelay = () => {
  const delay = WS_BASE_DELAY * Math.pow(2, wsReconnectAttempts)
  return Math.min(delay, 60000)
}

const getConfig = async (configData?: Record<string, any>) => {
  try {
    let config: Record<string, any>
    if (configData) {
      config = configData
    } else {
      const response = await axios.get(`${API_BASE_URL}/api/config/`)
      config = response.data.data
    }

    if (config.REMOTE_DB) {
      remoteDbForm.host = config.REMOTE_DB.host ?? remoteDbForm.host
      const parsedPort = Number(config.REMOTE_DB.port)
      remoteDbForm.port = Number.isNaN(parsedPort) ? remoteDbForm.port : parsedPort
      remoteDbForm.username = config.REMOTE_DB.user ?? remoteDbForm.username
      remoteDbForm.database = config.REMOTE_DB.database ?? remoteDbForm.database
      remoteDbForm.charset = config.REMOTE_DB.charset ?? remoteDbForm.charset

      if (config.REMOTE_DB.password === PASSWORD_MASK) {
        remoteDbForm.password = ''
        remotePasswordMasked.value = true
      } else if (config.REMOTE_DB.password) {
        remoteDbForm.password = config.REMOTE_DB.password
        remotePasswordMasked.value = false
      }
    }

    if (config.LOCAL_DB) {
      localDbForm.host = config.LOCAL_DB.host ?? localDbForm.host
      const parsedPort = Number(config.LOCAL_DB.port)
      localDbForm.port = Number.isNaN(parsedPort) ? localDbForm.port : parsedPort
      localDbForm.username = config.LOCAL_DB.user ?? localDbForm.username
      localDbForm.database = config.LOCAL_DB.database ?? localDbForm.database
      localDbForm.charset = config.LOCAL_DB.charset ?? localDbForm.charset

      if (config.LOCAL_DB.password === PASSWORD_MASK) {
        localDbForm.password = ''
        localPasswordMasked.value = true
      } else if (config.LOCAL_DB.password) {
        localDbForm.password = config.LOCAL_DB.password
        localPasswordMasked.value = false
      }
    }

    if (config.SYNC) {
      const parsedBatch = Number(config.SYNC.batch_size)
      const parsedRetry = Number(config.SYNC.retry_count)
      const parsedTimeout = Number(config.SYNC.timeout)
      syncParams.batchSize = Number.isNaN(parsedBatch) ? syncParams.batchSize : parsedBatch
      syncParams.retryCount = Number.isNaN(parsedRetry) ? syncParams.retryCount : parsedRetry
      syncParams.timeoutSeconds = Number.isNaN(parsedTimeout)
        ? syncParams.timeoutSeconds
        : parsedTimeout
      syncParams.primaryKeys = config.SYNC.primary_keys ?? syncParams.primaryKeys
      syncParams.defaultMonth = config.SYNC.default_month ?? syncParams.defaultMonth
    }

    if (configData) {
      configStatus.message = t('systemTools.configUpdated')
      configStatus.type = 'info'
      ElMessage.info(t('systemTools.configUpdated'))
    } else {
      configStatus.message = t('systemTools.configLoadSuccess')
      configStatus.type = 'success'
    }
  } catch (error) {
    console.error(t('systemTools.getConfigFailed'), error)
    configStatus.message = t('systemTools.getConfigFailed')
    configStatus.type = 'error'
    ElMessage.error(t('systemTools.getConfigFailed'))
  }
}

const connectWebSocket = () => {
  if (wsIntentionalClose) return

  try {
    const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws'
    const wsUrl = `${wsProtocol}://${API_BASE_URL.replace(/^https?:\/\//, '')}/ws/sync-progress/`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      wsConnected.value = true
      wsReconnectAttempts = 0
      configStatus.message = t('systemTools.webSocketConnected')
      configStatus.type = 'info'
    }

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data)
        if (message.type === 'config_update' && message.config) {
          getConfig(message.config)
        }
      } catch (error) {
        console.error('WebSocket消息解析失败:', error)
      }
    }

    ws.onclose = () => {
      wsConnected.value = false
      configStatus.message = t('systemTools.webSocketDisconnected')
      configStatus.type = 'warning'

      if (!wsIntentionalClose && wsReconnectAttempts < WS_MAX_RECONNECT) {
        wsReconnectAttempts++
        const delay = getWsReconnectDelay()
        setTimeout(connectWebSocket, delay)
      }
    }

    ws.onerror = () => {
      wsConnected.value = false
    }
  } catch (error) {
    console.error('WebSocket连接失败:', error)
    wsConnected.value = false
    if (!wsIntentionalClose && wsReconnectAttempts < WS_MAX_RECONNECT) {
      wsReconnectAttempts++
      const delay = getWsReconnectDelay()
      setTimeout(connectWebSocket, delay)
    }
  }
}

const closeWebSocket = () => {
  wsIntentionalClose = true
  if (ws) {
    ws.close()
    ws = null
    wsConnected.value = false
  }
}

const buildTestRequest = (form: typeof remoteDbForm, passwordMasked: boolean) => ({
  host: form.host,
  port: form.port,
  user: form.username,
  password: form.password,
  database: form.database,
  charset: form.charset,
  use_stored_password: passwordMasked && !form.password
})

const testRemoteConnection = async () => {
  if (!remoteFormRef.value) return
  const valid = await remoteFormRef.value.validate().catch(() => false)
  if (!valid) return

  remoteTestLoading.value = true
  try {
    const requestData = buildTestRequest(remoteDbForm, remotePasswordMasked.value)
    const response = await axios.post(`${API_BASE_URL}/api/config/test-remote/`, requestData)
    ElMessage.success(response.data.message || t('systemTools.connectionSuccess'))
    configStatus.message = t('systemTools.connectionSuccess')
    configStatus.type = 'success'
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('systemTools.connectionFailed'))
    configStatus.message = error.response?.data?.message || t('systemTools.connectionFailed')
    configStatus.type = 'error'
  } finally {
    remoteTestLoading.value = false
  }
}

const showRemoteTables = async () => {
  remoteTablesLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/api/database/tables/remote/`)
    const tables = response.data.data?.tables
    if (tables) {
      remoteTables.value = tables.map((table: string) => ({ name: table }))
      remoteTablesDialogVisible.value = true
    } else {
      ElMessage.error(response.data.message || t('systemTools.getTableListFailed'))
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('systemTools.getTableListFailed'))
  } finally {
    remoteTablesLoading.value = false
  }
}

const testLocalConnection = async () => {
  if (!localFormRef.value) return
  const valid = await localFormRef.value.validate().catch(() => false)
  if (!valid) return

  localTestLoading.value = true
  try {
    const requestData = buildTestRequest(localDbForm, localPasswordMasked.value)
    const response = await axios.post(`${API_BASE_URL}/api/config/test-local/`, requestData)
    ElMessage.success(response.data.message || t('systemTools.connectionSuccess'))
    configStatus.message = t('systemTools.connectionSuccess')
    configStatus.type = 'success'
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('systemTools.connectionFailed'))
    configStatus.message = error.response?.data?.message || t('systemTools.connectionFailed')
    configStatus.type = 'error'
  } finally {
    localTestLoading.value = false
  }
}

const showLocalTables = async () => {
  localTablesLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/api/database/tables/local/`)
    const tables = response.data.data?.tables
    if (tables) {
      localTables.value = tables.map((table: string) => ({ name: table }))
      localTablesDialogVisible.value = true
    } else {
      ElMessage.error(response.data.message || t('systemTools.getTableListFailed'))
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || t('systemTools.getTableListFailed'))
  } finally {
    localTablesLoading.value = false
  }
}

const saveConfig = async () => {
  const remoteValid = await remoteFormRef.value?.validate().catch(() => false)
  const localValid = await localFormRef.value?.validate().catch(() => false)
  if (!remoteValid || !localValid) return

  saveLoading.value = true
  try {
    const configData = {
      REMOTE_DB: {
        host: remoteDbForm.host,
        port: remoteDbForm.port.toString(),
        user: remoteDbForm.username,
        password:
          remotePasswordMasked.value && !remoteDbForm.password
            ? PASSWORD_MASK
            : remoteDbForm.password,
        database: remoteDbForm.database,
        charset: remoteDbForm.charset
      },
      LOCAL_DB: {
        host: localDbForm.host,
        port: localDbForm.port.toString(),
        user: localDbForm.username,
        password:
          localPasswordMasked.value && !localDbForm.password ? PASSWORD_MASK : localDbForm.password,
        database: localDbForm.database,
        charset: localDbForm.charset
      },
      SYNC: {
        batch_size: syncParams.batchSize.toString(),
        retry_count: syncParams.retryCount.toString(),
        timeout: syncParams.timeoutSeconds.toString(),
        primary_keys: syncParams.primaryKeys,
        default_month: syncParams.defaultMonth
      }
    }

    const response = await axios.post(`${API_BASE_URL}/api/config/`, configData)
    ElMessage.success(response.data.message || t('systemTools.configSaved'))
    configStatus.message = response.data.message || t('systemTools.configSaved')
    configStatus.type = 'success'

    remotePasswordMasked.value = true
    localPasswordMasked.value = true
    remoteDbForm.password = ''
    localDbForm.password = ''
  } catch (error) {
    console.error(t('systemTools.configSaveFailed'), error)
    ElMessage.error(t('systemTools.configSaveFailed'))
    configStatus.message = t('systemTools.configSaveFailed')
    configStatus.type = 'error'
  } finally {
    saveLoading.value = false
  }
}

const resetConfig = () => {
  ElMessageBox.confirm(t('systemTools.resetConfigConfirm'), t('systemTools.warning'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  })
    .then(() => {
      remoteDbForm.host = ''
      remoteDbForm.port = 3306
      remoteDbForm.username = ''
      remoteDbForm.password = ''
      remoteDbForm.database = ''
      remoteDbForm.charset = 'utf8mb4'
      remotePasswordMasked.value = false

      localDbForm.host = ''
      localDbForm.port = 3306
      localDbForm.username = ''
      localDbForm.password = ''
      localDbForm.database = ''
      localDbForm.charset = 'utf8mb4'
      localPasswordMasked.value = false

      syncParams.defaultMonth = ''
      syncParams.batchSize = 1000
      syncParams.retryCount = 3
      syncParams.timeoutSeconds = 30
      syncParams.primaryKeys = 'dataId'

      ElMessage.info(t('systemTools.configReset'))
      configStatus.message = t('systemTools.configReset')
      configStatus.type = 'info'
    })
    .catch(() => {})
}

onMounted(() => {
  getConfig()
  connectWebSocket()
})

onBeforeUnmount(() => {
  closeWebSocket()
})
</script>

<style scoped>
.sync-config {
  padding: 20px;
}

.database-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  margin-top: 20px;
  text-align: center;
}

.action-buttons .el-button {
  margin: 0 10px;
}

.dialog-footer {
  text-align: right;
}
</style>
