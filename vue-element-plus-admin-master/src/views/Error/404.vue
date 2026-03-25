<script setup lang="ts">
import { Error } from '@/components/Error'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { usePermissionStoreWithOut } from '@/store/modules/permission'
import { hasValidRefreshToken, isTokenExpired } from '@/utils/auth'

const { push } = useRouter()
const userStore = useUserStore()
const permissionStore = usePermissionStoreWithOut()

const errorClick = async () => {
  const token = userStore.getToken
  
  if (!token) {
    push('/login')
    return
  }
  
  if (isTokenExpired()) {
    if (hasValidRefreshToken()) {
      push('/')
    } else {
      push('/login')
    }
    return
  }
  
  if (!permissionStore.getIsAddRouters) {
    push('/')
    return
  }
  
  push('/')
}
</script>

<template>
  <Error @error-click="errorClick" />
</template>
