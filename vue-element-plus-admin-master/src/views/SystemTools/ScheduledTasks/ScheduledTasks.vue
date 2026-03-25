<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  getScheduledTasksApi,
  updateScheduledTaskApi,
  runScheduledTaskApi,
  getDashboardStatisticsApi,
  getTaskExecutionHistoryApi,
  type ScheduledTask,
  type DashboardStatistics,
  type TaskExecutionHistory
} from '@/api/scheduled-tasks'
import { ElMessage, ElSwitch, ElTag, ElCard, ElDescriptions, ElDescriptionsItem, ElButton, ElTable, ElTableColumn, ElDialog, ElForm, ElFormItem, ElInput, ElTabs, ElTabPane, ElTimeline, ElTimelineItem } from 'element-plus'
import { ContentWrap } from '@/components/ContentWrap'

const tasks = ref<ScheduledTask[]>([])
const statistics = ref<DashboardStatistics | null>(null)
const executionHistory = ref<TaskExecutionHistory[]>([])
const loading = ref(false)
const historyLoading = ref(false)
const runLoading = ref<string | null>(null)
const editDialogVisible = ref(false)
const historyDialogVisible = ref(false)
const editingTask = ref<ScheduledTask | null>(null)
const selectedTaskName = ref<string>('')
const editForm = ref({
  cron_expression: ''
})

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

const fetchExecutionHistory = async (taskName?: string) => {
  historyLoading.value = true
  try {
    const res = await getTaskExecutionHistoryApi(taskName, 50)
    if (res.code === 200) {
      executionHistory.value = res.data || []
    }
  } catch (error) {
    console.error('获取执行历史失败:', error)
  } finally {
    historyLoading.value = false
  }
}

