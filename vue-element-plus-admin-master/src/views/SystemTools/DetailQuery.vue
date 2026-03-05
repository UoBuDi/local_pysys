<template>
  <div class="detail-query">
    <el-card class="search-panel">
      <template #header>
        <div class="card-header">
          <span>详单查询</span>
        </div>
      </template>

      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="通行标识ID">
          <el-autocomplete
            v-model="searchForm.pass_id"
            :fetch-suggestions="queryPassIdSuggestions"
            placeholder="请输入通行标识ID"
            clearable
            style="width: 180px"
            @select="handlePassIdSelect"
          />
        </el-form-item>
        <el-form-item label="收费入口名称">
          <el-input
            v-model="searchForm.entry_name"
            placeholder="请输入收费入口名称"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="收费出口名称">
          <el-input
            v-model="searchForm.exit_name"
            placeholder="请输入收费出口名称"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="计费交易起止时间">
          <el-date-picker
            v-model="searchForm.time_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            format="YYYY-MM-DD HH:mm:ss"
            :default-time="defaultTime"
            clearable
            style="width: 380px"
          />
        </el-form-item>
        <el-form-item label="车牌号码">
          <el-autocomplete
            v-model="searchForm.plate_number"
            :fetch-suggestions="queryPlateNumberSuggestions"
            placeholder="请输入车牌号码"
            clearable
            style="width: 180px"
            @select="handlePlateNumberSelect"
          />
        </el-form-item>
        <el-form-item label="收费车型">
          <el-select
            v-model="searchForm.vehicle_type"
            placeholder="请选择收费车型"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="item in detailQueryOptions.vehicletype.options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="计费方式">
          <el-select
            v-model="searchForm.billing_method"
            placeholder="请选择计费方式"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="item in detailQueryOptions.exitfeetype.options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="通行介质">
          <el-select
            v-model="searchForm.medium"
            placeholder="请选择通行介质"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="item in detailQueryOptions.mediatype.options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="清分日">
          <el-date-picker
            v-model="searchForm.settlement_date"
            type="date"
            placeholder="选择清分日"
            value-format="YYYY-MM-DD"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select
            v-model="searchForm.data_type"
            placeholder="请选择数据类型"
            clearable
            style="width: 180px"
          >
            <el-option
              v-for="item in detailQueryOptions.splittype.options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="拆分月份">
          <el-date-picker
            v-model="searchForm.split_month"
            type="month"
            placeholder="选择拆分月份"
            value-format="YYYY-MM"
            clearable
            style="width: 180px"
          />
        </el-form-item>
      </el-form>
      <div class="search-buttons">
        <el-button type="primary" @click="handleSearch" :loading="loading"> 查询 </el-button>
        <el-button @click="handleReset"> 重置 </el-button>
        <el-button
          v-if="canShowExport"
          type="success"
          @click="handleExportCurrentPage"
          :disabled="tableData.length === 0"
          :loading="exportingCurrent"
        >
          导出数据
        </el-button>
      </div>
    </el-card>

    <el-card class="table-panel">
      <el-table
        v-loading="loading"
        :data="tableData"
        border
        stripe
        style="width: 100%"
        height="600"
        @row-click="handleRowClick"
        :row-class-name="tableRowClassName"
      >
        <el-table-column
          v-for="column in tableColumns"
          :key="column.prop"
          :prop="column.prop"
          :label="column.label"
          :min-width="column.minWidth || 150"
          :show-overflow-tooltip="true"
        />
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :page-sizes="[50, 100, 200, 500, 1000]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <el-card class="debug-panel" v-if="canShowDebug && debugInfo">
      <template #header>
        <div class="card-header">
          <span>调试信息</span>
          <el-button type="primary" link size="small" @click="showDebug = !showDebug">
            {{ showDebug ? '收起' : '展开' }}
          </el-button>
        </div>
      </template>

      <div v-show="showDebug" class="debug-content">
        <div class="debug-statistics">
          <el-tag type="info">总耗时: {{ debugInfo.total_time.toFixed(3) }}s</el-tag>
          <el-tag type="warning" style="margin-left: 10px"
            >COUNT 查询耗时: {{ debugInfo.count_duration.toFixed(3) }}s</el-tag
          >
        </div>

        <div class="debug-section">
          <h4>COUNT 查询 SQL</h4>
          <el-input :model-value="debugInfo.count_sql" type="textarea" :rows="3" readonly />
          <el-button type="primary" link size="small" @click="copySql(debugInfo.count_sql)">
            复制
          </el-button>
        </div>

        <div class="debug-section">
          <h4>SELECT 查询 SQL</h4>
          <el-input :model-value="debugInfo.select_sql" type="textarea" :rows="3" readonly />
          <el-button type="primary" link size="small" @click="copySql(debugInfo.select_sql)">
            复制
          </el-button>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="detailDialogVisible"
      title="详细信息"
      width="90%"
      :close-on-click-modal="false"
      class="detail-dialog"
    >
      <div class="detail-dialog-content">
        <el-descriptions :column="2" border v-if="currentRow">
          <el-descriptions-item
            v-for="[key, value] in normalFieldEntries"
            :key="key"
            :label="key"
            :label-class-name="
              key === '出口交易编号' || key === '通行标识ID' ? 'no-wrap-label' : ''
            "
          >
            <span class="detail-value">{{ value }}</span>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider v-if="hasCombinationFields" content-position="left">组合字段详情</el-divider>

        <el-table
          v-if="hasCombinationFields && combinationTableData.length > 0"
          :data="combinationTableData"
          border
          stripe
          style="width: 100%; margin-top: 20px"
          :scroll="{ x: 'max-content', y: 400 }"
          :show-summary="true"
          :summary-method="getSummary"
        >
          <el-table-column
            v-for="field in COMBINATION_FIELDS"
            :key="field"
            :prop="field"
            :label="field"
            :min-width="180"
            :show-overflow-tooltip="true"
          />
        </el-table>
      </div>

      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="copyRowData">复制全部</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { queryDetailData } from '@/api/detail-query'
