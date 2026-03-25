import request from '@/axios'

// 获取角色列表
export const getRoleListApi = () => {
  return request.get({ url: '/api/roles/' })
}

// 保存角色
export const saveRoleApi = (data: any) => {
  if (data.id) {
    return request.put({ url: `/api/roles/${data.id}`, data })
  } else {
    return request.post({ url: '/api/roles/', data })
  }
}

// 删除角色
export const deleteRoleApi = (ids: string[] | number[]) => {
  const promises = ids.map((id) => request.delete({ url: `/api/roles/${id}` }))
  return Promise.all(promises)
}

// 为角色分配菜单
export const assignRoleMenusApi = (data: { role_id: number; menu_ids: number[] }) => {
  return request.post({ url: '/api/role-menus/', data })
}

// 获取角色已分配的菜单
export const getRoleMenusApi = (roleId: number) => {
  return request.get({ url: `/api/roles/${roleId}/menus` })
}

// 获取权限点列表
export const getPermissionListApi = () => {
  return request.get({ url: '/api/permissions/' })
}

// 为角色分配权限
export const assignRolePermissionsApi = (data: { role_id: number; permission_ids: number[] }) => {
  return request.post({ url: '/api/role-permissions/', data })
}

// 获取角色已分配的权限
export const getRolePermissionsApi = (roleId: number) => {
  return request.get({ url: `/api/roles/${roleId}/permissions` })
}
