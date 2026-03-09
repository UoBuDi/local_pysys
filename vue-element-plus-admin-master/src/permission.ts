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

  if (to.path === '/login') {
    if (userStore.getUserInfo) {
      next({ path: '/' })
    } else {
      next()
    }
    return
  }

  const userInfo = userStore.getUserInfo
  const roleList = userInfo?.roleList || []

  if (roleList.includes('超级管理员') || roleList.includes('管理员')) {
    if (permissionStore.getIsAddRouters) {
      next()
      return
    }

    let roleRouters = userStore.getRoleRouters || []

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
        console.error('Failed to load server routes:', error)
        await permissionStore.generateRoutes('static')
      }
    } else {
      await permissionStore.generateRoutes('static')
    }

    permissionStore.getAddRouters.forEach((route) => {
      router.addRoute(route as unknown as RouteRecordRaw)
    })

    const redirectPath = from.query.redirect || to.path
    const redirect = decodeURIComponent(redirectPath as string)
    const nextData = to.path === redirect ? { ...to, replace: true } : { path: redirect }
    permissionStore.setIsAddRouters(true)
    next(nextData)
  } else {
    next({ path: '/404' })
  }
})

router.afterEach((to) => {
  useTitle(to?.meta?.title as string)
  done() // 结束Progress
  loadDone()
})
