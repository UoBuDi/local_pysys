import request from '@/axios'
import type { UserType } from './types'

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
  user?: {
    id: number
    username: string
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
