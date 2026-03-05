<template>
  <div class="sync-config">
    <el-tabs v-model="activeTab" type="card">
      <!-- 数据库配置标签页 -->
      <el-tab-pane :label="$t('systemTools.dbConfig')" name="database">
        <el-row :gutter="20">
          <el-col :span="12">
            <!-- 远程数据库配置表单 -->
            <el-card class="database-card">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('systemTools.sourceDb') }}</span>
                </div>
              </template>

              <el-form label-width="120px" :model="remoteDbForm" ref="remoteFormRef">
                <el-form-item :label="$t('systemTools.host')">
                  <el-input v-model="remoteDbForm.host" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.port')">
                  <el-input-number v-model="remoteDbForm.port" controls-position="right" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.username')">
                  <el-input v-model="remoteDbForm.username" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.password')">
                  <el-input v-model="remoteDbForm.password" type="password" show-password />
                </el-form-item>
                <el-form-item :label="$t('systemTools.database')">
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
                  <el-button type="primary" @click="testRemoteConnection">{{
                    $t('systemTools.testConnection')
                  }}</el-button>
                  <el-button @click="showRemoteTables">{{
                    $t('systemTools.showTableList')
                  }}</el-button>
                </el-form-item>
              </el-form>
            </el-card>
          </el-col>

          <el-col :span="12">
            <!-- 本地数据库配置表单 -->
            <el-card class="database-card">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('systemTools.targetDb') }}</span>
                </div>
              </template>

              <el-form :model="localDbForm" ref="localFormRef">
                <el-form-item :label="$t('systemTools.host')">
                  <el-input v-model="localDbForm.host" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.port')">
                  <el-input-number v-model="localDbForm.port" controls-position="right" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.username')">
                  <el-input v-model="localDbForm.username" />
                </el-form-item>
                <el-form-item :label="$t('systemTools.password')">
                  <el-input v-model="localDbForm.password" type="password" show-password />
                </el-form-item>
                <el-form-item :label="$t('systemTools.database')">
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
                  <el-button type="primary" @click="testLocalConnection">{{
                    $t('systemTools.testConnection')
                  }}</el-button>
                  <el-button @click="showLocalTables">{{
                    $t('systemTools.showTableList')
                  }}</el-button>
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
      <el-button type="primary" @click="saveConfig">{{ $t('systemTools.saveConfig') }}</el-button>
      <el-button @click="resetConfig">{{ $t('systemTools.resetConfig') }}</el-button>
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

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useI18n } from 'vue-i18n' // 引入国际化插件
import {
  ElMessage,
  ElMessageBox,
  ElInput,
  ElButton,
  ElForm,
  ElFormItem,
  ElDatePicker,
  ElInputNumber,
  ElSelect,
  ElOption,
  ElTabs,
  ElTabPane,
  ElCard,
  ElRow,
  ElCol,
  ElDialog,
  ElTable,
  ElTableColumn,
  ElSlider,
  ElAlert
} from 'element-plus'
import axios from 'axios'

// 使用环境变量设置API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_PATH || 'http://localhost:8000'

