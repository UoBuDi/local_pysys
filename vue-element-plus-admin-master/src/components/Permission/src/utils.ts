import { useI18n } from '@/hooks/web/useI18n'
import { useUserStoreWithOut } from '@/store/modules/user'

export const hasPermi = (value: string) => {
  const { t } = useI18n()
  const userStore = useUserStoreWithOut()
  const permissions = userStore.getPermissions || []
  if (!value) {
    throw new Error(t('permission.hasPermission'))
  }
  if (permissions.includes(value)) {
    return true
  }
  return false
}