import type {
  DetailQueryParams,
  DetailQueryData,
  DetailQueryDataItem,
  DetailQueryDebugInfo
} from '@/api/detail-query'
import { useUserStore } from '@/store/modules/user'
import detailQueryOptions from '@/assets/data/detail-query-options.json'
import * as XLSX from 'xlsx'

const userStore = useUserStore()

const hasPermission = (): boolean => {
  const userInfo = userStore.getUserInfo
  const roleList = userInfo?.roleList || []

  if (roleList.includes('超级管理员') || roleList.includes('管理员')) {
    return true
  }

  return false
}

const canShowDebug = computed(() => hasPermission())
const canShowExport = computed(() => hasPermission())

const loading = ref(false)
const exportingCurrent = ref(false)
const tableData = ref<DetailQueryDataItem[]>([])
const tableColumns = ref<Array<{ prop: string; label: string; minWidth?: number }>>([])
const debugInfo = ref<DetailQueryDebugInfo | null>(null)
const showDebug = ref(true)
const detailDialogVisible = ref(false)
const currentRow = ref<DetailQueryDataItem | null>(null)

const COMBINATION_FIELDS = [
  '拆分收费路段编号组合',
  '拆分收费路段名称组合',
  '拆分收费单元编码组合',
  '拆分收费单元名称组合',
  '拆分收费金额组合',
  '拆分收费时间组合'
]

const hasCombinationFields = computed(() => {
  if (!currentRow.value) return false
  return COMBINATION_FIELDS.some((field) => currentRow.value?.[field])
})

const normalFieldEntries = computed(() => {
  if (!currentRow.value) return []
  return Object.entries(currentRow.value).filter(([key]) => !COMBINATION_FIELDS.includes(key))
})

const combinationTableData = computed(() => {
  if (!currentRow.value) return []

  const splitValues: Record<string, string[]> = {}
  let maxLength = 0

  COMBINATION_FIELDS.forEach((field) => {
    const value = currentRow.value?.[field]
    if (value) {
      const values = String(value)
        .split('|')
        .filter((v) => v.trim())
      splitValues[field] = values
      maxLength = Math.max(maxLength, values.length)
    }
  })

  const result: Array<Record<string, string>> = []
  for (let i = 0; i < maxLength; i++) {
    const row: Record<string, string> = {}
    COMBINATION_FIELDS.forEach((field) => {
      row[field] = splitValues[field]?.[i] || ''
    })
    result.push(row)
  }

  return result
})

const formatSecondsToTime = (totalSeconds: number): string => {
  if (totalSeconds <= 0) return '00:00:00'
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
}

const totalAmount = computed(() => {
  if (!currentRow.value) return 0
  const amountField = '拆分收费金额组合'
  const value = currentRow.value?.[amountField]
  if (!value) return 0
  const amounts = String(value)
    .split('|')
    .filter((v) => v.trim())
    .map((v) => {
      const num = parseFloat(v)
      return isNaN(num) ? 0 : num
    })
  return amounts.reduce((sum, val) => sum + val, 0)
})

