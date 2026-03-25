<script setup lang="tsx">
import { reactive, ref, watch, onMounted, unref, nextTick } from 'vue'
import { Form, FormSchema } from '@/components/Form'
import { useI18n } from '@/hooks/web/useI18n'
import { ElCheckbox, ElLink } from 'element-plus'
import { useForm } from '@/hooks/web/useForm'
import { loginApi, getUserMenusApi } from '@/api/login'
import { usePermissionStore } from '@/store/modules/permission'
import { useRouter } from 'vue-router'
import type { RouteLocationNormalizedLoaded, RouteRecordRaw } from 'vue-router'
import { useValidator } from '@/hooks/web/useValidator'
import { Icon } from '@/components/Icon'
import { useUserStore } from '@/store/modules/user'
import { BaseButton } from '@/components/Button'
import { ElMessage } from 'element-plus'
import { clearRouteCache } from '@/permission'

const { required } = useValidator()

const emit = defineEmits(['to-register'])

const userStore = useUserStore()

const permissionStore = usePermissionStore()

const { currentRoute, addRoute, push } = useRouter()

const { t } = useI18n()

const rules = {
  username: [required()],
  password: [required()]
}

const schema = reactive<FormSchema[]>([
  {
    field: 'title',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return <h2 class="text-2xl font-bold text-center w-[100%]">{t('login.login')}</h2>
        }
      }
    }
  },
  {
    field: 'username',
    label: t('login.username'),
    // value: 'admin',
    component: 'Input',
    colProps: {
      span: 24
    },
    componentProps: {
      placeholder: '请输入用户名'
    }
  },
  {
    field: 'password',
    label: t('login.password'),
    // value: 'admin',
    component: 'InputPassword',
    colProps: {
      span: 24
    },
    componentProps: {
      style: {
        width: '100%'
      },
      placeholder: '请输入密码', 
      // 按下enter键触发登录
      onKeydown: (_e: any) => {
        if (_e.key === 'Enter') {
          _e.stopPropagation() // 阻止事件冒泡
          signIn()
        }
      }
    }
  },
  {
    field: 'tool',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex justify-between items-center w-[100%]">
                <ElCheckbox v-model={remember.value} label={t('login.remember')} size="small" />
                <ElLink type="primary" underline="never">
                  {t('login.forgetPassword')}
                </ElLink>
              </div>
            </>
          )
        }
      }
    }
  },
  {
    field: 'login',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="w-[100%]">
                <BaseButton
                  loading={loading.value}
                  type="primary"
                  class="w-[100%]"
                  onClick={signIn}
                >
                  {t('login.login')}
                </BaseButton>
              </div>
              <div class="w-[100%] mt-15px">
                <BaseButton class="w-[100%]" onClick={toRegister}>
                  {t('login.register')}
                </BaseButton>
              </div>
            </>
          )
        }
      }
    }
  },
  {
    field: 'other',
    component: 'Divider',
    label: t('login.otherLogin'),
    componentProps: {
      contentPosition: 'center'
    }
  },
  {
    field: 'otherIcon',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex justify-between w-[100%]">
                <Icon
                  icon="vi-ant-design:github-filled"
                  size={iconSize}
                  class="cursor-pointer ant-icon"
                  color={iconColor}
                  hoverColor={hoverColor}
                />
                <Icon
                  icon="vi-ant-design:wechat-filled"
                  size={iconSize}
                  class="cursor-pointer ant-icon"
                  color={iconColor}
                  hoverColor={hoverColor}
                />
                <Icon
                  icon="vi-ant-design:alipay-circle-filled"
                  size={iconSize}
                  color={iconColor}
                  hoverColor={hoverColor}
                  class="cursor-pointer ant-icon"
                />
                <Icon
                  icon="vi-ant-design:weibo-circle-filled"
                  size={iconSize}
                  color={iconColor}
                  hoverColor={hoverColor}
                  class="cursor-pointer ant-icon"
                />
              </div>
            </>
          )
        }
      }
    }
  }
])

const iconSize = 30

const remember = ref(userStore.getRememberMe)

const initLoginInfo = () => {
  const loginInfo = userStore.getLoginInfo
  if (loginInfo) {
    const { username, password } = loginInfo
    setValues({ username, password })
  }
}
onMounted(() => {
  initLoginInfo()
})

