/**
 * 请求成功状态码
 */
export const SUCCESS_CODE = 200

/**
 * 请求contentType
 */
export const CONTENT_TYPE: AxiosContentType = 'application/json'

/**
 * 请求超时时间
 */
export const REQUEST_TIMEOUT = 60000
/**
 * 详单查询请求超时时间
 */
export const DETAIL_QUERY_TIMEOUT = 300000

/**
 * 不重定向白名单
 */
export const NO_REDIRECT_WHITE_LIST = ['/login']

/**
 * 不重置路由白名单
 */
export const NO_RESET_WHITE_LIST = ['Redirect', 'RedirectWrap', 'Login', 'NoFind', 'Root']

/**
 * 表格默认过滤列设置字段
 */
export const DEFAULT_FILTER_COLUMN = ['expand', 'selection']

/**
 * 是否为mock模式
 */
export const IS_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

/**
 * 是否转换请求参数中的undefined为null
 */
export const TRANSFORM_REQUEST_DATA = true

/**
 * 全局图标前缀
 */
export const ICON_PREFIX = 'vi-'
