import request from '@/axios'

// 获取菜单列表
export const getMenuListApi = () => {
  return request.get({ url: '/api/menus/' })
}

// 保存菜单
export const saveMenuApi = (data: any) => {
  if (data.id) {
    return request.put({ url: `/api/menus/${data.id}`, data })
  } else {
    return request.post({ url: '/api/menus/', data })
  }
}

// 删除菜单
export const deleteMenuApi = (ids: string[] | number[]) => {
  const promises = ids.map((id) => request.delete({ url: `/api/menus/${id}` }))
  return Promise.all(promises)
}
