<script setup lang="ts">
import { Error } from '@/components/Error'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { useUserStore } from '@/store/modules/user'
import { useRouter } from 'vue-router'
import { hasValidRefreshToken, isTokenExpired } from '@/utils/auth'

const { push } = useRouter()
const permissionStore = usePermissionStoreWithOut()
const userStore = useUserStore()

const errorClick = async () => {
  const token = userStore.getToken
  
  if (!token) {
    push('/login')
    return
  }
  
  if (isTokenExpired() && !hasValidRefreshToken()) {
    push('/login')
    return
  }
  
  push('/')
}
</script>

<template>
  <Error type="500" @error-click="errorClick" />
</template>
