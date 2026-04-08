import request from '@/axios'

export interface CloudPortalDataStatus {
  has_data: boolean
  last_update: string | null
  total_centers: number
  total_road_sections: number
  total_gantries: number
}

export interface CloudPortalDataSyncRequest {
  access_token: string
}

export interface CloudPortalDataSyncResult {
  success: boolean
  message: string
  data: any
  statistics: {
    total_centers: number
    total_road_sections: number
    total_gantries: number
    failed_centers: Array<{
      centerNo: string
      centerName: string
      error: string
    }>
    failed_sections: Array<{
      roadSectionNo: string
      roadSectionName: string
      centerNo: string
      error: string
    }>
  }
}

export const getCloudPortalDataApi = () => {
  return request.get({ url: '/api/cloud-portal-data/' })
}

export const syncCloudPortalDataApi = (data: CloudPortalDataSyncRequest) => {
  return request.post({ url: '/api/cloud-portal-data/sync', data })
}

export const getCloudPortalDataStatusApi = () => {
  return request.get<CloudPortalDataStatus>({ url: '/api/cloud-portal-data/status' })
}
