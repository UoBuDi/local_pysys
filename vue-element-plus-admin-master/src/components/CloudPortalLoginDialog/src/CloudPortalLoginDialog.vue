<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElDialog, ElForm, ElFormItem, ElInput, ElButton, ElImage, ElMessage } from 'element-plus'
import { 
  getCloudPortalCaptcha, 
  cloudPortalLogin, 
  getCloudPortalCredentials,
  getCloudPortalStatus,
  updateCloudPortalSession
} from '@/api/split-match'

interface Props {
  visible: boolean
  title?: string
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success', data: { access_token: string; user_info: any }): void
  (e: 'cancel'): void
}

const props = withDefaults(defineProps<Props>(), {
  title: '云门户登录'
})

const emit = defineEmits<Emits>()

const dialogVisible = ref(props.visible)
const loading = ref(false)
const captchaLoading = ref(false)
const captchaImage = ref('')
const captchaUuid = ref('')
const sessionId = ref('')
const checkingSession = ref(false)

const loginForm = ref({
  username: '',
  password: '',
  captcha: ''
})

watch(() => props.visible, (val) => {
  dialogVisible.value = val
  if (val) {
    loadAccountInfo()
  }
})

watch(dialogVisible, (val) => {
  emit('update:visible', val)
})

const loadAccountInfo = async () => {
  checkingSession.value = true
  try {
    const response = await getCloudPortalCredentials()
    if (response && response.code === 200 && response.data) {
      const credentials = response.data as any
      loginForm.value.username = credentials.portal_username || ''
      loginForm.value.password = credentials.portal_password || ''
      sessionId.value = credentials.portal_session_id || ''
      
      if (sessionId.value) {
        const statusRes = await getCloudPortalStatus(sessionId.value)
        if (statusRes && statusRes.code === 200 && (statusRes.data as any)?.logged_in) {
          emit('success', {
            access_token: '',
            user_info: (statusRes.data as any).user_info
          })
          dialogVisible.value = false
          return
        }
      }
    }
    
    await refreshCaptcha()
  } catch (e) {
    console.error('获取账号信息失败:', e)
    await refreshCaptcha()
  } finally {
    checkingSession.value = false
  }
}

const refreshCaptcha = async (retryCount = 0) => {
  const MAX_RETRIES = 3
  const RETRY_DELAY = 1000
  
  if (retryCount === 0) {
    captchaLoading.value = true
  }
  
  try {
    const response = await getCloudPortalCaptcha(sessionId.value || undefined)
    
    if (response && response.code === 200) {
      captchaImage.value = (response.data as any).img
      captchaUuid.value = (response.data as any).uuid
      sessionId.value = (response.data as any).session_id
      
      if (retryCount > 0) {
        ElMessage.success('连接已恢复，验证码获取成功')
      }
    } else {
      if (retryCount < MAX_RETRIES) {
        ElMessage.warning(`验证码获取失败，正在重试 (${retryCount + 1}/${MAX_RETRIES})...`)
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY))
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
      await new Promise(resolve => setTimeout(resolve, RETRY_DELAY))
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

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password || !loginForm.value.captcha) {
    ElMessage.warning('请填写完整的登录信息')
    return
  }

  loading.value = true
  try {
    const response = await cloudPortalLogin({
      session_id: sessionId.value,
      username: loginForm.value.username,
      password: loginForm.value.password,
      captcha: loginForm.value.captcha,
      uuid: captchaUuid.value
    })

    if (response && response.code === 200) {
      ElMessage.success('登录成功')
      
      try {
        await updateCloudPortalSession(sessionId.value)
      } catch (e) {
        console.error('保存会话ID失败:', e)
      }
      
      emit('success', {
        access_token: (response.data as any)?.access_token || '',
        user_info: (response.data as any)?.user_info
      })
      dialogVisible.value = false
    } else {
      ElMessage.error(response?.message || '登录失败')
      await refreshCaptcha()
      loginForm.value.captcha = ''
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '登录失败')
    await refreshCaptcha()
    loginForm.value.captcha = ''
  } finally {
    loading.value = false
  }
}

const handleCancel = () => {
  dialogVisible.value = false
  emit('cancel')
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !loading.value) {
    handleLogin()
  }
}
</script>

<template>
  <ElDialog
    v-model="dialogVisible"
    :title="title"
    width="400px"
    :close-on-click-modal="false"
    destroy-on-close
    @keydown="handleKeydown"
  >
    <div v-if="checkingSession" style="text-align: center; padding: 20px; color: #909399;">
      正在检查登录状态...
    </div>
    <ElForm v-else :model="loginForm" label-width="80px" @submit.prevent>
      <ElFormItem label="用户名">
        <ElInput
          v-model="loginForm.username"
          placeholder="请输入云门户用户名"
          clearable
        />
      </ElFormItem>
      <ElFormItem label="密码">
        <ElInput
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
          show-password
          clearable
        />
      </ElFormItem>
      <ElFormItem label="验证码">
        <div style="display: flex; gap: 8px; align-items: center;">
          <ElInput
            v-model="loginForm.captcha"
            placeholder="请输入验证码"
            style="flex: 1;"
            clearable
          />
          <div
            style="width: 120px; height: 32px; cursor: pointer; border: 1px solid #dcdfe6; border-radius: 4px; overflow: hidden;"
            @click="() => refreshCaptcha()"
          >
            <ElImage
              v-if="captchaImage"
              :src="'data:image/jpeg;base64,' + captchaImage"
              fit="fill"
              style="width: 100%; height: 100%;"
            >
              <template #error>
                <div style="display: flex; justify-content: center; align-items: center; height: 100%; color: #909399; font-size: 12px;">
                  加载失败
                </div>
              </template>
            </ElImage>
            <div v-else style="display: flex; justify-content: center; align-items: center; height: 100%; color: #909399; font-size: 12px;">
              {{ captchaLoading ? '加载中...' : '点击获取' }}
            </div>
          </div>
        </div>
      </ElFormItem>
    </ElForm>
    <template #footer>
      <div style="display: flex; justify-content: flex-end; gap: 8px;">
        <ElButton @click="handleCancel">取消</ElButton>
        <ElButton type="primary" :loading="loading" @click="handleLogin" :disabled="checkingSession">
          登录
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>