export default defineComponent({
  name: 'SyncConfig',
  components: {
    ElInput,
    ElButton,
    ElForm,
    ElFormItem,
    ElDatePicker,
    ElInputNumber,
    ElSelect,
    ElOption,
    ElTabs,
    ElTabPane,
    ElCard,
    ElRow,
    ElCol,
    ElDialog,
    ElTable,
    ElTableColumn,
    ElSlider,
    ElAlert
  },
  setup() {
    const { t } = useI18n() // 使用国际化功能

    // 当前激活的标签页
    const activeTab = ref('database')

    // 表单引用
    const remoteFormRef = ref<any>(null)
    const localFormRef = ref<any>(null)

    // 配置状态
    const configStatus = reactive({
      message: '',
      type: 'success' as 'success' | 'warning' | 'info' | 'error'
    })

    // 远程数据库表列表对话框可见性
    const remoteTablesDialogVisible = ref(false)
    const remoteTables = ref<{ name: string }[]>([])

    // 本地数据库表列表对话框可见性
    const localTablesDialogVisible = ref(false)
    const localTables = ref<{ name: string }[]>([])

    // 远程数据库表单数据
    const remoteDbForm = reactive({
      host: '192.168.1.100',
      port: 3306,
      username: 'read_only',
      password: '',
      database: 'branchdb',
      charset: 'utf8mb4'
    })

    // 本地数据库表单数据
    const localDbForm = reactive({
      host: '127.0.0.1',
      port: 3306,
      username: 'root',
      password: '',
      database: 'branchdb',
      charset: 'utf8mb3'
    })

    // 同步参数
    const syncParams = reactive({
      defaultMonth: '',
      batchSize: 1000,
      retryCount: 3,
      timeoutSeconds: 30,
      primaryKeys: 'dataId'
    })

    // WebSocket连接
    let ws: WebSocket | null = null
    const wsConnected = ref(false)

    // 获取配置
    const getConfig = async (configData?: any) => {
      try {
        let config
        if (configData) {
          // 使用WebSocket推送的配置数据
          config = configData
        } else {
          // 从API获取配置
          const response = await axios.get(`${API_BASE_URL}/api/config/`)
          config = response.data
        }

        // 更新远程数据库配置
        if (config.REMOTE_DB) {
          remoteDbForm.host = config.REMOTE_DB.host || remoteDbForm.host
          remoteDbForm.port = parseInt(config.REMOTE_DB.port) || remoteDbForm.port
          remoteDbForm.username = config.REMOTE_DB.user || remoteDbForm.username
          remoteDbForm.password = config.REMOTE_DB.password || remoteDbForm.password
          remoteDbForm.database = config.REMOTE_DB.database || remoteDbForm.database
          remoteDbForm.charset = config.REMOTE_DB.charset || remoteDbForm.charset
        }

        // 更新本地数据库配置
        if (config.LOCAL_DB) {
          localDbForm.host = config.LOCAL_DB.host || localDbForm.host
          localDbForm.port = parseInt(config.LOCAL_DB.port) || localDbForm.port
          localDbForm.username = config.LOCAL_DB.user || localDbForm.username
          localDbForm.password = config.LOCAL_DB.password || localDbForm.password
          localDbForm.database = config.LOCAL_DB.database || localDbForm.database
          localDbForm.charset = config.LOCAL_DB.charset || localDbForm.charset
        }

        // 更新同步参数
        if (config.SYNC) {
          syncParams.batchSize = parseInt(config.SYNC.batch_size) || syncParams.batchSize
          syncParams.retryCount = parseInt(config.SYNC.retry_count) || syncParams.retryCount
          syncParams.timeoutSeconds = parseInt(config.SYNC.timeout) || syncParams.timeoutSeconds
          syncParams.primaryKeys = config.SYNC.primary_keys || syncParams.primaryKeys
        }

        if (configData) {
          // WebSocket推送的配置更新
          configStatus.message = t('systemTools.configUpdated')
          configStatus.type = 'info'
          ElMessage.info(t('systemTools.configUpdated'))
        } else {
          // 初始加载配置
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

    // 连接WebSocket
    const connectWebSocket = () => {
      try {
        // 构建WebSocket URL
        const wsProtocol = API_BASE_URL.startsWith('https') ? 'wss' : 'ws'
        const wsUrl = `${wsProtocol}://${API_BASE_URL.replace(/^https?:\/\//, '')}/ws/sync-progress/`

        ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('WebSocket连接已打开')
          wsConnected.value = true
          configStatus.message = t('systemTools.webSocketConnected')
          configStatus.type = 'info'
        }

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            if (message.type === 'config_update') {
              // 处理配置更新
              getConfig(message.config)
            }
          } catch (error) {
            console.error('WebSocket消息解析失败:', error)
          }
        }

        ws.onclose = () => {
          console.log('WebSocket连接已关闭')
          wsConnected.value = false
          configStatus.message = t('systemTools.webSocketDisconnected')
          configStatus.type = 'warning'
          // 尝试重新连接
          setTimeout(connectWebSocket, 3000)
        }

        ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          wsConnected.value = false
        }
      } catch (error) {
        console.error('WebSocket连接失败:', error)
        wsConnected.value = false
        // 尝试重新连接
        setTimeout(connectWebSocket, 3000)
      }
    }

    // 关闭WebSocket
    const closeWebSocket = () => {
      if (ws) {
        ws.close()
        ws = null
        wsConnected.value = false
      }
    }

    // 测试远程连接
    const testRemoteConnection = async () => {
      try {
        const requestData = {
          host: remoteDbForm.host,
          port: remoteDbForm.port,
          user: remoteDbForm.username,
          password: remoteDbForm.password,
          database: remoteDbForm.database,
          charset: remoteDbForm.charset
        }

        const response = await axios.post(`${API_BASE_URL}/api/config/test-remote/`, requestData)
        ElMessage.success(response.data.message || t('systemTools.connectionSuccess'))
        configStatus.message = t('systemTools.connectionSuccess')
        configStatus.type = 'success'
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('systemTools.connectionFailed'))
        configStatus.message = error.response?.data?.message || t('systemTools.connectionFailed')
        configStatus.type = 'error'
      }
    }

    // 显示远程数据库表列表
    const showRemoteTables = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/database/tables/remote/`)
        if (response.data.tables) {
          remoteTables.value = response.data.tables.map((table: string) => ({ name: table }))
          remoteTablesDialogVisible.value = true
        } else {
          ElMessage.error(response.data.message || t('systemTools.getTableListFailed'))
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('systemTools.getTableListFailed'))
      }
    }

    // 测试本地连接
    const testLocalConnection = async () => {
      try {
        const requestData = {
          host: localDbForm.host,
          port: localDbForm.port,
          user: localDbForm.username,
          password: localDbForm.password,
          database: localDbForm.database,
          charset: localDbForm.charset
        }

        const response = await axios.post(`${API_BASE_URL}/api/config/test-local/`, requestData)
        ElMessage.success(response.data.message || t('systemTools.connectionSuccess'))
        configStatus.message = t('systemTools.connectionSuccess')
        configStatus.type = 'success'
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('systemTools.connectionFailed'))
        configStatus.message = error.response?.data?.message || t('systemTools.connectionFailed')
        configStatus.type = 'error'
      }
    }

    // 显示本地数据库表列表
    const showLocalTables = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/database/tables/local/`)
        if (response.data.tables) {
          localTables.value = response.data.tables.map((table: string) => ({ name: table }))
          localTablesDialogVisible.value = true
        } else {
          ElMessage.error(response.data.message || t('systemTools.getTableListFailed'))
        }
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || t('systemTools.getTableListFailed'))
      }
    }

    // 保存配置
    const saveConfig = async () => {
      try {
        const configData = {
          REMOTE_DB: {
            host: remoteDbForm.host,
            port: remoteDbForm.port.toString(),
            user: remoteDbForm.username,
            password: remoteDbForm.password,
            database: remoteDbForm.database,
            charset: remoteDbForm.charset
          },
          LOCAL_DB: {
            host: localDbForm.host,
            port: localDbForm.port.toString(),
            user: localDbForm.username,
            password: localDbForm.password,
            database: localDbForm.database,
            charset: localDbForm.charset
          },
          SYNC: {
            batch_size: syncParams.batchSize.toString(),
            retry_count: syncParams.retryCount.toString(),
            timeout: syncParams.timeoutSeconds.toString(),
            primary_keys: syncParams.primaryKeys
          }
        }

        const response = await axios.post(`${API_BASE_URL}/api/config/`, configData)
        ElMessage.success(response.data.message || t('systemTools.configSaved'))
        configStatus.message = response.data.message || t('systemTools.configSaved')
        configStatus.type = 'success'
      } catch (error) {
        console.error(t('systemTools.configSaveFailed'), error)
        ElMessage.error(t('systemTools.configSaveFailed'))
        configStatus.message = t('systemTools.configSaveFailed')
        configStatus.type = 'error'
      }
    }

    // 重置配置
    const resetConfig = () => {
      ElMessageBox.confirm(t('systemTools.resetConfigConfirm'), t('systemTools.warning'), {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      })
        .then(() => {
          // 重置为默认值
          remoteDbForm.host = '192.168.1.100'
          remoteDbForm.port = 3306
          remoteDbForm.username = 'read_only'
          remoteDbForm.password = ''
          remoteDbForm.database = 'branchdb'
          remoteDbForm.charset = 'utf8mb4'

          localDbForm.host = '127.0.0.1'
          localDbForm.port = 3306
          localDbForm.username = 'root'
          localDbForm.password = ''
          localDbForm.database = 'branchdb'
          localDbForm.charset = 'utf8mb3'

          syncParams.defaultMonth = ''
          syncParams.batchSize = 1000
          syncParams.retryCount = 3
          syncParams.timeoutSeconds = 30
          syncParams.primaryKeys = 'dataId'

          ElMessage.info(t('systemTools.configReset'))
          configStatus.message = t('systemTools.configReset')
          configStatus.type = 'info'
        })
        .catch(() => {
          // 用户取消操作
        })
    }

    // 页面加载时获取配置并连接WebSocket
    onMounted(() => {
      getConfig()
      connectWebSocket()
    })

    // 组件卸载前关闭WebSocket
    onBeforeUnmount(() => {
      closeWebSocket()
    })

    return {
      activeTab,
      remoteFormRef,
      localFormRef,
      configStatus,
      remoteDbForm,
      localDbForm,
      syncParams,
      testRemoteConnection,
      testLocalConnection,
      saveConfig,
      resetConfig,
      // 表相关属性
      remoteTablesDialogVisible,
      remoteTables,
      showRemoteTables,
      localTablesDialogVisible,
      localTables,
      showLocalTables,
      // WebSocket相关
      wsConnected
    }
  }
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
