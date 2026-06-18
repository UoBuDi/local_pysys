<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import {
  getScheduledTasksApi,
  updateScheduledTaskApi,
  runScheduledTaskApi,
  getTaskRunStatusApi,
  getDashboardStatisticsApi,
  getTaskExecutionHistoryApi,
  type ScheduledTask,
  type DashboardStatistics,
  type TaskExecutionHistory
} from '@/api/scheduled-tasks'
import { syncCloudPortalDataApi, getCloudPortalDataStatusApi } from '@/api/cloud-portal-data'
import {
  ElMessage,
  ElSwitch,
  ElTag,
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElButton,
  ElTable,
  ElTableColumn,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElTabs,
  ElTabPane,
  ElSelect,
  ElOption,
  ElAlert,
  ElPagination,
  ElTooltip,
  ElRadioGroup,
  ElRadioButton,
  ElRow,
  ElCol,
  ElInputNumber
} from 'element-plus'
import { ContentWrap } from '@/components/ContentWrap'
import { CloudPortalLoginDialog } from '@/components/CloudPortalLoginDialog'

// ==================== 数据状态 ====================
const tasks = ref<ScheduledTask[]>([])
const statistics = ref<DashboardStatistics | null>(null)
const loading = ref(false)
const editDialogVisible = ref(false)
const editingTask = ref<ScheduledTask | null>(null)
const editForm = ref({ cron_expression: '' })

// 云门户相关
const loginDialogVisible = ref(false)
const cloudPortalAccessToken = ref('')
const pendingTask = ref<ScheduledTask | null>(null)
const cloudPortalDataStatus = ref<{
  has_data: boolean
  last_update: string | null
  total_centers: number
  total_road_sections: number
  total_gantries: number
} | null>(null)

// 执行历史分页
const historyDialogVisible = ref(false)
const selectedTaskName = ref<string>('')
const historyList = ref<TaskExecutionHistory[]>([])
const historyTotal = ref(0)
const historyPage = ref(1)
const historyPageSize = ref(10)
const historyLoading = ref(false)

// 异步执行轮询
const runningTasks = ref<Map<string, { runId: string; taskName: string }>>(new Map())
let pollTimer: ReturnType<typeof setInterval> | null = null

// ==================== Cron 可视化编辑器状态 ====================
const cronType = ref<'daily' | 'interval' | 'weekly' | 'monthly' | 'custom'>('daily')
const cronDailyHour = ref(2)
const cronDailyMinute = ref(0)
const cronIntervalMinutes = ref(30)
const cronWeeklyDay = ref(1) // 1=周一
const cronWeeklyHour = ref(2)
const cronWeeklyMinute = ref(0)
const cronMonthlyDay = ref(1)
const cronMonthlyHour = ref(2)
const cronMonthlyMinute = ref(0)

const weekDayOptions = [
  { label: '周一', value: 1 },
  { label: '周二', value: 2 },
  { label: '周三', value: 3 },
  { label: '周四', value: 4 },
  { label: '周五', value: 5 },
  { label: '周六', value: 6 },
  { label: '周日', value: 0 }
]

