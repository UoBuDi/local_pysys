import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getCloudPortalCaptcha,
  cloudPortalLogin,
  cloudPortalAutoLogin,
  cloudPortalLogout,
  getCloudPortalCredentials,
  setCloudPortalAccessToken,
  removeCloudPortalAccessToken,
  getCloudPortalAccessToken
} from '@/api/split-match'
import { useUserStore } from '@/store/modules/user'

export interface CloudPortalFormData {
  username: string
  password: string
  captcha: string
  passId: string
  plateNumber: string
  gateTime: string
  entryTime: string
  entryStationName: string
  gantryNamesCombined: string
  hours: number
  rows: number
}

export const useCloudPortal = () => {
  const userStore = useUserStore()
  const getUserId = () => userStore.getUserInfo?.id as number | undefined

  const cloudPortalDialogVisible = ref(false)
  const cloudPortalLoggedIn = ref(false)
  const cloudPortalUserInfo = ref<any>(null)
  const cloudPortalAccessToken = ref<string>('')
  const cloudPortalForm = ref<CloudPortalFormData>({
    username: '',
    password: '',
    captcha: '',
    passId: '',
    plateNumber: '',
    gateTime: '',
    entryTime: '',
    entryStationName: '',
    gantryNamesCombined: '',
    hours: 24,
    rows: 50
  })
  const captchaImage = ref('')
  const captchaUuid = ref('')
  const captchaLoading = ref(false)
  const loginLoading = ref(false)
  const needManualCaptcha = ref(false)

  const loadCloudPortalCredentials = async () => {
    try {
      const response = await getCloudPortalCredentials(getUserId())
      if (response && response.code === 200 && response.data) {
        const credentials = response.data as any
        cloudPortalForm.value.username = credentials.portal_username || ''
        cloudPortalForm.value.password = credentials.portal_password || ''
      }
    } catch (error) {
      console.error('获取云门户凭证失败:', error)
    }

    try {
      const savedToken = getCloudPortalAccessToken(getUserId())
      if (savedToken) {
        cloudPortalAccessToken.value = savedToken
        cloudPortalLoggedIn.value = true
      }
    } catch (error) {
      console.error('恢复云门户访问令牌失败:', error)
    }
  }

  const refreshCaptcha = async (retryCount = 0) => {
    const MAX_RETRIES = 2
    const RETRY_DELAY = 1000

    if (retryCount === 0) {
      captchaLoading.value = true
    }

    try {
      const response = await getCloudPortalCaptcha()

      if (response && response.code === 200) {
        captchaImage.value = (response.data as any).img
        captchaUuid.value = (response.data as any).uuid

        if (retryCount > 0) {
          ElMessage.success('连接已恢复，验证码获取成功')
        }
      } else {
        if (retryCount < MAX_RETRIES) {
          ElMessage.warning(`验证码获取失败，正在重试 (${retryCount + 1}/${MAX_RETRIES})...`)
          await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY))
          return refreshCaptcha(retryCount + 1)
        } else {
          ElMessage.error({
            message: response?.message || '获取验证码失败，请稍后重试',
            duration: 5000,
            showClose: true
          })
        }
      }
    } catch (error: any) {
      if (retryCount < MAX_RETRIES) {
        ElMessage.warning(`网络异常，正在重试 (${retryCount + 1}/${MAX_RETRIES})...`)
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY))
        return refreshCaptcha(retryCount + 1)
      } else {
        ElMessage.error({
          message: error?.message || '网络连接异常，请检查网络设置或联系管理员',
          duration: 5000,
          showClose: true
        })
      }
    } finally {
      if (retryCount >= MAX_RETRIES || captchaImage.value) {
        captchaLoading.value = false
      }
    }
  }

  const handleCloudPortalLogin = async () => {
    if (!cloudPortalForm.value.username || !cloudPortalForm.value.password) {
      ElMessage.warning('请填写用户名和密码')
      return
    }

    if (needManualCaptcha.value && !cloudPortalForm.value.captcha) {
      ElMessage.warning('请填写验证码')
      return
    }

    loginLoading.value = true
    try {
      if (!needManualCaptcha.value) {
        const autoResponse = await cloudPortalAutoLogin(
          {
            username: cloudPortalForm.value.username,
            password: cloudPortalForm.value.password
          },
          getUserId()
        )

        if (autoResponse && autoResponse.code === 200) {
          ElMessage.success('登录成功')
          cloudPortalLoggedIn.value = true
          cloudPortalUserInfo.value = (autoResponse.data as any)?.user_info
          cloudPortalAccessToken.value = (autoResponse.data as any)?.access_token || ''

          if (cloudPortalAccessToken.value) {
            setCloudPortalAccessToken(cloudPortalAccessToken.value, getUserId())
          }

          return
        } else if (autoResponse && autoResponse.code === 201) {
          needManualCaptcha.value = true
          const data = autoResponse.data as any
          captchaImage.value = data.img
          captchaUuid.value = data.uuid
          ElMessage.warning('验证码识别失败，请手动输入')
          return
        } else {
          needManualCaptcha.value = true
          await refreshCaptcha()
          ElMessage.error(autoResponse?.message || '自动登录失败，请手动输入验证码')
          return
        }
      }

      const response = await cloudPortalLogin({
        uuid: captchaUuid.value,
        username: cloudPortalForm.value.username,
        password: cloudPortalForm.value.password,
        captcha: cloudPortalForm.value.captcha
      })

      if (response && response.code === 200) {
        ElMessage.success('登录成功')
        cloudPortalLoggedIn.value = true
        cloudPortalUserInfo.value = (response.data as any)?.user_info
        cloudPortalAccessToken.value = (response.data as any)?.access_token || ''

        if (cloudPortalAccessToken.value) {
          setCloudPortalAccessToken(cloudPortalAccessToken.value, getUserId())
        }
      } else {
        ElMessage.error(response?.message || '登录失败')
        await refreshCaptcha()
        cloudPortalForm.value.captcha = ''
      }
    } catch (error: any) {
      ElMessage.error(error?.message || '登录失败')
      await refreshCaptcha()
      cloudPortalForm.value.captcha = ''
    } finally {
      loginLoading.value = false
    }
  }

  const handleCloudPortalLogout = async () => {
    try {
      await cloudPortalLogout(getUserId())
      cloudPortalLoggedIn.value = false
      cloudPortalUserInfo.value = null
      cloudPortalAccessToken.value = ''
      removeCloudPortalAccessToken(getUserId())

      ElMessage.success('已退出登录')
    } catch (error) {
      console.error('退出登录失败:', error)
    }
  }

  return {
    cloudPortalDialogVisible,
    cloudPortalLoggedIn,
    cloudPortalUserInfo,
    cloudPortalAccessToken,
    cloudPortalForm,
    captchaImage,
    captchaUuid,
    captchaLoading,
    loginLoading,
    needManualCaptcha,
    loadCloudPortalCredentials,
    refreshCaptcha,
    handleCloudPortalLogin,
    handleCloudPortalLogout
  }
}