const totalTime = computed(() => {
  if (!currentRow.value) return 0
  const startTime = currentRow.value['计费交易起点时间']
  const endTime = currentRow.value['计费交易终点时间']
  if (!startTime || !endTime) return 0

  try {
    const start = new Date(String(startTime))
    const end = new Date(String(endTime))
    if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0
    const diff = end.getTime() - start.getTime()
    if (diff <= 0) return 0
    return Math.floor(diff / 1000)
  } catch (error) {
    return 0
  }
})

const getSummary = ({ columns }: { columns: any[] }) => {
  return columns.map((column, index) => {
    if (index === 0) {
      return '合计'
    }
    if (column.property === '拆分收费金额组合') {
      return `${(totalAmount.value / 100).toFixed(2)} 元`
    }
    if (column.property === '拆分收费时间组合') {
      return formatSecondsToTime(totalTime.value)
    }
    return ''
  })
}

const STORAGE_KEY_PASS_ID = 'detail_query_pass_id_history'
const STORAGE_KEY_PLATE_NUMBER = 'detail_query_plate_number_history'
const MAX_HISTORY = 10

const defaultTime: [Date, Date] = [new Date(2000, 1, 1, 0, 0, 0), new Date(2000, 1, 1, 23, 59, 59)]

const passIdHistory = ref<string[]>([])
const plateNumberHistory = ref<string[]>([])

const loadHistory = () => {
  try {
    const passIdData = localStorage.getItem(STORAGE_KEY_PASS_ID)
    const plateNumberData = localStorage.getItem(STORAGE_KEY_PLATE_NUMBER)

    if (passIdData) {
      passIdHistory.value = JSON.parse(passIdData)
    }
    if (plateNumberData) {
      plateNumberHistory.value = JSON.parse(plateNumberData)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
  }
}

const saveToHistory = (value: string, history: string[], storageKey: string) => {
  if (!value || !value.trim()) return

  const trimmedValue = value.trim()

  const index = history.indexOf(trimmedValue)
  if (index > -1) {
    history.splice(index, 1)
  }

  history.unshift(trimmedValue)

  if (history.length > MAX_HISTORY) {
    history.pop()
  }

  try {
    localStorage.setItem(storageKey, JSON.stringify(history))
  } catch (error) {
    console.error('保存历史记录失败:', error)
  }
}

const queryPassIdSuggestions = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? passIdHistory.value.filter((item) => item.toLowerCase().includes(queryString.toLowerCase()))
    : passIdHistory.value

  cb(results.map((item) => ({ value: item })))
}

const queryPlateNumberSuggestions = (queryString: string, cb: (arg: any) => void) => {
  const results = queryString
    ? plateNumberHistory.value.filter((item) =>
        item.toLowerCase().includes(queryString.toLowerCase())
      )
    : plateNumberHistory.value

  cb(results.map((item) => ({ value: item })))
}

const handlePassIdSelect = (item: { value: string }) => {
  searchForm.pass_id = item.value
}

const handlePlateNumberSelect = (item: { value: string }) => {
  searchForm.plate_number = item.value
}

const searchForm = reactive<{
  pass_id: string
  entry_name: string
  exit_name: string
  time_range?: [string, string]
  plate_number: string
  vehicle_type: string
  billing_method: string
  medium: string
  settlement_date: string
  data_type: string
  split_month: string
  page: number
  page_size: number
}>({
  pass_id: '',
  entry_name: '',
  exit_name: '',
  plate_number: '',
  vehicle_type: '',
  billing_method: '',
  medium: '',
  settlement_date: '',
  data_type: '',
  split_month: '',
  page: 1,
  page_size: 20
})

const pagination = reactive({
  page: 1,
  page_size: 50,
  total: 0
})