// 从 Cron 表达式解析到可视化编辑器
const parseCronToVisual = (expr: string) => {
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) {
    cronType.value = 'custom'
    return
  }
  const [minute, hour, day, month, dow] = parts

  // 每天固定时间: 0 2 * * *
  if (day === '*' && month === '*' && dow === '*' && !minute.includes('/') && !hour.includes('/')) {
    cronType.value = 'daily'
    cronDailyHour.value = hour === '*' ? 0 : parseInt(hour)
    cronDailyMinute.value = minute === '*' ? 0 : parseInt(minute)
    return
  }

  // 间隔执行: */30 * * * *
  if (minute.startsWith('*/') && hour === '*' && day === '*' && month === '*' && dow === '*') {
    cronType.value = 'interval'
    cronIntervalMinutes.value = parseInt(minute.split('/')[1])
    return
  }

  // 每周固定时间: 0 2 * * 1
  if (day === '*' && month === '*' && dow !== '*' && !minute.includes('/') && !hour.includes('/')) {
    cronType.value = 'weekly'
    cronWeeklyDay.value = parseInt(dow)
    cronWeeklyHour.value = hour === '*' ? 0 : parseInt(hour)
    cronWeeklyMinute.value = parseInt(minute)
    return
  }

  // 每月固定时间: 0 2 1 * *
  if (day !== '*' && month === '*' && dow === '*' && !minute.includes('/') && !hour.includes('/')) {
    cronType.value = 'monthly'
    cronMonthlyDay.value = parseInt(day)
    cronMonthlyHour.value = hour === '*' ? 0 : parseInt(hour)
    cronMonthlyMinute.value = parseInt(minute)
    return
  }

  cronType.value = 'custom'
}

// 从可视化编辑器生成 Cron 表达式
const generateCronFromVisual = computed(() => {
  const pad = (n: number) => String(n).padStart(2, '0')
  switch (cronType.value) {
    case 'daily':
      return `${pad(cronDailyMinute.value)} ${pad(cronDailyHour.value)} * * *`
    case 'interval':
      return `*/${cronIntervalMinutes.value} * * * *`
    case 'weekly':
      return `${pad(cronWeeklyMinute.value)} ${pad(cronWeeklyHour.value)} * * ${cronWeeklyDay.value}`
    case 'monthly':
      return `${pad(cronMonthlyMinute.value)} ${pad(cronMonthlyHour.value)} ${cronMonthlyDay.value} * *`
    case 'custom':
      return editForm.value.cron_expression
    default:
      return '0 2 * * *'
  }
})

// 当可视化编辑器值变化时同步到 cron 表达式
const onCronVisualChange = () => {
  if (cronType.value !== 'custom') {
    editForm.value.cron_expression = generateCronFromVisual.value
  }
}