const { formRegister, formMethods } = useForm()
const { getFormData, getElFormExpose, setValues } = formMethods

const loading = ref(false)

const iconColor = '#999'

const hoverColor = 'var(--el-color-primary)'

const redirect = ref<string>('')

watch(
  () => currentRoute.value,
  (route: RouteLocationNormalizedLoaded) => {
    redirect.value = route?.query?.redirect as string
  },
  {
    immediate: true
  }
)

// 登录
const signIn = async () => {
  const formRef = await getElFormExpose()
  await formRef?.validate(async (isValid) => {
    if (isValid) {
      loading.value = true
      const formData = await getFormData()

      try {
        // 登录前清除所有缓存，确保获取最新数据
        clearRouteCache()
        userStore.setRoleRouters([])
        permissionStore.reset()
        console.log('已清除所有缓存，准备重新登录')

        const res = await loginApi({
          username: formData.username,
          password: formData.password
        })

        // 直接检查响应数据，axios拦截器会处理code === 200的情况
        if (res && res.data && res.data.user) {
          // 是否记住我
          if (unref(remember)) {
            userStore.setLoginInfo({
              username: formData.username,
              password: formData.password
            })
          } else {
            userStore.setLoginInfo(undefined)
          }

          // 设置用户信息
          const userData = res.data.user
          const tokenData = res.data

          // 设置token及相关数据
          userStore.setTokenData({
            token: tokenData.token || '',
            refreshToken: tokenData.refreshToken || '',
            expiresAt: tokenData.expiresAt || 0,
            refreshExpiresAt: tokenData.refreshExpiresAt || 0
          })

          // 设置用户信息 - 使用后端返回的角色信息
          const roleList = userData.roleList || []

          userStore.setUserInfo({
            username: userData.username,
            id: userData.id,
            password: '',
            role: '',
            roleId: '',
            roleList
          })

          // 从后端获取菜单数据
          const menusRes = await getUserMenusApi()
          const serverMenus = menusRes.data || []
          userStore.setRoleRouters(serverMenus)

          // 设置菜单权限 - 使用服务端动态路由
          await permissionStore.generateRoutes('server', serverMenus)

          // 动态添加路由
          permissionStore.getAddRouters.forEach((route) => {
            addRoute(route as unknown as RouteRecordRaw)
          })

          // 设置菜单权限标志，避免路由守卫重复添加
          permissionStore.setIsAddRouters(true)

          // 使用 permissionStore 的 addRouters 找到第一个可用的菜单路径
          let firstMenuPath = '/dashboard/analysis'
          if (permissionStore.getAddRouters && permissionStore.getAddRouters.length > 0) {
            const firstRoute = permissionStore.getAddRouters[0]
            if (firstRoute.path) {
              firstMenuPath = firstRoute.path
              // 如果有子路由，优先使用第一个子路由
              if (firstRoute.children && firstRoute.children.length > 0) {
                const firstChild = firstRoute.children[0]
                if (firstChild.path && !firstChild.path.startsWith('/')) {
                  firstMenuPath = `${firstRoute.path}/${firstChild.path}`.replace(/\/\//g, '/')
                }
              }
            }
          }
          
          console.log('登录成功，跳转到首页:', firstMenuPath)
          console.log('可用的路由:', permissionStore.getAddRouters?.map(r => r.path))

          // 跳转到指定页面或智能找到的首页
          await nextTick()
          await push(redirect.value || firstMenuPath)
        } else {
          console.log('登录失败:', res?.data?.message || '未知错误')
          ElMessage.error(res?.data?.message || '登录失败')
        }
      } catch (error: any) {
        console.error('登录异常:', error)
        ElMessage.error(error.message || '登录过程中发生错误')
      } finally {
        loading.value = false
      }
    }
  })
}

const toRegister = () => {
  emit('to-register')
}
</script>

<template>
  <Form
    :schema="schema"
    :rules="rules"
    label-position="top"
    hide-required-asterisk
    size="large"
    class="dark:(border-1 border-[var(--el-border-color)] border-solid)"
    @register="formRegister"
  />
</template>