const handleToggleEnabled = async (task: ScheduledTask) => {
  try {
    const res = await updateScheduledTaskApi(task.id, { is_enabled: task.is_enabled ? 0 : 1 })
    if (res.code === 200) {
      ElMessage.success(task.is_enabled ? '已禁用任务' : '已启用任务')
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
  runLoading.value = task.task_name
  try {
    ElMessage.info('正在执行任务...')
    const res = await runScheduledTaskApi(task.task_name)
    if (res.code === 200) {
      ElMessage.success(res.message || '任务执行成功')
      await fetchTasks()
      await fetchStatistics()
      if (historyDialogVisible.value) {
        await fetchExecutionHistory(selectedTaskName.value)
      }
    } else {
      ElMessage.error(res.message || '任务执行失败')
    }
  } catch (error) {
    console.error('执行任务失败:', error)
    ElMessage.error('执行任务失败')
  } finally {
    runLoading.value = null
  }
}

const handleEditTask = (task: ScheduledTask) => {
  editingTask.value = task
  editForm.value.cron_expression = task.cron_expression || ''
  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editingTask.value) return
  
  if (!validateCronExpression(editForm.value.cron_expression)) {
    ElMessage.error('Cron表达式格式无效')
    return
  }
  
  try {
    const res = await updateScheduledTaskApi(editingTask.value.id, {
      cron_expression: editForm.value.cron_expression
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

const handleViewHistory = (task: ScheduledTask) => {
  selectedTaskName.value = task.task_name
  historyDialogVisible.value = true
  fetchExecutionHistory(task.task_name)
}

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
      return nums.every(n => n >= min && n <= max)
    }
    return false
  }
  
  return validatePart(parts[0], 0, 59) &&
         validatePart(parts[1], 0, 23) &&
         validatePart(parts[2], 1, 31) &&
         validatePart(parts[3], 1, 12) &&
         validatePart(parts[4], 0, 6)
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

const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(2) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(2) + 'K'
  }
  return num.toString()
}

const formatDuration = (seconds: number | null): string => {
  if (!seconds) return '-'
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
  return `${Math.floor(seconds / 3600)}时${Math.floor((seconds % 3600) / 60)}分`
}

onMounted(() => {
  fetchTasks()
  fetchStatistics()
})
</script>

<template>
  <ContentWrap title="定时任务管理">
    <ElTabs>
      <ElTabPane label="任务列表">
        <ElCard class="mb-20px">
          <template #header>
            <div class="flex justify-between items-center">
              <span>任务列表</span>
              <ElButton type="primary" @click="fetchTasks" :loading="loading">刷新</ElButton>
            </div>
          </template>
          <ElTable :data="tasks" v-loading="loading" stripe>
            <ElTableColumn prop="task_name" label="任务名称" width="250" />
            <ElTableColumn prop="task_type" label="任务类型" width="120" />
            <ElTableColumn prop="cron_expression" label="Cron表达式" width="150" />
            <ElTableColumn label="状态" width="100">
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
            <ElTableColumn prop="last_run_time" label="上次执行时间" width="180" />
            <ElTableColumn prop="last_run_message" label="执行消息" min-width="200" show-overflow-tooltip />
            <ElTableColumn label="操作" width="260" fixed="right">
              <template #default="{ row }">
                <ElButton
                  type="primary"
                  size="small"
                  @click="handleRunTask(row)"
                  :loading="runLoading === row.task_name"
                >
                  立即执行
                </ElButton>
                <ElButton
                  type="default"
                  size="small"
                  @click="handleEditTask(row)"
                >
                  编辑
                </ElButton>
                <ElButton
                  type="info"
                  size="small"
                  @click="handleViewHistory(row)"
                >
                  历史
                </ElButton>
              </template>
            </ElTableColumn>
          </ElTable>
        </ElCard>
      </ElTabPane>

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
            <ElDescriptionsItem label="总交易数">{{ formatNumber(statistics.total_transactions) }}</ElDescriptionsItem>
            <ElDescriptionsItem label="总交易金额">¥{{ formatNumber(statistics.total_amount) }}</ElDescriptionsItem>
            <ElDescriptionsItem label="总拆分金额">¥{{ formatNumber(statistics.total_split_amount) }}</ElDescriptionsItem>
            <ElDescriptionsItem label="收费站数量">{{ statistics.station_count }}</ElDescriptionsItem>
            <ElDescriptionsItem label="更新时间" :span="3">{{ statistics.updated_at }}</ElDescriptionsItem>
          </ElDescriptions>

          <div class="mt-20px" v-if="statistics.vehicle_types && statistics.vehicle_types.length">
            <h4 class="mb-10px">车型分布</h4>
            <ElTable :data="statistics.vehicle_types.slice(0, 10)" stripe size="small" max-height="300">
              <ElTableColumn prop="type" label="车型" width="150" />
              <ElTableColumn prop="count" label="数量">
                <template #default="{ row }">
                  {{ formatNumber(row.count) }}
                </template>
              </ElTableColumn>
            </ElTable>
          </div>

          <div class="mt-20px" v-if="statistics.daily_transactions && statistics.daily_transactions.length">
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

    <ElDialog v-model="editDialogVisible" title="编辑任务配置" width="500px">
      <ElForm :model="editForm" label-width="120px">
        <ElFormItem label="任务名称">
          <ElInput :model-value="editingTask?.task_name" disabled />
        </ElFormItem>
        <ElFormItem label="Cron表达式" required>
          <ElInput v-model="editForm.cron_expression" placeholder="例如: 0 2 * * *" />
          <div class="cron-help">
            <p>格式: 分 时 日 月 周</p>
            <p>示例: 0 2 * * * (每天凌晨2点执行)</p>
            <p>示例: */30 * * * * (每30分钟执行)</p>
          </div>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="editDialogVisible = false">取消</ElButton>
        <ElButton type="primary" @click="handleSaveEdit">保存</ElButton>
      </template>
    </ElDialog>

    <ElDialog v-model="historyDialogVisible" :title="`执行历史 - ${selectedTaskName}`" width="800px">
      <ElTable :data="executionHistory" v-loading="historyLoading" stripe max-height="500">
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="start_time" label="开始时间" width="180" />
        <ElTableColumn prop="end_time" label="结束时间" width="180" />
        <ElTableColumn label="耗时" width="120">
          <template #default="{ row }">
            {{ formatDuration(row.duration_seconds) }}
          </template>
        </ElTableColumn>
        <ElTableColumn prop="message" label="执行消息" show-overflow-tooltip />
      </ElTable>
      <template #footer>
        <ElButton @click="historyDialogVisible = false">关闭</ElButton>
        <ElButton type="primary" @click="fetchExecutionHistory(selectedTaskName)" :loading="historyLoading">刷新</ElButton>
      </template>
    </ElDialog>
  </ContentWrap>
</template>

<style scoped>
.mb-20px {
  margin-bottom: 20px;
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
</style>
