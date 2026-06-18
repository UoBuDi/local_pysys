import request from '@/axios'
import type {
  ScheduledTask,
  DashboardStatistics,
  TaskExecutionHistory,
  ExecutionHistoryPage,
  UpdateTaskRequest,
  RunTaskResponse,
  TaskRunStatus
} from './types'

export type {
  ScheduledTask,
  DashboardStatistics,
  TaskExecutionHistory,
  ExecutionHistoryPage,
  UpdateTaskRequest,
  RunTaskResponse,
  TaskRunStatus
}

export const getScheduledTasksApi = () => {
  return request.get({ url: '/api/scheduled-tasks/' })
}

export const updateScheduledTaskApi = (taskId: number, data: UpdateTaskRequest) => {
  return request.put({ url: `/api/scheduled-tasks/${taskId}`, data })
}

export const runScheduledTaskApi = (taskName: string) => {
  return request.post<RunTaskResponse>({ url: `/api/scheduled-tasks/${taskName}/run` })
}

export const getTaskRunStatusApi = (runId: string) => {
  return request.get<TaskRunStatus>({ url: `/api/scheduled-tasks/run-status/${runId}` })
}

export const getDashboardStatisticsApi = (statMonth?: string) => {
  return request.get<DashboardStatistics>({
    url: '/api/dashboard-statistics/',
    params: statMonth ? { stat_month: statMonth } : undefined
  })
}

export const getTaskExecutionHistoryApi = (
  taskName?: string,
  page: number = 1,
  pageSize: number = 10
) => {
  const params: Record<string, any> = { page, page_size: pageSize }
  if (taskName) {
    params.task_name = taskName
  }
  return request.get<ExecutionHistoryPage>({ url: '/api/task-execution-history/', params })
}
