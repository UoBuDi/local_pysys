import request from '@/axios'
import { DETAIL_QUERY_TIMEOUT } from '@/constants'

export interface DetailQueryParams {
  pass_id?: string
  entry_name?: string
  exit_name?: string
  start_time?: string
  end_time?: string
  plate_number?: string
  vehicle_type?: string
  billing_method?: string
  medium?: string
  settlement_date?: string
  data_type?: string
  split_month?: string
  page?: number
  page_size?: number
}

export interface DetailQueryData {
  list: Record<string, unknown>[]
  total: number
  page: number
  page_size: number
}

export interface DetailQueryDebugInfo {
  count_sql: string
  select_sql: string
  total_time: number
  count_duration: number
}

export type DetailQueryDataItem = Record<string, unknown>

export const queryDetailData = (params: DetailQueryParams) => {
  return request.post<DetailQueryData>({
    url: '/api/detail-query/',
    data: params,
    timeout: DETAIL_QUERY_TIMEOUT
  })
}
