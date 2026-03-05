import { watch, ref, computed } from 'vue'
import { isString } from '@/utils/is'
import { useAppStoreWithOut } from '@/store/modules/app'
import { useI18n } from '@/hooks/web/useI18n'

export const useTitle = (newTitle?: string) => {
  const { t } = useI18n()
  const appStore = useAppStoreWithOut()

  const systemTitle = computed(() => t('common.systemTitle'))

  const title = computed(() => {
    return newTitle ? `${systemTitle.value} - ${t(newTitle as string)}` : systemTitle.value
  })

  watch(
    title,
    (n, o) => {
      if (isString(n) && n !== o && document) {
        document.title = n
      }
    },
    { immediate: true }
  )

  return title
}
