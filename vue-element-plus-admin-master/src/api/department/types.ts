export interface DepartmentItem {
  id: string
  departmentName: string
  name: string
  status: number
  created_at: string
  children?: DepartmentItem[]
}

export interface DepartmentListResponse {
  list: DepartmentItem[]
}

export interface DepartmentUserParams {
  pageSize: number
  pageIndex: number
  id?: string
  department_id?: string
  username?: string
  account?: string
}

export interface DepartmentUserItem {
  id: string
  username: string
  account: string
  email: string
  createTime: string
  role: string
  department: DepartmentItem
  department_id?: number | string
  status: number
  created_at: string
}

export interface DepartmentUserResponse {
  list: DepartmentUserItem[]
  total: number
}
