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

export interface VerifyPassIdResult {
  exists: boolean
  match_count: number
  records: Array<Record<string, unknown>>
  query_time: number
}

export const verifyPassId = (params: {
  pass_id: string
  verify_type: string
  user_id?: number
  username?: string
}) => {
  return request.get<ApiResponse<VerifyPassIdResult>>({
    url: '/api/split-match/verify-pass-id/',
    params
  })
}

export interface VerifyHistoryRecord {
  id: number
  pass_id: string
  verify_type: string
  table_name: string
  match_count: number
  verify_result: VerifyPassIdResult
  user_id: number | null
  username: string | null
  verify_time: string
}

export const getVerifyHistory = (params: {
  pass_id?: string
  user_id?: number
  page?: number
  page_size?: number
}) => {
  return request.get<
    ApiResponse<{
      list: VerifyHistoryRecord[]
      total: number
      page: number
      page_size: number
    }>
  >({
    url: '/api/split-match/verify-history/',
    params
  })
}

export interface CloudPortalCaptchaResult {
  session_id: string
  img: string
  uuid: string
}

export const getCloudPortalCaptcha = (sessionId?: string) => {
  const params: Record<string, string> = {}
  if (sessionId) {
    params.session_id = sessionId
  }
  return request.get<ApiResponse<CloudPortalCaptchaResult>>({
    url: '/api/cloud-portal/captcha',
    params,
    timeout: 30000
  })
}

export interface CloudPortalLoginResult {
  user_info?: {
    id?: number
    username?: string
    real_name?: string
    [key: string]: unknown
  }
}

export const cloudPortalLogin = (data: {
  session_id: string
  username: string
  password: string
  captcha: string
  uuid: string
}) => {
  return request.post<ApiResponse<CloudPortalLoginResult>>({
    url: '/api/cloud-portal/login',
    data,
    timeout: 30000
  })
}

export interface AutoLoginResult {
  user_info?: {
    id?: number
    username?: string
    real_name?: string
    [key: string]: unknown
  }
}

export interface AutoLoginResponse {
  session_id?: string
  img?: string
  uuid?: string
  need_captcha?: boolean
}

export const cloudPortalAutoLogin = (data: {
  username: string
  password: string
  session_id?: string
}) => {
  return request.post<ApiResponse<AutoLoginResult | AutoLoginResponse>>({
    url: '/api/cloud-portal/auto-login',
    data,
    timeout: 60000
  })
}

export const cloudPortalQuery = (data: {
  session_id: string
  query_params: Record<string, unknown>
}) => {
  return request.post<ApiResponse<Record<string, unknown>[]>>({
    url: '/api/cloud-portal/query',
    data,
    timeout: 60000
  })
}

export interface CloudPortalStatusResult {
  logged_in: boolean
  user_info?: {
    id?: number
    username?: string
    real_name?: string
    [key: string]: unknown
  }
  login_time?: number
  expires_at?: number
}

export const getCloudPortalStatus = (sessionId: string) => {
  return request.get<ApiResponse<CloudPortalStatusResult>>({
    url: '/api/cloud-portal/status',
    params: { session_id: sessionId }
  })
}

export const cloudPortalLogout = (sessionId: string) => {
  return request.post<ApiResponse<null>>({
    url: '/api/cloud-portal/logout',
    data: { session_id: sessionId }
  })
}

export const checkCloudPortalHealth = () => {
  return request.get<ApiResponse<{ status: string; service: string; version: string }>>({
    url: '/api/cloud-portal/health',
    timeout: 5000
  })
}

export interface AIAuditVehicleImage {
  picturePath: string
  bigPositivePic: string
  picTime: string
  stationId: string
  stationName: string
  vehPlate: string
  vehPlateColor: string
  stationType: string
  picId: string
}

export interface AIAuditGantryImage {
  picTime: string
  vehPlate: string
  stationName: string
  stationId: string
  picturePath: string
  bigPositivePic: string
  vehPlateColor: string
  picId: string
}

