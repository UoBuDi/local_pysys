<script setup lang="ts">
import { propTypes } from '@/utils/propTypes'
import { computed } from 'vue'
import { useUserStoreWithOut } from '@/store/modules/user'

const props = defineProps({
  permission: propTypes.string.def()
})

const userStore = useUserStoreWithOut()
const userPermissions = computed(() => {
  return userStore.getPermissions || []
})

const hasPermission = computed(() => {
  return userPermissions.value.includes(props.permission)
})
</script>

<template>
  <template v-if="hasPermission">
    <slot></slot>
  </template>
</template>
