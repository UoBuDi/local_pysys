export interface ScheduledTask {
  id: number
  task_name: string
  task_type: string
  cron_expression: string
  is_enabled: number
  last_run_time: string | null
  next_run_time: string | null
  last_run_status: string | null
  last_run_message: string | null
  created_at: string
  updated_at: string
}

export interface DashboardStatistics {
  id: number
  stat_date: string
  stat_month: string
  total_transactions: number
  free_transactions: number
  split_section_amount: number
  total_amount?: number
  total_split_amount?: number
  station_count?: number
  vehicle_types: Array<{ type: string; code: string; count: number }>
  media_types: Array<{ type: string | null; count: number }>
  province_data: Array<{ province: string; count: number }>
  daily_transactions?: Array<{ date: string; count: number }>
  created_at: string
  updated_at: string
}

export interface TaskExecutionHistory {
  id: number
  task_name: string
  start_time: string
  end_time: string | null
  status: 'running' | 'success' | 'failed'
  message: string | null
  details: Record<string, any> | null
  duration_seconds: number | null
  created_at: string
}

export interface UpdateTaskRequest {
  is_enabled?: number
  cron_expression?: string
}

export interface RunTaskResponse {
  success: boolean
  message: string
  data?: Record<string, any>
  executed_at: string
}
