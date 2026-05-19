import request from '@/axios'

// 为用户分配角色
export const assignUserRolesApi = (data: { user_id: number; role_ids: number[] }) => {
  return request.post({ url: '/api/user-roles/', data })
}

// 获取用户已分配的角色
export const getUserRolesApi = (userId: number) => {
  return request.get({ url: `/api/users/${userId}/roles` })
}
