import request from '@/axios'

export interface SplitMatchTable {
  table_name?: string
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
