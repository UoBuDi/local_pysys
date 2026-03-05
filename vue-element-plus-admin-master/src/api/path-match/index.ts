import request from '@/axios'

export interface PathMatchRequest {
  timeRange: string[]
  transactionTimeRange: string[]
  includeUnits: string
  endUnit: string
  excludeExits: string
  excludeUnits: string
  excludeGreenChannel: boolean
  vehicleTypes: string
}

export interface PathMatchResult {
  id: number
  path: string
  totalAmount: number
  startTime: string
  endTime: string
  exitName: string
  [key: string]: any
}

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
  count?: number
  debug?: any
}

export const getPathMatchTables = () => {
  return request.get<ApiResponse<string[]>>({ url: '/api/path-match/tables/' })
}

export const searchPathMatch = (params: PathMatchRequest) => {
  return request.post<ApiResponse<PathMatchResult[]>>({
    url: '/api/path-match/search',
    data: params
  })
}

export const getProvincesByCodes = (codes: string[]) => {
  return request.post<ApiResponse<Record<string, string>>>({
    url: '/api/path-match/provinces',
    data: { codes }
  })
}

export const getPathMatchDetail = (passageId: string, tableName?: string) => {
  return request.post<ApiResponse<Record<string, any>>>({
    url: '/api/path-match/detail',
    data: { passageId, tableName: tableName || '' }
  })
}
