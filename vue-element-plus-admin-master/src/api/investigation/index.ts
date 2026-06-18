import request from '@/axios'

export interface InvestigationAddParams {
  pass_id: string
  plate_number: string
}

export interface InvestigationQueryParams {
  page?: number
  page_size?: number
  pass_id?: string
  plate_number?: string
  created_by?: string
  review_status?: string
  start_time?: string
  end_time?: string
}

export interface InvestigationRecord {
  id: number
  pass_id: string
  plate_number: string
  add_time: string
  created_by: string
  review_result: string | null
  reviewed_by: string | null
  review_time: string | null
  created_at: string
  updated_at: string
}

export interface InvestigationListData {
  records: InvestigationRecord[]
  total: number
  page: number
  page_size: number
}

export interface InvestigationReviewParams {
  id: number
  review_result: string
}

export interface PassRecordData {
  records: Record<string, any>[]
  columns: string[]
  total: number
  table_name: string
}

/** 加入追查 */
export const addToInvestigation = (data: InvestigationAddParams) => {
  return request.post({ url: '/api/investigation/add', data })
}

/** 查询追查详单列表 */
export const getInvestigationList = (params: InvestigationQueryParams) => {
  return request.get<InvestigationListData>({ url: '/api/investigation/list', params })
}

/** 提交复核结果 */
export const reviewInvestigation = (data: InvestigationReviewParams) => {
  return request.put({ url: '/api/investigation/review', data })
}

/** 删除追查详单记录 */
export const deleteInvestigation = (id: number) => {
  return request.delete({ url: `/api/investigation/${id}` })
}

/** 导出追查详单 */
export const exportInvestigation = (params: InvestigationQueryParams) => {
  return request.get({ url: '/api/investigation/export', params, responseType: 'blob' })
}

/** 根据通行标识ID查询通行记录 */
export const getPassRecords = (pass_id: string) => {
  return request.get<PassRecordData>({ url: '/api/investigation/pass-records', params: { pass_id } })
}
