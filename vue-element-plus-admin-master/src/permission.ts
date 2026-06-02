import router from './router'
import { useAppStoreWithOut } from '@/store/modules/app'
import type { RouteLocationNormalized, RouteRecordRaw } from 'vue-router'
import { useTitle } from '@/hooks/web/useTitle'
import { useNProgress } from '@/hooks/web/useNProgress'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { usePageLoading } from '@/hooks/web/usePageLoading'
import { PUBLIC_ROUTES, DASHBOARD_ROUTES, MAX_DYNAMIC_ROUTES } from '@/constants'
import { useUserStoreWithOut } from '@/store/modules/user'
import { ElMessage } from 'element-plus'
import { checkAndRefreshToken } from '@/utils/auth'

const { start, done } = useNProgress()

const { loadStart, loadDone } = usePageLoading()

enum PermissionErrorType {
  API_ERROR = 'API_ERROR',
  ROUTE_ERROR = 'ROUTE_ERROR',
  AUTH_ERROR = 'AUTH_ERROR',
  NETWORK_ERROR = 'NETWORK_ERROR'
}

interface RouteCacheEntry {
  cached: boolean
  timestamp: number
}

const ROUTE_CACHE_TTL = 5 * 60 * 1000
const MAX_ROUTE_CACHE_SIZE = 50

const routeCache = new Map<string, RouteCacheEntry>()

function isRouteCacheExpired(entry: RouteCacheEntry): boolean {
  return Date.now() - entry.timestamp > ROUTE_CACHE_TTL
}

function cleanupExpiredRouteCache(): void {
  const now = Date.now()
  for (const [path, entry] of routeCache.entries()) {
    if (now - entry.timestamp > ROUTE_CACHE_TTL) {
      routeCache.delete(path)
    }
  }
}

function enforceRouteCacheSizeLimit(): void {
  if (routeCache.size <= MAX_ROUTE_CACHE_SIZE) {
    return
  }
  const entries = Array.from(routeCache.entries())
  entries.sort((a, b) => a[1].timestamp - b[1].timestamp)
  const toRemove = entries.slice(0, entries.length - MAX_ROUTE_CACHE_SIZE)
  for (const [path] of toRemove) {
    routeCache.delete(path)
  }
}

function handlePermissionError(error: any, type: PermissionErrorType): void {
  console.error(`[${type}]`, error)

  switch (type) {
    case PermissionErrorType.API_ERROR:
      ElMessage.error('获取权限信息失败，请稍后重试')
      break
    case PermissionErrorType.ROUTE_ERROR:
      ElMessage.error('路由加载失败，请刷新页面')
      break
    case PermissionErrorType.AUTH_ERROR:
      ElMessage.error('登录已过期，请重新登录')
      break
    case PermissionErrorType.NETWORK_ERROR:
      ElMessage.error('网络连接失败，请检查网络')
      break
  }
}

function checkRouteExists(path: string): boolean {
  const routes = router.getRoutes()
  return routes.some((route) => route.path === path || route.redirect === path)
}

function handleRouteNotFound(
  targetPath: string,
  fallbackPath: string = '/dashboard/analysis'
): string {
  if (checkRouteExists(targetPath)) {
    return targetPath
  }
  if (checkRouteExists(fallbackPath)) {
    console.warn(`目标路由不存在: ${targetPath}, 重定向到: ${fallbackPath}`)
    return fallbackPath
  }
  console.warn(`目标路由和兜底路由均不存在: ${targetPath}, ${fallbackPath}, 重定向到: /login`)
  return '/login'
}

function validateRouteCount(routes: any[]): boolean {
  if (routes.length > MAX_DYNAMIC_ROUTES) {
    console.warn(`动态路由数量超过限制: ${routes.length}/${MAX_DYNAMIC_ROUTES}`)
    return false
  }
  return true
}

function checkFineGrainedPermission(
  route: RouteLocationNormalized,
  permissions: string[]
): boolean {
  const requiredPermissions = route.meta?.permissions as string[]

  if (!requiredPermissions || requiredPermissions.length === 0) {
    return true
  }

  return requiredPermissions.some((perm) => permissions.includes(perm))
}

function sendRouteAnalytics(logData: any): void {
  try {
    const url = '/api/analytics/route'
    const userStoreData = localStorage.getItem('user')
    let authHeader = ''
    if (userStoreData) {
      try {
        const parsed = JSON.parse(userStoreData)
        authHeader = parsed?.token || ''
      } catch {
        authHeader = ''
      }
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json'
    }
    if (authHeader) {
      headers['Authorization'] = `Bearer ${authHeader}`
    }

    fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(logData),
      keepalive: true
    }).catch(() => {})
  } catch (error) {
    // 静默处理，路由分析不影响主流程
  }
}

async function fetchAndSetUserMenusAndPermissions(
  userStore: ReturnType<typeof useUserStoreWithOut>
): Promise<any[]> {
  const { getUserMenusApi, getUserPermissionsApi } = await import('@/api/login')

  const menusRes = await getUserMenusApi()
  const roleRouters = menusRes.data || []

  if (!validateRouteCount(roleRouters)) {
    throw new Error('动态路由数量超过限制')
  }

  userStore.setRoleRouters(roleRouters)
  console.log('获取菜单数据成功:', roleRouters.length, '个菜单项')

  const permissionsRes = await getUserPermissionsApi()
  const permissions = permissionsRes.data || []
  userStore.setPermissions(permissions)
  console.log('获取权限数据成功:', permissions.length, '个权限点')

  return roleRouters
}