// ==================== 数据获取 ====================
const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getScheduledTasksApi()
    if (res.code === 200) {
      tasks.value = res.data || []
    }
  } catch (error) {
    console.error('获取定时任务列表失败:', error)
    ElMessage.error('获取定时任务列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStatistics = async () => {
  try {
    const res = await getDashboardStatisticsApi()
    if (res.code === 200) {
      statistics.value = res.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchExecutionHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getTaskExecutionHistoryApi(
      selectedTaskName.value || undefined,
      historyPage.value,
      historyPageSize.value
    )
    if (res.code === 200) {
      const data = res.data
      historyList.value = data.list || []
      historyTotal.value = data.total || 0
    }
  } catch (error) {
    console.error('获取执行历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

const fetchCloudPortalDataStatus = async () => {
  try {
    const res = await getCloudPortalDataStatusApi()
    if (res.code === 200) {
      cloudPortalDataStatus.value = res.data
    }
  } catch (error) {
    console.error('获取云门户数据状态失败:', error)
  }
}

// ==================== 任务操作 ====================
const handleToggleEnabled = async (task: ScheduledTask) => {
  const newEnabled = task.is_enabled === 1 ? 0 : 1
  try {
    const res = await updateScheduledTaskApi(task.id, { is_enabled: newEnabled })
    if (res.code === 200) {
      ElMessage.success(newEnabled === 1 ? '已启用任务' : '已禁用任务')
      await fetchTasks()
    } else {
      ElMessage.error(res.message || '操作失败')
    }
  } catch (error) {
    console.error('更新任务状态失败:', error)
    ElMessage.error('更新任务状态失败')
  }
}

const handleRunTask = async (task: ScheduledTask) => {
  // 云门户同步走单独流程
  if (task.task_name === 'cloud_portal_data_sync') {
    pendingTask.value = task
    loginDialogVisible.value = true
    return
  }

  // 标记为执行中
  const runKey = task.task_name
  runningTasks.value.set(runKey, { runId: '', taskName: task.task_name })

  try {
    const res = await runScheduledTaskApi(task.task_name)
    if (res.code === 200 && res.data) {
      const runId = res.data.run_id
      runningTasks.value.set(runKey, { runId, taskName: task.task_name })
      ElMessage.info('任务已提交执行，请等待完成...')
      // 启动轮询
      startPolling()
    } else {
      runningTasks.value.delete(runKey)
      ElMessage.error(res.message || '提交任务执行失败')
    }
  } catch (error) {
    runningTasks.value.delete(runKey)
    console.error('提交任务执行失败:', error)
    ElMessage.error('提交任务执行失败')
  }
}

// ==================== 异步执行轮询 ====================
const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(pollRunningTasks, 2000)
}

const pollRunningTasks = async () => {
  if (runningTasks.value.size === 0) {
    stopPolling()
    return
  }

  const entries = Array.from(runningTasks.value.entries())
  for (const [runKey, info] of entries) {
    if (!info.runId) continue
    try {
      const res = await getTaskRunStatusApi(info.runId)
      if (res.code === 200 && res.data) {
        if (res.data.status !== 'running') {
          runningTasks.value.delete(runKey)
          if (res.data.status === 'success') {
            ElMessage.success(`${info.taskName} 执行成功: ${res.data.message}`)
          } else {
            ElMessage.error(`${info.taskName} 执行失败: ${res.data.message}`)
          }
          await fetchTasks()
          await fetchStatistics()
          if (historyDialogVisible.value) {
            await fetchExecutionHistory()
          }
        }
      } else if (res.code === 404) {
        runningTasks.value.delete(runKey)
      }
    } catch {
      // 轮询失败不中断，继续下次
    }
  }
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const isTaskRunning = (taskName: string) => {
  return runningTasks.value.has(taskName)
}

// ==================== 云门户同步 ====================
const handleLoginSuccess = async (data: { access_token: string; user_info: any }) => {
  cloudPortalAccessToken.value = data.access_token
  loginDialogVisible.value = false
  await executeCloudPortalDataSync()
}

const executeCloudPortalDataSync = async () => {
  if (!pendingTask.value) return

  const runKey = pendingTask.value.task_name
  runningTasks.value.set(runKey, { runId: '', taskName: pendingTask.value.task_name })

  try {
    ElMessage.info('正在同步云门户数据...')
    const res = await syncCloudPortalDataApi({ access_token: cloudPortalAccessToken.value })

    runningTasks.value.delete(runKey)

    if (res.code === 200) {
      ElMessage.success(res.message || '数据同步成功')
      await fetchTasks()
      await fetchCloudPortalDataStatus()
      if (historyDialogVisible.value) {
        await fetchExecutionHistory()
      }
    } else {
      ElMessage.error(res.message || '数据同步失败')
    }
  } catch (error) {
    runningTasks.value.delete(runKey)
    console.error('执行云门户数据同步失败:', error)
    ElMessage.error('执行云门户数据同步失败')
  } finally {
    pendingTask.value = null
  }
}

// ==================== 编辑任务 ====================
const handleEditTask = (task: ScheduledTask) => {
  editingTask.value = task
  editForm.value.cron_expression = task.cron_expression || ''
  parseCronToVisual(task.cron_expression || '')
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editingTask.value) return

  // 自定义模式下验证 cron 表达式
  if (cronType.value === 'custom' && !validateCronExpression(editForm.value.cron_expression)) {
    ElMessage.error('Cron表达式格式无效')
    return
  }

  // 非自定义模式下用可视化编辑器的值
  const cronExpr =
    cronType.value === 'custom' ? editForm.value.cron_expression : generateCronFromVisual.value

  try {
    const res = await updateScheduledTaskApi(editingTask.value.id, {
      cron_expression: cronExpr
    })
    if (res.code === 200) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      await fetchTasks()
    } else {
      ElMessage.error(res.message || '更新失败')
    }
  } catch (error) {
    console.error('更新任务失败:', error)
    ElMessage.error('更新任务失败')
  }
}

// ==================== 查看执行历史 ====================
const handleViewHistory = (task: ScheduledTask) => {
  selectedTaskName.value = task.task_name
  historyPage.value = 1
  historyDialogVisible.value = true
  fetchExecutionHistory()
}

const handleHistoryPageChange = (page: number) => {
  historyPage.value = page
  fetchExecutionHistory()
}

const handleHistorySizeChange = (size: number) => {
  historyPageSize.value = size
  historyPage.value = 1
  fetchExecutionHistory()
}

// ==================== 工具函数 ====================
const validateCronExpression = (expression: string): boolean => {
  if (!expression) return false
  const parts = expression.trim().split(/\s+/)
  if (parts.length !== 5) return false

  const validatePart = (part: string, min: number, max: number): boolean => {
    if (part === '*') return true
    if (part === '?') return true
    if (/^\d+$/.test(part)) {
      const num = parseInt(part)
      return num >= min && num <= max
    }
    if (/^\d+-\d+$/.test(part)) {
      const [start, end] = part.split('-').map(Number)
      return start >= min && end <= max && start <= end
    }
    if (/^\*\/\d+$/.test(part)) {
      const step = parseInt(part.split('/')[1])
      return step > 0 && step <= max
    }
    if (/^\d+(,\d+)*$/.test(part)) {
      const nums = part.split(',').map(Number)
      return nums.every((n) => n >= min && n <= max)
    }
    return false
  }

  return (
    validatePart(parts[0], 0, 59) &&
    validatePart(parts[1], 0, 23) &&
    validatePart(parts[2], 1, 31) &&
    validatePart(parts[3], 1, 12) &&
    validatePart(parts[4], 0, 6)
  )
}

const getStatusType = (status: string | null): 'success' | 'danger' | 'warning' | 'info' => {
  if (!status) return 'info'
  if (status === 'success') return 'success'
  if (status === 'failed') return 'danger'
  if (status === 'running') return 'warning'
  return 'warning'
}

const getStatusText = (status: string | null): string => {
  if (!status) return '未执行'
  if (status === 'success') return '成功'
  if (status === 'failed') return '失败'
  if (status === 'running') return '执行中'
  return status
}

const formatNumber = (num: number | undefined | null): string => {
  if (num === undefined || num === null) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
}

const getCronDescription = (expr: string): string => {
  if (!expr) return ''
  const parts = expr.trim().split(/\s+/)
  if (parts.length !== 5) return expr

  const [minute, hour, day, month, dow] = parts

  if (minute.startsWith('*/') && hour === '*' && day === '*' && month === '*' && dow === '*') {
    return `每${minute.split('/')[1]}分钟执行`
  }
  if (day === '*' && month === '*' && dow === '*' && !minute.includes('/')) {
    return `每天 ${hour.padStart(2, '0')}:${minute.padStart(2, '0')} 执行`
  }
  if (day === '*' && month === '*' && dow !== '*' && !minute.includes('/')) {
    const dayName = weekDayOptions.find((d) => d.value === parseInt(dow))?.label || dow
    return `每${dayName} ${hour.padStart(2, '0')}:${minute.padStart(2, '0')} 执行`
  }
  if (day !== '*' && month === '*' && dow === '*' && !minute.includes('/')) {
    return `每月${day}日 ${hour.padStart(2, '0')}:${minute.padStart(2, '0')} 执行`
  }
  return expr
}

// ==================== 生命周期 ====================
onMounted(() => {
  fetchTasks()
  fetchStatistics()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <ContentWrap title="定时任务管理">
    <!-- 连续失败告警 -->
    <ElAlert
      v-for="task in tasks.filter((t) => t.consecutive_failures >= 3)"
      :key="'alert-' + task.task_name"
      :title="`告警: 任务「${task.task_name}」已连续失败 ${task.consecutive_failures} 次，请检查任务配置或数据源`"
      type="error"
      show-icon
      :closable="false"
      class="mb-12px"
    />

    <ElTabs>
      <!-- 任务列表 Tab -->
      <ElTabPane label="任务列表">
        <ElCard class="mb-20px">
          <template #header>
            <div class="flex justify-between items-center">
              <span>任务列表</span>
              <ElButton type="primary" @click="fetchTasks" :loading="loading">刷新</ElButton>
            </div>
          </template>
          <ElTable :data="tasks" v-loading="loading" stripe>
            <ElTableColumn prop="task_name" label="任务名称" width="220" />
            <ElTableColumn prop="task_type" label="任务类型" width="100">
              <template #default="{ row }">
                <ElTag size="small" :type="row.task_type === 'statistics' ? 'primary' : 'success'">
                  {{ row.task_type === 'statistics' ? '统计' : '同步' }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn
              prop="description"
              label="任务描述"
              min-width="200"
              show-overflow-tooltip
            />
            <ElTableColumn prop="cron_expression" label="Cron表达式" width="130" />
            <ElTableColumn label="执行频率" width="160">
              <template #default="{ row }">
                <span class="cron-desc">{{ getCronDescription(row.cron_expression) }}</span>
              </template>
            </ElTableColumn>
            <ElTableColumn label="状态" width="90">
              <template #default="{ row }">
                <ElSwitch
                  :model-value="row.is_enabled === 1"
                  @change="handleToggleEnabled(row)"
                  active-text="启用"
                  inactive-text="禁用"
                />
              </template>
            </ElTableColumn>
            <ElTableColumn label="上次执行状态" width="120">
              <template #default="{ row }">
                <ElTag :type="getStatusType(row.last_run_status)">
                  {{ getStatusText(row.last_run_status) }}
                </ElTag>
              </template>
            </ElTableColumn>
            <ElTableColumn prop="last_run_time" label="上次执行时间" width="170" />
            <ElTableColumn
              prop="last_run_message"
              label="执行消息"
              min-width="180"
              show-overflow-tooltip
            />
            <ElTableColumn label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <ElButton
                  type="primary"
                  size="small"
                  @click="handleRunTask(row)"
                  :loading="isTaskRunning(row.task_name)"
                  v-hasPermi="'scheduled-tasks:run'"
                >
                  {{ isTaskRunning(row.task_name) ? '执行中...' : '立即执行' }}
                </ElButton>
                <ElButton
                  type="default"
                  size="small"
                  @click="handleEditTask(row)"
                  v-hasPermi="'scheduled-tasks:edit'"
                >
                  编辑
                </ElButton>
                <ElButton
                  type="info"
                  size="small"
                  @click="handleViewHistory(row)"
                  v-hasPermi="'scheduled-tasks:view-history'"
                >
                  历史
                </ElButton>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElTabPane>

      <!-- 统计数据 Tab -->
      <ElTabPane label="统计数据">
        <ElCard v-if="statistics">
          <template #header>
            <div class="flex justify-between items-center">
              <span>Dashboard统计数据 ({{ statistics.stat_month }})</span>
              <ElButton type="primary" @click="fetchStatistics">刷新统计</ElButton>
            </div>
          </template>
          <ElDescriptions :column="4" border>
            <ElDescriptionsItem label="统计月份">{{ statistics.stat_month }}</ElDescriptionsItem>
            <ElDescriptionsItem label="总交易数">{{
              formatNumber(statistics.total_transactions)
            }}</ElDescriptionsItem>
            <ElDescriptionsItem label="总交易金额"
              >¥{{ formatNumber(statistics.total_amount) }}</ElDescriptionsItem
            >
            <ElDescriptionsItem label="总拆分金额"
              >¥{{ formatNumber(statistics.total_split_amount) }}</ElDescriptionsItem
            >
            <ElDescriptionsItem label="收费站数量">{{
              statistics.station_count
            }}</ElDescriptionsItem>
            <ElDescriptionsItem label="更新时间" :span="3">{{
              statistics.updated_at
            }}</ElDescriptionsItem>
          </ElDescriptions>

          <div class="mt-20px" v-if="statistics.vehicle_types && statistics.vehicle_types.length">
            <h4 class="mb-10px">车型分布</h4>
            <ElTable
              :data="statistics.vehicle_types.slice(0, 10)"
              stripe
              size="small"
              max-height="300"
            >
              <ElTableColumn prop="type" label="车型" width="150" />
              <ElTableColumn prop="count" label="数量">
                <template #default="{ row }">
                  {{ formatNumber(row.count) }}
                </template>
              </ElTableColumn>
            </ElTable>
          </div>

          <div
            class="mt-20px"
            v-if="statistics.daily_transactions && statistics.daily_transactions.length"
          >
            <h4 class="mb-10px">每日交易趋势 (最近7天)</h4>
            <ElTable :data="statistics.daily_transactions.slice(-7)" stripe size="small">
              <ElTableColumn prop="date" label="日期" width="150" />
              <ElTableColumn prop="count" label="交易数">
                <template #default="{ row }">
                  {{ formatNumber(row.count) }}
                </template>
              </ElTableColumn>
            </ElTable>
          </div>
        </ElCard>
      </ElTabPane>
    </ElTabs>

    <!-- 编辑任务对话框（含 Cron 可视化编辑器） -->
    <ElDialog v-model="editDialogVisible" title="编辑任务配置" width="600px">
      <ElForm :model="editForm" label-width="120px">
        <ElFormItem label="任务名称">
          <ElInput :model-value="editingTask?.task_name" disabled />
        </ElFormItem>
        <ElFormItem label="任务描述">
          <ElInput :model-value="editingTask?.description" disabled />
        </ElFormItem>
        <ElFormItem label="调度方式" required>
          <ElRadioGroup v-model="cronType" @change="onCronVisualChange">
            <ElRadioButton value="daily">每天</ElRadioButton>
            <ElRadioButton value="interval">间隔</ElRadioButton>
            <ElRadioButton value="weekly">每周</ElRadioButton>
            <ElRadioButton value="monthly">每月</ElRadioButton>
            <ElRadioButton value="custom">自定义</ElRadioButton>
          </ElRadioGroup>
        </ElFormItem>

        <!-- 每天 -->
        <ElFormItem v-if="cronType === 'daily'" label="执行时间">
          <ElRow :gutter="8" align="middle">
            <ElCol :span="11">
              <ElInputNumber
                v-model="cronDailyHour"
                :min="0"
                :max="23"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="2" class="text-center">时</ElCol>
            <ElCol :span="11">
              <ElInputNumber
                v-model="cronDailyMinute"
                :min="0"
                :max="59"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="2" class="text-center">分</ElCol>
          </ElRow>
        </ElFormItem>

        <!-- 间隔执行 -->
        <ElFormItem v-if="cronType === 'interval'" label="执行间隔">
          <ElRow :gutter="8" align="middle">
            <ElCol :span="16">
              <ElInputNumber
                v-model="cronIntervalMinutes"
                :min="1"
                :max="1440"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="8">分钟</ElCol>
          </ElRow>
        </ElFormItem>

        <!-- 每周 -->
        <ElFormItem v-if="cronType === 'weekly'" label="执行时间">
          <ElRow :gutter="8" align="middle">
            <ElCol :span="8">
              <ElSelect v-model="cronWeeklyDay" @change="onCronVisualChange">
                <ElOption
                  v-for="d in weekDayOptions"
                  :key="d.value"
                  :label="d.label"
                  :value="d.value"
                />
              </ElSelect>
            </ElCol>
            <ElCol :span="8">
              <ElInputNumber
                v-model="cronWeeklyHour"
                :min="0"
                :max="23"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="2" class="text-center">时</ElCol>
            <ElCol :span="5">
              <ElInputNumber
                v-model="cronWeeklyMinute"
                :min="0"
                :max="59"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="1" class="text-center">分</ElCol>
          </ElRow>
        </ElFormItem>

        <!-- 每月 -->
        <ElFormItem v-if="cronType === 'monthly'" label="执行时间">
          <ElRow :gutter="8" align="middle">
            <ElCol :span="5">
              <ElInputNumber
                v-model="cronMonthlyDay"
                :min="1"
                :max="31"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="3" class="text-center">日</ElCol>
            <ElCol :span="8">
              <ElInputNumber
                v-model="cronMonthlyHour"
                :min="0"
                :max="23"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="2" class="text-center">时</ElCol>
            <ElCol :span="5">
              <ElInputNumber
                v-model="cronMonthlyMinute"
                :min="0"
                :max="59"
                controls-position="right"
                @change="onCronVisualChange"
              />
            </ElCol>
            <ElCol :span="1" class="text-center">分</ElCol>
          </ElRow>
        </ElFormItem>

        <!-- 自定义 -->
        <ElFormItem v-if="cronType === 'custom'" label="Cron表达式" required>
          <ElInput v-model="editForm.cron_expression" placeholder="例如: 0 2 * * *" />
          <div class="cron-help">
            <p>格式: 分 时 日 月 周</p>
            <p>示例: 0 2 * * * (每天凌晨2点执行)</p>
            <p>示例: */30 * * * * (每30分钟执行)</p>
            <p>示例: 0 2 * * 1-5 (工作日凌晨2点执行)</p>
          </div>
        </ElFormItem>

        <!-- 预览生成的 Cron 表达式 -->
        <ElFormItem v-if="cronType !== 'custom'" label="生成表达式">
          <ElTooltip :content="getCronDescription(generateCronFromVisual)" placement="top">
            <ElTag type="info" size="large">{{ generateCronFromVisual }}</ElTag>
          </ElTooltip>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editDialogVisible = false">取消</ElButton>
        <ElButton type="primary" @click="handleSaveEdit">保存</ElButton>
      </template>
    </ElDialog>

    <!-- 执行历史对话框（分页） -->
    <ElDialog
      v-model="historyDialogVisible"
      :title="`执行历史 - ${selectedTaskName}`"
      width="800px"
    >
      <ElTable :data="historyList" v-loading="historyLoading" stripe max-height="450">
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="start_time" label="开始时间" width="170" />
        <ElTableColumn prop="end_time" label="结束时间" width="170" />
        <ElTableColumn label="耗时" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration_seconds) }}
          </template>
        </ElTableColumn>
        <ElTableColumn prop="message" label="执行消息" show-overflow-tooltip />
      </ElTable>
      <div class="pagination-container">
        <ElPagination
          v-model:current-page="historyPage"
          v-model:page-size="historyPageSize"
          :total="historyTotal"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleHistoryPageChange"
          @size-change="handleHistorySizeChange"
        />
      </div>
      <template #footer>
        <ElButton @click="historyDialogVisible = false">关闭</ElButton>
        <ElButton type="primary" @click="fetchExecutionHistory" :loading="historyLoading">
          刷新
        </ElButton>
      </template>
    </ElDialog>

    <!-- 云门户登录对话框 -->
    <CloudPortalLoginDialog
      v-model:visible="loginDialogVisible"
      title="云门户登录 - 数据同步"
      @success="handleLoginSuccess"
      @cancel="pendingTask = null"
    />
  </ContentWrap>
</template>

<style scoped>
.mb-20px {
  margin-bottom: 20px;
}
.mb-12px {
  margin-bottom: 12px;
}
.mt-20px {
  margin-top: 20px;
}
.mb-10px {
  margin-bottom: 10px;
}
.cron-help {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  line-height: 1.6;
}
.cron-help p {
  margin: 2px 0;
}
.cron-desc {
  font-size: 12px;
  color: #606266;
}
.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
.text-center {
  text-align: center;
  line-height: 32px;
}
</style>
