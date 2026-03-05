<script setup lang="ts">
import { computed } from 'vue'
import { useDesign } from '@/hooks/web/useDesign'
import { useI18n } from '@/hooks/web/useI18n'

const { getPrefixCls } = useDesign()
const { t } = useI18n()

const prefixCls = getPrefixCls('footer')

const title = computed(() => t('common.systemTitle'))
</script>

<template>
  <div
    :class="prefixCls"
    class="text-center text-[var(--el-text-color-placeholder)] bg-[var(--app-content-bg-color)] h-[var(--app-footer-height)] leading-[var(--app-footer-height)] dark:bg-[var(--el-bg-color)] overflow-hidden"
  >
    Copyright ©2025-present {{ title }}
  </div>
</template>
