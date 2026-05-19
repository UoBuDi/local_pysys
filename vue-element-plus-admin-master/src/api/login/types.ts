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

export interface TokenData {
  token: string
  refreshToken: string
  tokenType: string
  expiresAt: number
  refreshExpiresAt: number
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface RefreshTokenResponse {
  token: string
  refreshToken: string
  tokenType: string
  expiresAt: number
  refreshExpiresAt: number
}

export interface ValidateTokenResponse {
  valid: boolean
  username?: string
  type?: string
  exp?: number
}
