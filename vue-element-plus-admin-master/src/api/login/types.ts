export interface UserLoginType {
  username: string
  password: string
}

export interface UserType {
  id?: number
  username: string
  password: string
  role: string
  roleId: string
  roleList?: string[]
}