const copySql = (sql: string) => {
  navigator.clipboard
    .writeText(sql)
    .then(() => {
      ElMessage.success('SQL 已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

const tableRowClassName = () => {
  return 'clickable-row'
}

const handleRowClick = (row: DetailQueryDataItem) => {
  currentRow.value = row
  detailDialogVisible.value = true
}

const copyRowData = () => {
  if (!currentRow.value) return

  let text = ''

  const normalFields = Object.entries(currentRow.value).filter(
    ([key]) => !COMBINATION_FIELDS.includes(key)
  )
  if (normalFields.length > 0) {
    text += '基本信息:\n'
    text += normalFields.map(([key, value]) => `${key}: ${value}`).join('\n')
  }

  if (hasCombinationFields.value && combinationTableData.value.length > 0) {
    if (text) text += '\n\n'
    text += '组合字段详情:\n'
    text += COMBINATION_FIELDS.join('\t') + '\n'
    combinationTableData.value.forEach((row) => {
      text += COMBINATION_FIELDS.map((field) => row[field]).join('\t') + '\n'
    })
  }

  navigator.clipboard
    .writeText(text)
    .then(() => {
      ElMessage.success('数据已复制到剪贴板')
    })
    .catch(() => {
      ElMessage.error('复制失败')
    })
}

const handleExportCurrentPage = () => {
  if (tableData.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  exportingCurrent.value = true

  try {
    const ws = XLSX.utils.json_to_sheet(tableData.value)
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, '详单数据')

    const now = new Date()
    const fileName = `详单数据_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}${String(now.getSeconds()).padStart(2, '0')}.xlsx`

    XLSX.writeFile(wb, fileName)
    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  } finally {
    exportingCurrent.value = false
  }
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params: DetailQueryParams = {
      pass_id: searchForm.pass_id,
      entry_name: searchForm.entry_name,
      exit_name: searchForm.exit_name,
      start_time: searchForm.time_range?.[0] ?? '',
      end_time: searchForm.time_range?.[1] ?? '',
      plate_number: searchForm.plate_number,
      vehicle_type: searchForm.vehicle_type,
      billing_method: searchForm.billing_method,
      medium: searchForm.medium,
      settlement_date: searchForm.settlement_date,
      data_type: searchForm.data_type,
      split_month: searchForm.split_month,
      page: pagination.page,
      page_size: pagination.page_size
    }
    const res: any = await queryDetailData(params)
    if (res.code === 200) {
      const data = res.data as DetailQueryData
      tableData.value = data.list
      pagination.total = data.total

      if (res.debug) {
        debugInfo.value = res.debug
      }

      saveToHistory(searchForm.pass_id, passIdHistory.value, STORAGE_KEY_PASS_ID)
      saveToHistory(searchForm.plate_number, plateNumberHistory.value, STORAGE_KEY_PLATE_NUMBER)

      if (tableData.value.length > 0 && tableColumns.value.length === 0) {
        const firstRow = tableData.value[0]
        tableColumns.value = Object.keys(firstRow).map((key) => ({
          prop: key,
          label: key,
          minWidth: 150
        }))
      }

      ElMessage.success('查询成功')
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  Object.assign(searchForm, {
    pass_id: '',
    entry_name: '',
    exit_name: '',
    plate_number: '',
    vehicle_type: '',
    billing_method: '',
    medium: '',
    settlement_date: '',
    data_type: '',
    split_month: ''
  })
  searchForm.time_range = undefined
  pagination.page = 1
  tableData.value = []
  tableColumns.value = []
  pagination.total = 0
  debugInfo.value = null
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  pagination.page = 1
  handleSearch()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  handleSearch()
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped lang="scss">
.detail-query {
  .search-panel {
    margin-bottom: 20px;

    .card-header {
      font-size: 16px;
      font-weight: bold;
    }

    .search-form {
      .el-form-item {
        margin-bottom: 16px;
      }
    }

    .search-buttons {
      display: flex;
      gap: 12px;
      margin-top: 8px;
    }
  }

  .table-panel {
    margin-bottom: 20px;

    :deep(.el-pagination) {
      display: flex;
    }

    :deep(.el-table .clickable-row) {
      cursor: pointer;

      &:hover {
        background-color: #f5f7fa;
      }
    }
  }

  .debug-panel {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 16px;
      font-weight: bold;
    }

    .debug-content {
      .debug-statistics {
        margin-bottom: 20px;
      }

      .debug-section {
        margin-bottom: 20px;

        h4 {
          margin: 0 0 10px 0;
          font-size: 14px;
          color: #606266;
        }

        .el-textarea {
          :deep(.el-textarea__inner) {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            color: #303133;
            background-color: #f5f7fa;
          }
        }
      }
    }
  }

  :deep(.el-dialog) {
    .el-descriptions {
      .detail-value {
        word-break: break-all;
      }
    }
  }

  :deep(.detail-dialog) {
    .el-dialog__body {
      padding: 20px;
      max-height: 70vh;
      overflow-y: auto;
    }

    .el-descriptions {
      .no-wrap-label {
        white-space: nowrap !important;
        width: auto !important;
        min-width: 140px;
      }
    }
  }
}
</style>