async function generateAndAddRoutes(
  appStore: ReturnType<typeof useAppStoreWithOut>,
  permissionStore: ReturnType<typeof usePermissionStoreWithOut>,
  roleRouters: any[]
): Promise<void> {
  if (appStore.getDynamicRouter) {
    try {
      appStore.serverDynamicRouter
        ? await permissionStore.generateRoutes('server', roleRouters as AppCustomRouteRecordRaw[])
        : await permissionStore.generateRoutes('frontEnd', roleRouters as string[])

      if (permissionStore.getRouters.length === 0) {
        console.warn('Server routes loading failed, falling back to static routes')
        await permissionStore.generateRoutes('static')
      }
    } catch (error) {
      handlePermissionError(error, PermissionErrorType.ROUTE_ERROR)
      await permissionStore.generateRoutes('static')
    }
  } else {
    await permissionStore.generateRoutes('static')
  }

  permissionStore.getAddRouters.forEach((route) => {
    router.addRoute(route as unknown as RouteRecordRaw)
  })
}

function performFinalNavigation(
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  permissionStore: ReturnType<typeof usePermissionStoreWithOut>,
  next: (to?: any) => void
): void {
  if (permissionStore.getAddRouters.length === 0) {
    permissionStore.setIsAddRouters(true)
    next({ path: '/403', replace: true })
    return
  }
  const redirectPath = from.query.redirect || to.path
  const redirect = decodeURIComponent(redirectPath as string)
  const finalPath = handleRouteNotFound(redirect)
  const nextData = to.path === finalPath ? { ...to, replace: true } : { path: finalPath }
  permissionStore.setIsAddRouters(true)
  next(nextData)
}

function clearRouteCache(): void {
  routeCache.clear()
}

const RouteGuardUtils = {
  isPublicRoute(path: string): boolean {
    return PUBLIC_ROUTES.some((route) => path.startsWith(route))
  },

  isDashboardRoute(path: string): boolean {
    return DASHBOARD_ROUTES.some((route) => path.startsWith(route))
  },

  hasPermission(roleList: string[]): boolean {
    return roleList.length > 0
  },

  hasMenus(roleRouters: any[]): boolean {
    return roleRouters && roleRouters.length > 0
  },

  isUserInfoValid(userInfo: any): boolean {
    return userInfo && Array.isArray(userInfo?.roleList)
  },

  isRouteCached(path: string): boolean {
    const entry = routeCache.get(path)
    if (!entry) {
      return false
    }
    if (isRouteCacheExpired(entry)) {
      routeCache.delete(path)
      return false
    }
    return entry.cached
  },

  cacheRoute(path: string): void {
    cleanupExpiredRouteCache()
    enforceRouteCacheSizeLimit()
    routeCache.set(path, {
      cached: true,
      timestamp: Date.now()
    })
  },

  clearRouteCache
}

router.beforeEach(async (to, from, next) => {
  const startTime = Date.now()

  to.meta.navigationStartTime = startTime

  start()
  loadStart()

  const permissionStore = usePermissionStoreWithOut()
  const appStore = useAppStoreWithOut()
  const userStore = useUserStoreWithOut()

  try {
    if (to.path === '/login') {
      if (userStore.getUserInfo) {
        next({ path: '/' })
      } else {
        next()
      }
      return
    }

    if (RouteGuardUtils.isPublicRoute(to.path)) {
      next()
      return
    }

    const userInfo = userStore.getUserInfo

    if (!userInfo) {
      console.warn('用户未登录，重定向到登录页')
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }

    const tokenResult = await checkAndRefreshToken()
    if (tokenResult.shouldLogout) {
      console.warn('Token无效且刷新失败，重定向到登录页')
      userStore.logout()
      next({ path: '/login', query: { redirect: to.fullPath } })
      return
    }

    if (tokenResult.refreshed) {
      console.log('Token已静默刷新')
    }

    const roleList = userInfo?.roleList || []
    let roleRouters = userStore.getRoleRouters || []
    const hasPermissionAndMenus =
      RouteGuardUtils.hasPermission(roleList) && RouteGuardUtils.hasMenus(roleRouters)

    if (permissionStore.getIsAddRouters) {
      if (hasPermissionAndMenus) {
        const permissions = userStore.getPermissions || []
        if (!checkFineGrainedPermission(to, permissions)) {
          console.warn(`用户没有访问路由 ${to.path} 的细粒度权限`)
          ElMessage.warning('您没有访问该页面的权限')
          next({ path: '/403' })
          return
        }
      }
      if (!RouteGuardUtils.isRouteCached(to.path)) {
        RouteGuardUtils.cacheRoute(to.path)
      }
      next()
      return
    }

    if (appStore.getDynamicRouter && appStore.getServerDynamicRouter) {
      try {
        roleRouters = await fetchAndSetUserMenusAndPermissions(userStore)
      } catch (error) {
        handlePermissionError(error, PermissionErrorType.API_ERROR)
        await permissionStore.generateRoutes('static')
      }
    }

    await generateAndAddRoutes(appStore, permissionStore, roleRouters)
    performFinalNavigation(to, from, permissionStore, next)
  } catch (error) {
    handlePermissionError(error, PermissionErrorType.NETWORK_ERROR)
    next({ path: handleRouteNotFound('/dashboard/analysis'), replace: true })
  }
})

router.afterEach((to, from) => {
  const duration = Date.now() - ((from.meta?.navigationStartTime as number) || Date.now())

  useTitle(to?.meta?.title as string)
  done()
  loadDone()

  const logData = {
    timestamp: Date.now(),
    from: from.path,
    to: to.path,
    duration,
    userAgent: navigator.userAgent
  }

  console.log('[Route Navigation]', logData)
  sendRouteAnalytics(logData)
})

export { clearRouteCache, RouteGuardUtils }