export interface AIAuditGantryTrade {
  fee: number
  transTime: string
  vehiclePlate: string
  passId: string
  gantryId: string
  gantryName: string
  axleCount: number
  feeVehicleTypeName: string
  vehiclePlateColor: string
  vehiclePlateColorName: string
  gantryOrderNumName: string
  enVehicleTypeName?: string
  mediaTypeName?: string
  tradeStatus?: string
  tradeStatusName?: string
  receivableFee?: number
  actualFee?: number
  specialType?: string
  specialTypeName?: string
}

export interface AIAuditGantryPlate {
  picTime: string
  gantryName: string
  vehiclePlate: string
  vehicleTypeName: string
  vehicleSpeed: number
  gantryId: string
  picId?: string
  gantryOrderNumName?: string
  cameraId?: string
}

export interface AIAuditExitTrade {
  plateNumber: string
  fee: number
  entime: string
  extime: string
  entollstationname: string
  extollstationname: string
  vehicleTypeName: string
  specialtype: string
  cardid: string
  mediano: string
  enVehicleTypeName?: string
  exVehicleTypeName?: string
  mediaTypeName?: string
  enVehiclePlate?: string
  exVehiclePlate?: string
  totalReceivableFee?: number
  totalTradeFee?: number
  totalDiscountFee?: number
  minFeeTradeAmount?: number
  totalMileage?: number
  minFeeMileage?: number
  feeCalcMethod?: string
  feeCalcMethodName?: string
  specialTypeName?: string
}

export interface AIAuditAuditOrder {
  order_id: string
  pass_id: string
  vehicle_no: string
  plate_number: string
  plate_color_name: string
  en_time: string
  ex_time: string
  en_station_name: string
  ex_station_name: string
  en_vehicle_type_name: string
  ex_vehicle_type_name: string
  fee: string
  label_code: string
  label_code_name: string
  loss_amount: string | null
  order_source: string
  order_status: number
  order_status_name: string
  toll_fee: string
  penalty_fee: string
  total_fee: string
  review_name: string
  review_time: string
  operate_time: string
  operator_name: string
}

export interface AIAuditSuspectedCar {
  rate: number
  vehiclePlate: string
  passId: string
  list: Array<{
    matchingId: string
    matchingVehiclePlate: string
    matchingGantryName: string
    matchingGantryId: string
    matchingTransTime: string
    matchingPassId: string
  }>
}

export interface AIAuditBatchQueryResult {
  time_range: {
    start_time: string
    end_time: string
  }
  vehicle_images: {
    success: boolean
    total: number
    images: AIAuditVehicleImage[]
    error?: string
  }
  gantry_trade: {
    success: boolean
    total: number
    records: AIAuditGantryTrade[]
    error?: string
  }
  gantry_plate: {
    success: boolean
    total: number
    records: AIAuditGantryPlate[]
    error?: string
  }
  exit_trade_etc: {
    success: boolean
    total: number
    records: AIAuditExitTrade[]
    error?: string
  }
  exit_trade_other: {
    success: boolean
    total: number
    records: AIAuditExitTrade[]
    error?: string
  }
  audit_order: {
    success: boolean
    total: number
    records: AIAuditAuditOrder[]
    error?: string
  }
  suspected_car: {
    success: boolean
    trade_list: AIAuditSuspectedCar[]
    error?: string
  }
  errors: string[]
}

export const aiAuditBatchQuery = (data: {
  session_id: string
  plate_number: string
  entry_time: string
  gate_time: string
  pass_id?: string
  hours?: number
  rows?: number
}) => {
  return request.post<ApiResponse<AIAuditBatchQueryResult>>({
    url: '/api/cloud-portal/ai-audit/batch-query',
    data,
    timeout: 180000
  })
}

export const aiAuditVehicleImages = (data: {
  session_id: string
  plate_number: string
  start_time: string
  end_time: string
  page?: number
  page_size?: number
  sort?: string
}) => {
  return request.post<ApiResponse<{ total: number; images: AIAuditVehicleImage[] }>>({
    url: '/api/cloud-portal/ai-audit/vehicle-images',
    data,
    timeout: 60000
  })
}

export const aiAuditGantryImages = (data: {
  session_id: string
  station_id: string
  start_time: string
  end_time: string
  rows?: number
  start?: number
  sort?: string
}) => {
  return request.post<ApiResponse<{ total: number; images: AIAuditGantryImage[] }>>({
    url: '/api/cloud-portal/ai-audit/gantry-images',
    data,
    timeout: 60000
  })
}

