<script setup lang="ts">
import { propTypes } from '@/utils/propTypes'
import { computed, unref } from 'vue'
import { useRouter } from 'vue-router'

const { currentRoute } = useRouter()

const props = defineProps({
  permission: propTypes.string.def()
})

const currentPermission = computed(() => {
  return unref(currentRoute)?.meta?.permission || []
})

const hasPermission = computed(() => {
  return currentPermission.value.includes(props.permission)
})
</script>

<template>
  <template v-if="hasPermission">
    <slot></slot>
  </template>
</template>
