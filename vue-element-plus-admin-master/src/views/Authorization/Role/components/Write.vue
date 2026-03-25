<script setup lang="tsx">
import { Form, FormSchema } from '@/components/Form'
import { useForm } from '@/hooks/web/useForm'
import { PropType, reactive, watch, ref, unref, nextTick, onMounted } from 'vue'
import { useValidator } from '@/hooks/web/useValidator'
import { useI18n } from '@/hooks/web/useI18n'
import { ElTree, ElCheckboxGroup, ElCheckbox } from 'element-plus'
import { getMenuListApi } from '@/api/menu'
import { filter, eachTree } from '@/utils/tree'
import { findIndex } from '@/utils'
import { getRoleMenusApi } from '@/api/role'

const { t } = useI18n()

const { required } = useValidator()

const props = defineProps({
  currentRow: {
    type: Object as PropType<any>,
    default: () => null
  }
})

const treeRef = ref<typeof ElTree>()

const formSchema = ref<FormSchema[]>([
  {
    field: 'roleName',
    label: t('role.roleName'),
    component: 'Input'
  },
  {
    field: 'status',
    label: t('menu.status'),
    component: 'Select',
    componentProps: {
      options: [
        {
          label: t('userDemo.disable'),
          value: 0
        },
        {
          label: t('userDemo.enable'),
          value: 1
        }
      ]
    }
  },
  {
    field: 'menu',
    label: t('role.menu'),
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: () => {
          return (
            <>
              <div class="flex w-full menu-assignment-container">
                <div class="flex-1">
                  {/* 全选复选框 */}
                  <div class="menu-select-all mb-20px">
                    <ElCheckbox
                      v-model={selectAll.value}
                      indeterminate={isIndeterminate.value}
                      onChange={handleSelectAll}
                    >
                      全选
                    </ElCheckbox>
                  </div>

                  <ElTree
                    ref={treeRef}
                    show-checkbox
                    node-key="id"
                    highlight-current
                    check-strictly
                    expand-on-click-node={false}
                    data={treeData.value}
                    onNode-click={nodeClick}
                    onCheck={checkSelectAll}
                  >
                    {{
                      default: (data) => {
                        return <span>{data.data.meta.title}</span>
                      }
                    }}
                  </ElTree>
                </div>
                <div class="flex-1">
                  {unref(currentTreeData) && unref(currentTreeData)?.permissionList ? (
                    <ElCheckboxGroup v-model={unref(currentTreeData).meta.permission}>
                      {unref(currentTreeData)?.permissionList.map((v: any) => {
                        return <ElCheckbox label={v.value}>{v.label}</ElCheckbox>
                      })}
                    </ElCheckboxGroup>
                  ) : null}
                </div>
              </div>
            </>
          )
        }
      }
    }
  }
])

const currentTreeData = ref()
const nodeClick = (treeData: any) => {
  currentTreeData.value = treeData
}

// 全选相关
const selectAll = ref(false)
const isIndeterminate = ref(false)

// 获取所有菜单ID
const getAllMenuIds = (menus: any[]): number[] => {
  const ids: number[] = []
  const traverse = (items: any[]) => {
    items.forEach((item) => {
      ids.push(item.id)
      if (item.children && item.children.length > 0) {
        traverse(item.children)
      }
    })
  }
  traverse(menus)
  return ids
}

// 检查是否全选
const checkSelectAll = () => {
  const allMenuIds = getAllMenuIds(treeData.value)
  const checkedKeys = unref(treeRef)?.getCheckedKeys() || []
  const selectedCount = checkedKeys.length
  const totalCount = allMenuIds.length

  if (selectedCount === 0) {
    selectAll.value = false
    isIndeterminate.value = false
  } else if (selectedCount === totalCount) {
    selectAll.value = true
    isIndeterminate.value = false
  } else {
    selectAll.value = false
    isIndeterminate.value = true
  }
}

// 全选/取消全选
const handleSelectAll = (checked: boolean) => {
  if (checked) {
    const allMenuIds = getAllMenuIds(treeData.value)
    unref(treeRef)?.setCheckedKeys(allMenuIds)
  } else {
    unref(treeRef)?.setCheckedKeys([])
  }
  isIndeterminate.value = false
}

const rules = reactive({
  roleName: [required()],
  role: [required()],
  status: [required()]
})

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, getElFormExpose } = formMethods

const treeData = ref([])
const getMenuList = async () => {
  const res = await getMenuListApi()
  if (res) {
    treeData.value = res.data.list
    if (!props.currentRow) return
    await nextTick()

    let checkedMenuIds: number[] = []
    if (props.currentRow.id) {
      try {
        const menuRes = await getRoleMenusApi(props.currentRow.id)
        if (menuRes.code === 200) {
          checkedMenuIds = menuRes.data || []
        }
      } catch (error) {
        console.error('获取角色菜单失败:', error)
      }
    }

    for (const menuId of checkedMenuIds) {
      unref(treeRef)?.setChecked(menuId, true, false)
    }

    nextTick(() => {
      checkSelectAll()
    })
  }
}
getMenuList()

const submit = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate().catch((err) => {
    console.log(err)
  })
  if (valid) {
    const formData = await getFormData()
    const checkedKeys = unref(treeRef)?.getCheckedKeys() || []
    const data = filter(unref(treeData), (item: any) => {
      return checkedKeys.includes(item.id)
    })
    formData.menu = data || []
    // 处理字段映射：roleName -> name
    if (formData.roleName && !formData.name) {
      formData.name = formData.roleName
    }
    console.log(formData)
    return formData
  }
}

watch(
  () => props.currentRow,
  (currentRow) => {
    if (!currentRow) return
    // 处理字段映射：name -> roleName
    const dataToSet = { ...currentRow }
    if (dataToSet.name && !dataToSet.roleName) {
      dataToSet.roleName = dataToSet.name
    }
    setValues(dataToSet)
    // 重新加载菜单数据以获取最新的菜单分配
    getMenuList()
  },
  {
    deep: true,
    immediate: true
  }
)

defineExpose({
  submit
})
</script>

<template>
  <Form :rules="rules" @register="formRegister" :schema="formSchema" />
</template>

<style scoped lang="scss">
.menu-assignment-container {
  .menu-select-all {
    padding: 10px 0;
    border-bottom: 1px solid #e4e7ed;
    margin-bottom: 20px;

    :deep(.el-checkbox) {
      font-size: 14px;
      font-weight: 500;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .menu-assignment-container {
    .menu-select-all {
      margin-bottom: 15px;
      padding: 8px 0;
    }
  }
}
</style>