export const aiAuditGantryTrade = (data: {
  session_id: string
  query_value: string
  start_time: string
  end_time: string
}) => {
  return request.post<ApiResponse<{ total: number; records: AIAuditGantryTrade[] }>>({
    url: '/api/cloud-portal/ai-audit/gantry-trade',
    data,
    timeout: 60000
  })
}

export const aiAuditGantryPlate = (data: {
  session_id: string
  plate_number: string
  start_time: string
  end_time: string
}) => {
  return request.post<ApiResponse<{ total: number; records: AIAuditGantryPlate[] }>>({
    url: '/api/cloud-portal/ai-audit/gantry-plate',
    data,
    timeout: 60000
  })
}

export const aiAuditExitTrade = (data: {
  session_id: string
  query_value: string
  start_time: string
  end_time: string
  trade_type?: number
}) => {
  return request.post<ApiResponse<{ total: number; records: AIAuditExitTrade[] }>>({
    url: '/api/cloud-portal/ai-audit/exit-trade',
    data,
    timeout: 60000
  })
}

export const aiAuditSuspectedCar = (data: {
  session_id: string
  vehicle_or_pass_id: string
  start_time: string
  end_time: string
}) => {
  return request.post<ApiResponse<{ trade_list: AIAuditSuspectedCar[] }>>({
    url: '/api/cloud-portal/ai-audit/suspected-car',
    data,
    timeout: 60000
  })
}

export interface SelectedImage {
  base64: string
  station_name: string
  pic_time: string
}

export const aiAuditSelectImages = (data: {
  images: AIAuditVehicleImage[]
  gantry_ids: string[]
}) => {
  return request.post<ApiResponse<{ image1?: SelectedImage; image2?: SelectedImage }>>({
    url: '/api/cloud-portal/ai-audit/select-images',
    data
  })
}

export const aiAuditSaveImages = (data: {
  table_name: string
  record_id: string
  image1_base64?: string
  image2_base64?: string
  review_status?: string
  check_pass_id?: string
  special_situation?: string
  check_split?: string
  remark?: string
  clear_empty?: boolean
}) => {
  return request.post<ApiResponse<{ affected_rows: number }>>({
    url: '/api/cloud-portal/ai-audit/save-images',
    data
  })
}

export const aiAuditOriginalImage = (data: { session_id: string; picture_path: string }) => {
  return request.post<ApiResponse<{ image: string }>>({
    url: '/api/cloud-portal/ai-audit/original-image',
    data
  })
}

export const fetchPicture = (data: { session_id: string; picture_url: string }) => {
  return request.post<
    ApiResponse<{
      image?: string
      data_url?: string
      referer?: string
      response_status?: number
      response_content_type?: string
      response_content_length?: number
      response_headers?: Record<string, string>
      response_body?: string
    }>
  >({
    url: '/api/cloud-portal/fetch-picture',
    data
  })
}

export interface CloudPortalAccount {
  id: number
  user_id: number
  portal_username: string
  has_password: boolean
  created_at: string
  updated_at: string
}

export const getCloudPortalAccount = () => {
  return request.get<ApiResponse<CloudPortalAccount | null>>({
    url: '/api/cloud-portal-account/'
  })
}

export const saveCloudPortalAccount = (data: {
  portal_username: string
  portal_password: string
}) => {
  return request.post<ApiResponse<null>>({
    url: '/api/cloud-portal-account/',
    data
  })
}

export const deleteCloudPortalAccount = () => {
  return request.delete<ApiResponse<null>>({
    url: '/api/cloud-portal-account/'
  })
}

export const getCloudPortalCredentials = () => {
  return request.get<
    ApiResponse<{
      portal_username: string
      portal_password: string
      portal_session_id: string
    } | null>
  >({
    url: '/api/cloud-portal-account/credentials'
  })
}

export const updateCloudPortalSession = (sessionId: string) => {
  return request.post<ApiResponse<null>>({
    url: '/api/cloud-portal-account/session',
    data: { session_id: sessionId }
  })
}
