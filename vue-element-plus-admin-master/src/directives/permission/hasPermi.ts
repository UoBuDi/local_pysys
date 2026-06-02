import type { App, Directive, DirectiveBinding } from 'vue'
import { useI18n } from '@/hooks/web/useI18n'
import { useUserStoreWithOut } from '@/store/modules/user'

const { t } = useI18n()

const hasPermission = (value: string): boolean => {
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

function updateElementVisibility(el: Element, binding: DirectiveBinding) {
  const value = binding.value
  const flag = hasPermission(value)
  if (flag) {
    el.removeAttribute('style')
    ;(el as HTMLElement).style.display = ''
  } else {
    ;(el as HTMLElement).style.display = 'none'
  }
}

const permiDirective: Directive = {
  mounted(el: Element, binding: DirectiveBinding<any>) {
    updateElementVisibility(el, binding)
  },
  updated(el: Element, binding: DirectiveBinding<any>) {
    updateElementVisibility(el, binding)
  }
}

export const setupPermissionDirective = (app: App<Element>) => {
  app.directive('hasPermi', permiDirective)
}

export default permiDirective
