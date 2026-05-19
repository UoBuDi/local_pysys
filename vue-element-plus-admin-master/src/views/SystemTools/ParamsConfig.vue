<template>
  <div class="params-config">
    <el-card class="config-card">
      <template #header>
        <div class="card-header">
          <span class="title">{{ $t('systemTools.dbConfig') }}</span>
        </div>
      </template>

      <div class="config-sections">
        <!-- 路径匹配配置 -->
        <div class="config-section">
          <div class="section-title">
            <el-icon class="section-icon"><Connection /></el-icon>
            <span>{{ $t('router.pathMatch') }}</span>
          </div>
          <el-form label-width="140px" :model="pathMatchForm" class="config-form">
            <el-form-item :label="$t('systemTools.pathMatchTable')">
              <el-select
                v-model="pathMatchForm.tableName"
                :placeholder="$t('systemTools.selectPathMatchTable')"
                style="width: 300px"
                clearable
                filterable
              >
                <el-option
                  v-for="table in availableTables"
                  :key="table"
                  :label="table"
                  :value="table"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>

        <el-divider class="section-divider" />

        <!-- 详单查询配置 -->
        <div class="config-section">
          <div class="section-title">
            <el-icon class="section-icon"><Document /></el-icon>
            <span>{{ $t('router.detailQuery') }}</span>
          </div>
          <el-form label-width="140px" :model="detailQueryForm" class="config-form">
            <el-form-item :label="$t('systemTools.detailQueryTable')">
              <el-select
                v-model="detailQueryForm.tableName"
                :placeholder="$t('systemTools.selectDetailQueryTable')"
                style="width: 300px"
                clearable
                filterable
              >
                <el-option
                  v-for="table in availableTables"
                  :key="table"
                  :label="table"
                  :value="table"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </el-card>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button type="primary" size="large" @click="saveConfig">
        <el-icon class="btn-icon"><Check /></el-icon>
        {{ $t('systemTools.saveConfig') }}
      </el-button>
      <el-button size="large" @click="resetConfig">
        <el-icon class="btn-icon"><RefreshLeft /></el-icon>
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
      class="status-alert"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Connection, Document, Check, RefreshLeft } from '@element-plus/icons-vue'
import axios from 'axios'

const { t } = useI18n()

const API_BASE_URL = import.meta.env.VITE_API_BASE_PATH || 'http://localhost:8000'

const configStatus = reactive({
  message: '',
  type: 'success' as 'success' | 'warning' | 'info' | 'error'
})

const availableTables = ref<string[]>([])

const pathMatchForm = reactive({
  tableName: ''
})

const detailQueryForm = reactive({
  tableName: ''
})

const loadAvailableTables = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/path-match/tables/`)
    if (response.data.code === 200 && response.data.data) {
      availableTables.value = response.data.data
    }
  } catch (error: any) {
    console.error(t('systemTools.getPathMatchTablesFailed'), error)
    ElMessage.error(t('systemTools.getPathMatchTablesFailed'))
  }
}

const getConfig = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/params-config/`)
    const config = response.data

    if (config.PATH_MATCH) {
      pathMatchForm.tableName = config.PATH_MATCH.table_name || ''
    }

    if (config.DETAIL_QUERY) {
      detailQueryForm.tableName = config.DETAIL_QUERY.table_name || ''
    }

    configStatus.message = t('systemTools.configLoadSuccess')
    configStatus.type = 'success'
  } catch (error) {
    console.error(t('systemTools.getConfigFailed'), error)
    configStatus.message = t('systemTools.getConfigFailed')
    configStatus.type = 'error'
    ElMessage.error(t('systemTools.getConfigFailed'))
  }
}

const saveConfig = async () => {
  try {
    const configData = {
      PATH_MATCH: {
        table_name: pathMatchForm.tableName
      },
      DETAIL_QUERY: {
        table_name: detailQueryForm.tableName
      }
    }

    const response = await axios.post(`${API_BASE_URL}/api/params-config/`, configData)
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

const resetConfig = () => {
  ElMessageBox.confirm(t('systemTools.resetConfigConfirm'), t('systemTools.warning'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  })
    .then(() => {
      pathMatchForm.tableName = ''
      detailQueryForm.tableName = ''
      ElMessage.info(t('systemTools.configReset'))
      configStatus.message = t('systemTools.configReset')
      configStatus.type = 'info'
    })
    .catch(() => {})
}

onMounted(() => {
  loadAvailableTables()
  getConfig()
})
</script>

<style scoped>
.params-config {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

.config-card {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #e4e7ed;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.config-sections {
  padding: 8px 0;
}

.config-section {
  padding: 20px 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 15px;
  font-weight: 500;
  color: #303133;
}

.section-icon {
  font-size: 18px;
  color: #409eff;
}

.config-form {
  padding-left: 26px;
}

.section-divider {
  margin: 0;
  border-color: #f0f0f0;
}

.action-buttons {
  margin-top: 24px;
  text-align: center;
  display: flex;
  gap: 16px;
  justify-content: center;
}

.action-buttons .el-button {
  min-width: 140px;
  height: 44px;
}

.btn-icon {
  margin-right: 6px;
}

.status-alert {
  margin-top: 20px;
  border-radius: 8px;
}
</style>
