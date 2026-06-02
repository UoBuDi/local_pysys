import request from '@/axios'
import type {
  ScheduledTask,
  DashboardStatistics,
  TaskExecutionHistory,
  UpdateTaskRequest
} from './types'

export type { ScheduledTask, DashboardStatistics, TaskExecutionHistory, UpdateTaskRequest }

export const getScheduledTasksApi = () => {
  return request.get({ url: '/api/scheduled-tasks/' })
}

export const updateScheduledTaskApi = (taskId: number, data: UpdateTaskRequest) => {
  return request.put({ url: `/api/scheduled-tasks/${taskId}`, data })
}

export const runScheduledTaskApi = (taskName: string) => {
  return request.post({ url: `/api/scheduled-tasks/${taskName}/run` })
}

export const getDashboardStatisticsApi = () => {
  return request.get<DashboardStatistics>({ url: '/api/dashboard-statistics/' })
}

export const getTaskExecutionHistoryApi = (taskName?: string, limit: number = 20) => {
  const params: Record<string, any> = { limit }
  if (taskName) {
    params.task_name = taskName
  }
  return request.get({ url: '/api/task-execution-history/', params })
}
