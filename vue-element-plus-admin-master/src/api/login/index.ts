import request from '@/axios'
import type { UserType, RefreshTokenResponse, ValidateTokenResponse } from './types'

interface RoleParams {
  roleName: string
}

interface LoginCredentials {
  username: string
  password: string
}

interface LoginResponse {
  message: string
  token?: string
  refreshToken?: string
  tokenType?: string
  expiresAt?: number
  refreshExpiresAt?: number
  user?: {
    id: number
    username: string
    roles?: any[]
    roleList?: string[]
    avatar?: string
    nickname?: string
    email?: string
  }
}

export const loginApi = (data: LoginCredentials): Promise<IResponse<LoginResponse>> => {
  return request.post({ url: '/api/login/', data })
}

export const registerApi = (data: LoginCredentials): Promise<IResponse<LoginResponse>> => {
  return request.post({ url: '/api/register/', data })
}

export const loginOutApi = (): Promise<IResponse> => {
  return request.get({ url: '/api/user/loginOut' })
}

export const refreshTokenApi = (refreshToken: string): Promise<IResponse<RefreshTokenResponse>> => {
  return request.post({ url: '/api/token/refresh', data: { refresh_token: refreshToken } })
}

export const validateTokenApi = (token: string): Promise<IResponse<ValidateTokenResponse>> => {
  return request.post({ url: '/api/token/validate', data: { refresh_token: token } })
}

export const getUserListApi = ({ params }: AxiosConfig) => {
  return request.get<{
    code: string
    data: {
      list: UserType[]
      total: number
    }
  }>({ url: '/api/user/list', params })
}

export const getAdminRoleApi = (
  params: RoleParams
): Promise<IResponse<AppCustomRouteRecordRaw[]>> => {
  return request.get({ url: '/api/role/list', params })
}

export const getTestRoleApi = (params: RoleParams): Promise<IResponse<string[]>> => {
  return request.get({ url: '/api/role/list2', params })
}

export const getUserMenusApi = (): Promise<IResponse<AppCustomRouteRecordRaw[]>> => {
  return request.get({ url: '/api/user/menus' })
}

export const getUserPermissionsApi = (): Promise<IResponse<string[]>> => {
  return request.get({ url: '/api/user/permissions' })
}
