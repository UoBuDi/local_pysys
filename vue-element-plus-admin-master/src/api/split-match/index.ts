import request from '@/axios'

export interface SplitMatchTable {
  table_name?: string
  records?: Array<{
    id: any
    通行标识ID?: string
    核查通行标识?: string
  }>
}

export interface SplitMatchData {
  total: number
  page: number
  page_size: number
  columns: string[]
  data: Record<string, unknown>[]
}

export interface MatchResult {
  matched_count: number
  unmatched_count: number
  total: number
  pass_id_matched?: number
  check_id_matched?: number
  debug?: {
    total_time?: number
    count_duration?: number
    yc_duration?: number
    cf_duration?: number
    match_duration?: number
    select_sql?: string
    yc_query?: string
    cf_query?: string
    update_by_pass_id_query?: string
    update_by_check_id_query?: string
    records_source?: string
    records_count?: number
    valid_record_count?: number
    cf_record_count?: number
    cf_table?: string
    pass_id_matched_count?: number
    check_id_matched_count?: number
    pass_id_update_count?: number
    check_id_update_count?: number
    pass_id_batch_count?: number
    check_id_batch_count?: number
  }
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export const getSplitMatchTables = () => {
  return request.get<ApiResponse<string[]>>({ url: '/api/split-match/tables/' })
}

export const getSplitMatchData = (params: {
  table_name?: string
  filters?: string
  page?: number
  page_size?: number
}) => {
  return request.get<ApiResponse<SplitMatchData>>({ url: '/api/split-match/data/', params })
}

export const executeSplitMatch = (data: SplitMatchTable) => {
  return request.post<ApiResponse<MatchResult>>({
    url: '/api/split-match/execute/',
    data: data,
    timeout: 300000
  })
}

export const previewSplitMatch = (data: SplitMatchTable) => {
  return request.post<
    ApiResponse<{
      sqls: Array<{
        name: string
        sql: string
        batch_count?: number
        total_count?: number
      }>
      total_records?: number
      error?: string
    }>
  >({
    url: '/api/split-match/preview/',
    data: data
  })
}

export const getCfTables = () => {
  return request.get<ApiResponse<string[]>>({ url: '/api/split-match/cf-tables/' })
}

export const updateSplitMatchData = (data: {
  table_name?: string
  row_id: string
  data: Record<string, unknown>
}) => {
  return request.post<ApiResponse<{ updated: boolean }>>({
    url: '/api/split-match/update/',
    data: data
  })
}

export interface ExportSplitMatchData {
  data: Record<string, unknown>[]
  columns: string[]
  column_types: Record<string, string>
}

export const getExportSplitMatchData = (params: { table_name?: string; filters?: string }) => {
  return request.get<ApiResponse<ExportSplitMatchData>>({ url: '/api/split-match/export/', params })
}
