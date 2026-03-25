import { defineStore } from 'pinia'
import { store } from '../index'
import { UserLoginType, UserType } from '@/api/login/types'
import { ElMessageBox } from 'element-plus'
import { useI18n } from '@/hooks/web/useI18n'
import { loginOutApi } from '@/api/login'
import { useTagsViewStore } from './tagsView'
import { usePermissionStore } from './permission'
import router from '@/router'
import { clearRouteCache } from '@/permission'

interface UserState {
  userInfo?: UserType
  tokenKey: string
  token: string
  refreshToken: string
  tokenExpiresAt: number
  refreshExpiresAt: number
  roleRouters?: string[] | AppCustomRouteRecordRaw[]
  permissions?: string[]
  rememberMe: boolean
  loginInfo?: UserLoginType
}

export const useUserStore = defineStore('user', {
  state: (): UserState => {
    return {
      userInfo: undefined,
      tokenKey: 'Authorization',
      token: '',
      refreshToken: '',
      tokenExpiresAt: 0,
      refreshExpiresAt: 0,
      roleRouters: undefined,
      rememberMe: true,
      loginInfo: undefined
    }
  },
  getters: {
    getTokenKey(): string {
      return this.tokenKey
    },
    getToken(): string {
      return this.token
    },
    getRefreshToken(): string {
      return this.refreshToken
    },
    getTokenExpiresAt(): number {
      return this.tokenExpiresAt
    },
    getRefreshExpiresAt(): number {
      return this.refreshExpiresAt
    },
    getUserInfo(): UserType | undefined {
      return this.userInfo
    },
    getRoleRouters(): string[] | AppCustomRouteRecordRaw[] | undefined {
      return this.roleRouters
    },
    getPermissions(): string[] | undefined {
      return this.permissions
    },
    getRememberMe(): boolean {
      return this.rememberMe
    },
    getLoginInfo(): UserLoginType | undefined {
      return this.loginInfo
    }
  },
  actions: {
    setTokenKey(tokenKey: string) {
      this.tokenKey = tokenKey
    },
    setToken(token: string) {
      this.token = token
    },
    setRefreshToken(refreshToken: string) {
      this.refreshToken = refreshToken
    },
    setTokenExpiresAt(expiresAt: number) {
      this.tokenExpiresAt = expiresAt
    },
    setRefreshExpiresAt(expiresAt: number) {
      this.refreshExpiresAt = expiresAt
    },
    setTokenData(data: { token: string; refreshToken: string; expiresAt: number; refreshExpiresAt: number }) {
      this.token = data.token
      this.refreshToken = data.refreshToken
      this.tokenExpiresAt = data.expiresAt
      this.refreshExpiresAt = data.refreshExpiresAt
    },
    setUserInfo(userInfo?: UserType) {
      this.userInfo = userInfo
    },
    setRoleRouters(roleRouters: string[] | AppCustomRouteRecordRaw[]) {
      this.roleRouters = roleRouters
    },
    setPermissions(permissions?: string[]) {
      this.permissions = permissions
    },
    logoutConfirm() {
      const { t } = useI18n()
      ElMessageBox.confirm(t('common.loginOutMessage'), t('common.reminder'), {
        confirmButtonText: t('common.ok'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      })
        .then(async () => {
          const res = await loginOutApi().catch(() => {})
          if (res) {
            this.reset()
          }
        })
        .catch(() => {})
    },
    reset() {
      const tagsViewStore = useTagsViewStore()
      const permissionStore = usePermissionStore()
      tagsViewStore.delAllViews()
      this.setToken('')
      this.setRefreshToken('')
      this.setTokenExpiresAt(0)
      this.setRefreshExpiresAt(0)
      this.setUserInfo(undefined)
      this.setRoleRouters([])
      permissionStore.reset()
      clearRouteCache()
      router.replace('/login')
    },
    logout() {
      this.reset()
    },
    setRememberMe(rememberMe: boolean) {
      this.rememberMe = rememberMe
    },
    setLoginInfo(loginInfo: UserLoginType | undefined) {
      this.loginInfo = loginInfo
    }
  },
  persist: [
    {
      pick: ['token', 'refreshToken', 'tokenExpiresAt', 'refreshExpiresAt', 'userInfo', 'permissions', 'rememberMe', 'loginInfo'],
      storage: localStorage
    }
  ]
})

export const useUserStoreWithOut = () => {
  return useUserStore(store)
}
