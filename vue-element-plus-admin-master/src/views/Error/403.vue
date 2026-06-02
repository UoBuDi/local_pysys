<script setup lang="ts">
import { Error } from '@/components/Error'
import { useRouter } from 'vue-router'
import { useUserStoreWithOut } from '@/store/modules/user'

const { replace } = useRouter()
const userStore = useUserStoreWithOut()

const errorClick = () => {
  if (userStore.getUserInfo) {
    replace('/dashboard/analysis')
  } else {
    replace('/login')
  }
}
</script>

<template>
  <Error type="403" @error-click="errorClick" />
</template>
