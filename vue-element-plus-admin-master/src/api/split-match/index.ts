import request from '@/axios'

export const getCloudPortalAccessToken = (userId?: number): string => {
  try {
    const key = userId ? `cloud_portal_access_token_${userId}` : 'cloud_portal_access_token'
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

export const setCloudPortalAccessToken = (token: string, userId?: number) => {
  try {
    const key = userId ? `cloud_portal_access_token_${userId}` : 'cloud_portal_access_token'
    if (token) {
      localStorage.setItem(key, token)
    } else {
      localStorage.removeItem(key)
    }
  } catch {
    // ignore
  }
}

export const removeCloudPortalAccessToken = (userId?: number) => {
  try {
    const key = userId ? `cloud_portal_access_token_${userId}` : 'cloud_portal_access_token'
    localStorage.removeItem(key)
  } catch {
    // ignore
  }
}

const appendUserId = (baseUrl: string, userId?: number): string => {
  if (!userId) return baseUrl
  const separator = baseUrl.includes('?') ? '&' : '?'
  return `${baseUrl}${separator}user_id=${userId}`
}

const injectAccessToken = (data: Record<string, any>, userId?: number): Record<string, any> => {
  const token = getCloudPortalAccessToken(userId)
  if (token && !data.access_token) {
    return { ...data, access_token: token }
  }
  return data
}

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

export const getSplitMatchTables = () => {
  return request.get<string[]>({ url: '/api/split-match/tables/' })
}

export const getSplitMatchData = (params: {
  table_name?: string
  filters?: string
  page?: number
  page_size?: number
}) => {
  return request.get<SplitMatchData>({ url: '/api/split-match/data/', params })
}

export const executeSplitMatch = (data: SplitMatchTable) => {
  return request.post<MatchResult>({
    url: '/api/split-match/execute/',
    data: data,
    timeout: 300000
  })
}

export const previewSplitMatch = (data: SplitMatchTable) => {
  return request.post<{
    sqls: Array<{
      name: string
      sql: string
      batch_count?: number
      total_count?: number
    }>
    total_records?: number
    error?: string
  }>({
    url: '/api/split-match/preview/',
    data: data
  })
}

export const getCfTables = () => {
  return request.get<string[]>({ url: '/api/split-match/cf-tables/' })
}

export const updateSplitMatchData = (data: {
  table_name?: string
  row_id: string
  data: Record<string, unknown>
  version?: number
  force_overwrite?: boolean
}) => {
  return request.post<{ affectedRows: number; version?: number }>({
    url: '/api/split-match/update/',
    data: data
  })
}

export interface ExportSplitMatchData {
  tableName: string
  columns: string[]
  column_types: Record<string, string>
  data: Record<string, unknown>[]
  rows: Record<string, unknown>[]
  count: number
}

export const getExportSplitMatchData = (params: { table_name?: string; filters?: string }) => {
  return request.get<ExportSplitMatchData>({
    url: '/api/split-match/export/',
    params: { ...params, format: 'json' }
  })
}

export const getOriginalImage = (params: {
  table_name: string
  pass_id: string
  field: string
}) => {
  return request.get<string>({
    url: '/api/split-match/original-image/',
    params
  })
}

export interface TableImagesResult {
  [passId: string]: {
    [field: string]: string | null
  }
}

export const getTableImages = (params: {
  table_name: string
  pass_ids: string
  fields?: string
}) => {
  return request.get<TableImagesResult>({
    url: '/api/split-match/images/',
    params
  })
}

export interface SplitStatisticsData {
  split_count: number
  total_split_amount: number
}

export const getSplitStatistics = (data: { table_name: string }) => {
  return request.post<SplitStatisticsData>({
    url: '/api/split-match/split-statistics/',
    data
  })
}

export interface VerifyPassIdResult {
  exists: boolean
  match_count: number
  records: Array<Record<string, unknown>>
  query_time: number
}

export const verifyPassId = (params: {
  pass_id: string
  pass_id_secondary?: string
  verify_type: string
  user_id?: number
  username?: string
}) => {
  return request.get<VerifyPassIdResult>({
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
  return request.get<{
    list: VerifyHistoryRecord[]
    total: number
    page: number
    page_size: number
  }>({
    url: '/api/split-match/verify-history/',
    params
  })
}

export interface CloudPortalCaptchaResult {
  img: string
  uuid: string
}

export const getCloudPortalCaptcha = () => {
  return request.get<CloudPortalCaptchaResult>({
    url: '/api/cloud-portal/captcha',
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
  uuid: string
  username: string
  password: string
  captcha: string
}) => {
  return request.post<CloudPortalLoginResult>({
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
  img?: string
  uuid?: string
  need_captcha?: boolean
}

export const cloudPortalAutoLogin = (
  data: {
    username: string
    password: string
  },
  userId?: number
) => {
  return request.post<AutoLoginResult | AutoLoginResponse>({
    url: appendUserId('/api/cloud-portal/auto-login', userId),
    data,
    timeout: 60000
  })
}

export const cloudPortalQuery = (
  data: {
    query_params: Record<string, unknown>
  },
  userId?: number
) => {
  return request.post<Record<string, unknown>[]>({
    url: appendUserId('/api/cloud-portal/query', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const cloudPortalLogout = (userId?: number) => {
  return request.post<null>({
    url: appendUserId('/api/cloud-portal/logout', userId),
    data: {}
  })
}

export const keepCloudPortalAlive = (userId?: number) => {
  return request.post<null>({
    url: appendUserId('/api/cloud-portal/keep-alive', userId),
    data: {}
  })
}

export const checkCloudPortalHealth = () => {
  return request.get<{ status: string; service: string; version: string }>({
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

export const aiAuditBatchQuery = (
  data: {
    plate_number: string
    entry_time: string
    gate_time: string
    pass_id?: string
    hours?: number
    rows?: number
  },
  userId?: number
) => {
  return request.post<AIAuditBatchQueryResult>({
    url: appendUserId('/api/cloud-portal/ai-audit/batch-query', userId),
    data: injectAccessToken(data),
    timeout: 180000
  })
}

export interface OrderDetailLabelCode {
  labelCode: string
  labelName: string
  auditInfo: string | null
  auditMethod: string
}

export interface OrderDetailPicture {
  picturePath: string
  smallPositivePic: string
  bigPositivePic: string
  smallBackPic: string
  bigBackPic: string
  bigPic: string | null
  smallPic: string | null
  venderName: string | null
  vehType: string | null
  venderId: string | null
  plateImage: string | null
  plateImageWidth: number | null
  plateImageHeight: number | null
  sideImage: string | null
  sideImagePath: string | null
  sideImageWidth: number | null
  sideImageHeight: number | null
  headImage: string | null
  headImageHeight: number | null
  headImageWidth: number | null
  headImagePath: string | null
  tailImagePath: string | null
  tailImage: string | null
  tailImageWidth: number | null
  tailImageHeight: number | null
  source: string | null
  picTime: string
  stationType: string
  vehPlate: string
  picId: string
  vehPlateColor: string
  shootPosition: string
  stationId: string
  stationName: string
  reid_hw: string
  reid_sm: string
  tw_reid: string
  gantryId: string | null
}

export interface OrderDetailLabelVo {
  vehicle_no?: string
  en_station_name?: string
  en_time?: string
  ex_station_name?: string
  ex_time?: string
  audit_remark?: string
}

export interface OrderDetailData {
  pay_amount?: number
  labelVo?: OrderDetailLabelVo
  labelCodeList?: OrderDetailLabelCode[]
  historyData?: any[]
  auditCheckdescConfigs?: any[]
  picBeanVo?: {
    total: string
    picBeanList: OrderDetailPicture[]
  }
}

export const aiAuditOrderDetail = (
  params: {
    order_id: string
  },
  userId?: number
) => {
  const token = getCloudPortalAccessToken()
  const queryParams: Record<string, any> = token
    ? { ...params, access_token: token }
    : { ...params }
  if (userId) queryParams.user_id = userId
  return request.get<OrderDetailData>({
    url: '/api/cloud-portal/ai-audit/order-detail',
    params: queryParams,
    timeout: 30000
  })
}

export const aiAuditVehicleImages = (
  data: {
    plate_number: string
    start_time: string
    end_time: string
    page?: number
    page_size?: number
    sort?: string
  },
  userId?: number
) => {
  return request.post<{ success: boolean; total: number; images: AIAuditVehicleImage[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/vehicle-images', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const aiAuditGantryImages = (
  data: {
    station_id: string
    start_time: string
    end_time: string
    rows?: number
    start?: number
    sort?: string
  },
  userId?: number
) => {
  return request.post<{ success: boolean; total: number; images: AIAuditGantryImage[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/gantry-images', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const aiAuditGantryTrade = (
  data: {
    query_value: string
    start_time: string
    end_time: string
  },
  userId?: number
) => {
  return request.post<{ total: number; records: AIAuditGantryTrade[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/gantry-trade', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const aiAuditGantryPlate = (
  data: {
    plate_number: string
    start_time: string
    end_time: string
  },
  userId?: number
) => {
  return request.post<{ total: number; records: AIAuditGantryPlate[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/gantry-plate', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const aiAuditExitTrade = (
  data: {
    query_value: string
    start_time: string
    end_time: string
    trade_type?: number
  },
  userId?: number
) => {
  return request.post<{ total: number; records: AIAuditExitTrade[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/exit-trade', userId),
    data: injectAccessToken(data),
    timeout: 60000
  })
}

export const aiAuditSuspectedCar = (
  data: {
    vehicle_or_pass_id: string
    start_time: string
    end_time: string
  },
  userId?: number
) => {
  return request.post<{ trade_list: AIAuditSuspectedCar[] }>({
    url: appendUserId('/api/cloud-portal/ai-audit/suspected-car', userId),
    data: injectAccessToken(data),
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
  return request.post<{ image1?: SelectedImage; image2?: SelectedImage }>({
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
  return request.post<{ affected_rows: number }>({
    url: '/api/cloud-portal/ai-audit/save-images',
    data
  })
}

export const aiAuditOriginalImage = (data: { picture_path: string }, userId?: number) => {
  return request.post<{ image: string }>({
    url: appendUserId('/api/cloud-portal/ai-audit/original-image', userId),
    data: injectAccessToken(data)
  })
}

export const fetchPicture = (data: { picture_url: string }, userId?: number) => {
  return request.post<{
    image?: string
    data_url?: string
    referer?: string
    response_status?: number
    response_content_type?: string
    response_content_length?: number
    response_headers?: Record<string, string>
    response_body?: string
  }>({
    url: appendUserId('/api/cloud-portal/fetch-picture', userId),
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

export const getCloudPortalAccount = (userId?: number) => {
  const params: Record<string, any> = {}
  if (userId) params.user_id = userId
  return request.get<CloudPortalAccount | null>({
    url: '/api/cloud-portal-account/',
    params
  })
}

export const saveCloudPortalAccount = (
  data: {
    portal_username: string
    portal_password: string
  },
  userId?: number
) => {
  return request.post<null>({
    url: appendUserId('/api/cloud-portal-account/', userId),
    data
  })
}

export const deleteCloudPortalAccount = (userId?: number) => {
  return request.delete<null>({
    url: appendUserId('/api/cloud-portal-account/', userId)
  })
}

export const getCloudPortalCredentials = (userId?: number) => {
  const params: Record<string, any> = {}
  if (userId) params.user_id = userId
  return request.get<{
    portal_username: string
    portal_password: string
    access_token?: string
    refresh_token?: string
    redirect_uri?: string
    token_expires_at?: number
    is_valid?: boolean
  } | null>({
    url: '/api/cloud-portal-account/credentials',
    params
  })
}

// ==================== 协作功能 API ====================

export interface LockResult {
  locked: boolean
  own_lock: boolean
  locked_by?: string
  user_id?: number
}

export const lockRow = (data: { table_name: string; row_id: string }) => {
  return request.post<LockResult>({
    url: '/api/split-match/lock/',
    data
  })
}

export const unlockRow = (data: { table_name: string; row_id: string }) => {
  return request.post<{ released: boolean }>({
    url: '/api/split-match/unlock/',
    data
  })
}

export interface ActiveLock {
  row_id: string
  user_id: number
  username: string
  expires_at: string
}

export const getActiveLocks = (tableName: string) => {
  return request.get<ActiveLock[]>({
    url: '/api/split-match/active-locks/',
    params: { table_name: tableName }
  })
}

export interface RowVersion {
  version: number
  updated_by: string | null
  updated_at: string | null
}

export const getRowVersion = (tableName: string, rowId: string) => {
  return request.get<RowVersion>({
    url: '/api/split-match/row-version/',
    params: { table_name: tableName, row_id: rowId }
  })
}

export const getSingleRow = (tableName: string, rowId: string) => {
  return request.get<Record<string, unknown>>({
    url: '/api/split-match/single-row/',
    params: { table_name: tableName, row_id: rowId }
  })
}
