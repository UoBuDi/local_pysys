import request from '@/axios'
import { DepartmentListResponse, DepartmentUserParams, DepartmentUserResponse } from './types'

// 获取部门列表
export const getDepartmentApi = () => {
  return request.get<DepartmentListResponse>({ url: '/api/departments/' })
}

// 获取部门下的用户列表
export const getUserByIdApi = (params: DepartmentUserParams) => {
  return request.get<DepartmentUserResponse>({ url: '/api/users/', params })
}

// 删除用户
export const deleteUserByIdApi = (ids: string[] | number[]) => {
  // 注意：这里需要特殊处理，因为后端是RESTful API
  // 实际项目中应该逐个删除或者后端提供批量删除接口
  const promises = ids.map((id) => request.delete({ url: `/api/users/${id}` }))
  return Promise.all(promises)
}

// 保存用户
export const saveUserApi = (data: any) => {
  if (data.id) {
    return request.put({ url: `/api/users/${data.id}`, data })
  } else {
    return request.post({ url: '/api/users/', data })
  }
}

// 保存部门
export const saveDepartmentApi = (data: any) => {
  if (data.id) {
    return request.put({ url: `/api/departments/${data.id}`, data })
  } else {
    return request.post({ url: '/api/departments/', data })
  }
}

// 删除部门
export const deleteDepartmentApi = (ids: string[] | number[]) => {
  // 注意：这里需要特殊处理，因为后端是RESTful API
  // 实际项目中应该逐个删除或者后端提供批量删除接口
  const promises = ids.map((id) => request.delete({ url: `/api/departments/${id}` }))
  return Promise.all(promises)
}

// 获取部门表格数据
export const getDepartmentTableApi = (params: any) => {
  return request.get({ url: '/api/departments/', params })
}
