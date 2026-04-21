<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElForm, ElFormItem, ElInput, ElButton, ElMessage, ElAlert, ElDivider } from 'element-plus'
import {
  getCloudPortalAccount,
  saveCloudPortalAccount,
  deleteCloudPortalAccount
} from '@/api/split-match'
import type { CloudPortalAccount } from '@/api/split-match'

const formRef = ref()
const loading = ref(false)
const deleteLoading = ref(false)
const accountInfo = ref<CloudPortalAccount | null>(null)

const formData = ref({
  portal_username: '',
  portal_password: ''
})

const rules = {
  portal_username: [{ required: true, message: '请输入云门户用户名', trigger: 'blur' }],
  portal_password: [{ required: true, message: '请输入云门户密码', trigger: 'blur' }]
}

const fetchAccountInfo = async () => {
  loading.value = true
  try {
    const response = await getCloudPortalAccount()
    if (response && response.code === 200) {
      accountInfo.value = response.data as any
      if (accountInfo.value) {
        formData.value.portal_username = accountInfo.value.portal_username
        formData.value.portal_password = ''
      }
    }
  } catch (error: any) {
    console.error('获取云门户账号信息失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        const response = await saveCloudPortalAccount({
          portal_username: formData.value.portal_username,
          portal_password: formData.value.portal_password
        })
        if (response && response.code === 200) {
          ElMessage.success('绑定成功')
          fetchAccountInfo()
        } else {
          ElMessage.error(response?.message || '绑定失败')
        }
      } catch (error: any) {
        ElMessage.error(error?.message || '绑定失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const handleDelete = async () => {
  deleteLoading.value = true
  try {
    const response = await deleteCloudPortalAccount()
    if (response && response.code === 200) {
      ElMessage.success('解绑成功')
      accountInfo.value = null
      formData.value.portal_username = ''
      formData.value.portal_password = ''
    } else {
      ElMessage.error(response?.message || '解绑失败')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '解绑失败')
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  fetchAccountInfo()
})
</script>

<template>
  <div class="cloud-portal-account">
    <ElAlert type="info" :closable="false" style="margin-bottom: 20px">
      绑定云门户账号后，在进行云门户人工核查时可自动填充账号密码，无需手动输入
    </ElAlert>

    <ElDivider content-position="left">
      {{ accountInfo ? '已绑定账号' : '绑定云门户账号' }}
    </ElDivider>

    <ElForm
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      style="max-width: 500px"
    >
      <ElFormItem label="云门户用户名" prop="portal_username">
        <ElInput
          v-model="formData.portal_username"
          placeholder="请输入云门户用户名"
          :disabled="loading"
        />
      </ElFormItem>

      <ElFormItem :label="accountInfo ? '新密码(留空不修改)' : '云门户密码'" prop="portal_password">
        <ElInput
          v-model="formData.portal_password"
          type="password"
          :placeholder="accountInfo ? '留空则保持原密码不变' : '请输入云门户密码'"
          show-password
          :disabled="loading"
        />
      </ElFormItem>

      <ElFormItem>
        <ElButton type="primary" :loading="loading" @click="handleSubmit">
          {{ accountInfo ? '更新绑定' : '绑定账号' }}
        </ElButton>
        <ElButton v-if="accountInfo" type="danger" :loading="deleteLoading" @click="handleDelete">
          解除绑定
        </ElButton>
      </ElFormItem>
    </ElForm>

    <div v-if="accountInfo" style="margin-top: 20px; color: #909399; font-size: 12px">
      <p>绑定时间: {{ accountInfo.created_at }}</p>
      <p v-if="accountInfo.updated_at !== accountInfo.created_at">
        更新时间: {{ accountInfo.updated_at }}
      </p>
    </div>
  </div>
</template>

<style lang="less" scoped>
.cloud-portal-account {
  padding: 20px;
}
</style>
