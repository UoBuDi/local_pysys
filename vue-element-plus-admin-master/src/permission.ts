import router from './router'
import { useAppStoreWithOut } from '@/store/modules/app'
import type { RouteRecordRaw } from 'vue-router'
import { useTitle } from '@/hooks/web/useTitle'
import { useNProgress } from '@/hooks/web/useNProgress'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { usePageLoading } from '@/hooks/web/usePageLoading'
import { NO_REDIRECT_WHITE_LIST } from '@/constants'
import { useUserStoreWithOut } from '@/store/modules/user'

const { start, done } = useNProgress()

const { loadStart, loadDone } = usePageLoading()

router.beforeEach(async (to, from, next) => {
  start()
  loadStart()
  const permissionStore = usePermissionStoreWithOut()
  const appStore = useAppStoreWithOut()
  const userStore = useUserStoreWithOut()

  // 取消权限验证，所有用户都可以访问所有路由
  if (to.path === '/login') {
    if (userStore.getUserInfo) {
      next({ path: '/' })
    } else {
      next()
    }
    return
  }

  // 检查路由是否已加载
  if (permissionStore.getIsAddRouters) {
    next()
    return
  }

  // 获取菜单路由数据
  let roleRouters = userStore.getRoleRouters || []

  // 如果菜单数据为空，尝试从后端获取
  if (appStore.getDynamicRouter && appStore.getServerDynamicRouter && roleRouters.length === 0) {
    try {
      const { getUserMenusApi } = await import('@/api/login')
      const menusRes = await getUserMenusApi()
      roleRouters = menusRes.data || []
      userStore.setRoleRouters(roleRouters)
      console.log('获取菜单数据成功:', roleRouters.length, '个菜单项')
    } catch (error) {
      console.error('获取菜单数据失败:', error)
    }
  }

  // 使用静态路由模式，加载所有路由
  if (appStore.getDynamicRouter) {
    try {
      // 尝试使用服务端动态路由
      appStore.serverDynamicRouter
        ? await permissionStore.generateRoutes('server', roleRouters as AppCustomRouteRecordRaw[])
        : await permissionStore.generateRoutes('frontEnd', roleRouters as string[])

      // 检查是否成功加载菜单
      if (permissionStore.getRouters.length === 0) {
        // 加载失败，使用静态路由
        console.warn('Server routes loading failed, falling back to static routes')
        await permissionStore.generateRoutes('static')
      }
    } catch (error) {
      // 发生错误，使用静态路由
      console.error('Failed to load server routes:', error)
      await permissionStore.generateRoutes('static')
    }
  } else {
    await permissionStore.generateRoutes('static')
  }

  // 动态添加所有路由
  permissionStore.getAddRouters.forEach((route) => {
    router.addRoute(route as unknown as RouteRecordRaw)
  })

  const redirectPath = from.query.redirect || to.path
  const redirect = decodeURIComponent(redirectPath as string)
  const nextData = to.path === redirect ? { ...to, replace: true } : { path: redirect }
  permissionStore.setIsAddRouters(true)
  next(nextData)
})

router.afterEach((to) => {
  useTitle(to?.meta?.title as string)
  done() // 结束Progress
  loadDone()
})
