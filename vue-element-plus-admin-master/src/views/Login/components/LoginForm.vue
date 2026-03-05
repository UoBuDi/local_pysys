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
      placeholder: 'admin or test'
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
      placeholder: 'admin or test',
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

          // 设置token
          userStore.setToken((tokenData as any).token)

          // 设置用户信息
          const roleList: string[] = []
          if (userData.username === 'admin' || userData.username === 'test') {
            roleList.push('超级管理员')
          }

          userStore.setUserInfo({
            username: userData.username,
            id: userData.id,
            password: '', // API没有返回密码，所以设为空字符串
            role: '', // API没有返回角色，所以设为空字符串
            roleId: '', // API没有返回角色ID，所以设为空字符串
            roleList // 添加角色列表
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

          // 设置菜单权限
          permissionStore.setIsAddRouters(true)

          // 跳转到指定页面或首页
          await nextTick()
          await push(redirect.value || '/')
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
