<script setup lang="tsx">
import { reactive, ref, unref, watch, computed, nextTick } from 'vue'
import {
  getRoleListApi,
  saveRoleApi,
  deleteRoleApi,
  assignRoleMenusApi,
  getRoleMenusApi,
  getPermissionListApi,
  assignRolePermissionsApi,
  getRolePermissionsApi
} from '@/api/role'
import { useTable } from '@/hooks/web/useTable'
import { useI18n } from '@/hooks/web/useI18n'
import { Table, TableColumn } from '@/components/Table'
import { ElTag, ElMessage } from 'element-plus'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { Dialog } from '@/components/Dialog'
import { BaseButton } from '@/components/Button'
import { getMenuListApi } from '@/api/menu'
import { hasPermi } from '@/components/Permission/src/utils'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const res = await getRoleListApi()
    return {
      list: res.data?.list || [],
      total: res.data?.total || 0
    }
  }
})

const { dataList, loading, total } = tableState
const { getList, getElTableExpose } = tableMethods

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'index',
    label: t('userDemo.index'),
    type: 'index'
  },
  {
    field: 'name',
    label: t('role.roleName')
  },
  {
    field: 'code',
    label: t('role.role')
  },
  {
    field: 'description',
    label: t('userDemo.remark')
  },
  {
    field: 'status',
    label: t('menu.status'),
    width: 80,
    formatter: (_, __, cellValue) => {
      return (
        <ElTag type={cellValue ? 'success' : 'danger'}>
          {cellValue ? t('userDemo.enable') : t('userDemo.disable')}
        </ElTag>
      )
    }
  },
  {
    field: 'created_at',
    label: t('userDemo.createTime'),
    width: 170
  },
  {
    field: 'action',
    label: t('userDemo.action'),
    width: 380,
    fixed: 'right',
    slots: {
      default: (data: any) => {
        return (
          <>
            {hasPermi('system:role:edit') && (
              <BaseButton type="primary" onClick={() => action(data.row, 'edit')}>
                {t('exampleDemo.edit')}
              </BaseButton>
            )}
            {hasPermi('system:role:view') && (
              <BaseButton type="success" onClick={() => action(data.row, 'detail')}>
                {t('exampleDemo.detail')}
              </BaseButton>
            )}
            {hasPermi('system:role:assign') && (
              <BaseButton type="warning" onClick={() => assignMenus(data.row)}>
                {t('role.menu')}
              </BaseButton>
            )}
            {hasPermi('system:role:assign-permission') && (
              <BaseButton type="info" onClick={() => assignPermissions(data.row)}>
                权限
              </BaseButton>
            )}
            {hasPermi('system:role:delete') && (
              <BaseButton type="danger" onClick={() => delData(data.row)}>
                {t('exampleDemo.del')}
              </BaseButton>
            )}
          </>
        )
      }
    }
  }
])

getList()

const searchSchema = reactive<FormSchema[]>([
  {
    field: 'name',
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
          label: t('userDemo.enable'),
          value: 1
        },
        {
          label: t('userDemo.disable'),
          value: 0
        }
      ]
    }
  }
])

const searchParams = ref({})

const setSearchParams = (params: any) => {
  searchParams.value = params
  getList()
}

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isDetail = ref(false)

const currentRow = ref<any>(null)

const AddAction = () => {
  dialogTitle.value = t('exampleDemo.add')
  currentRow.value = null
  dialogVisible.value = true
  isDetail.value = false
}

const delLoading = ref(false)

const delData = async (row: any) => {
  const elTableExpose = await getElTableExpose()
  const selection = row ? [row] : ((await elTableExpose?.getSelectionRows()) as any[])

  if (!selection.length) {
    return
  }

  delLoading.value = true

  try {
    // 将选中的行ID转换为数字数组
    const idsToDelete = selection.map((item) => item.id)
    await deleteRoleApi(idsToDelete)
    ElMessage.success(t('exampleDemo.delSuccess'))
    getList()
  } catch (error) {
    ElMessage.error(t('exampleDemo.delFailed'))
  } finally {
    delLoading.value = false
  }
}

const action = (row: any, type: string) => {
  dialogTitle.value = t(type === 'edit' ? 'exampleDemo.edit' : 'exampleDemo.detail')
  isDetail.value = type === 'detail'
  currentRow.value = row
  dialogVisible.value = true
}

const saveLoading = ref(false)

const save = async () => {
  const writeRef = unref(writeRefEl)
  if (!writeRef) return
  const formData = await writeRef.submit()
  if (!formData) return

  saveLoading.value = true
  try {
    const res = await saveRoleApi(formData)
    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      dialogVisible.value = false
      getList()
    } else {
      ElMessage.error(res.message || t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('exampleDemo.saveFailed'))
  } finally {
    saveLoading.value = false
  }
}

const writeRefEl = ref<ComponentRef<typeof Write>>()

const detailRef = ref<ComponentRef<typeof Detail>>()

// 菜单分配相关
const menuDialogVisible = ref(false)
const menuLoading = ref(false)
const menuList = ref<any[]>([])
const menuTreeRef = ref()
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
  const allMenuIds = getAllMenuIds(menuList.value)
  const checkedKeys = menuTreeRef.value?.getCheckedKeys() || []
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
    const allMenuIds = getAllMenuIds(menuList.value)
    menuTreeRef.value?.setCheckedKeys(allMenuIds)
  } else {
    menuTreeRef.value?.setCheckedKeys([])
  }
  isIndeterminate.value = false
}

// 获取菜单列表
const buildMenuTree = (items: any[], parentId = 0) => {
  return items
    .filter((item) => item.parentId === parentId && item.type !== 2)
    .map((item) => {
      const children = buildMenuTree(items, item.id)
      return {
        ...item,
        ...(children.length > 0 ? { children } : {})
      }
    })
}
const getMenuList = async () => {
  menuLoading.value = true
  try {
    const res = await getMenuListApi()
    const list = res.data?.list || []
    menuList.value = buildMenuTree(list)
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  } finally {
    menuLoading.value = false
  }
}

// 打开菜单分配对话框
// 从菜单树中提取所有叶子节点ID
const getLeafIds = (nodes: any[]): number[] => {
  const ids: number[] = []
  const traverse = (items: any[]) => {
    items.forEach((item) => {
      if (item.children && item.children.length > 0) {
        traverse(item.children)
      } else {
        ids.push(item.id)
      }
    })
  }
  traverse(nodes)
  return ids
}

// 从已保存的菜单ID中过滤出叶子节点ID（用于setCheckedKeys回显）
const filterLeafIds = (savedIds: number[], tree: any[]): number[] => {
  const leafSet = new Set(getLeafIds(tree))
  return savedIds.filter((id) => leafSet.has(id))
}

const assignMenus = async (row: any) => {
  currentRow.value = row
  menuDialogVisible.value = true

  await getMenuList()

  try {
    const res = await getRoleMenusApi(row.id)
    const menuIds = res.data || []
    const leafIds = filterLeafIds(menuIds, menuList.value)
    await nextTick()
    menuTreeRef.value?.setCheckedKeys(leafIds)
    checkSelectAll()
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  }
}

// 保存菜单分配
// 保存时必须包含半选父节点ID，后端需通过父节点构建完整菜单树
// 回显时仅传叶子节点ID给setCheckedKeys，el-tree自动推导父节点选中状态
const saveMenus = async () => {
  if (!currentRow.value) return

  try {
    const checkedKeys = menuTreeRef.value?.getCheckedKeys() || []
    const halfCheckedKeys = menuTreeRef.value?.getHalfCheckedKeys() || []
    const allMenuIds = [...checkedKeys, ...halfCheckedKeys]

    const res = await assignRoleMenusApi({
      role_id: currentRow.value.id,
      menu_ids: allMenuIds
    })

    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      menuDialogVisible.value = false
      // 刷新角色列表以获取最新数据
      getList()
    } else {
      ElMessage.error(res.message || t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('exampleDemo.saveFailed'))
  }
}

// 权限分配相关
const permissionDialogVisible = ref(false)
const permissionLoading = ref(false)
const permissionList = ref<any[]>([])
const selectedPermissions = ref<number[]>([])
const permissionSelectAll = ref(false)
const permissionIsIndeterminate = ref(false)

// 按所属菜单页面分组权限
const groupedPermissions = computed(() => {
  const groups: Record<string, any[]> = {}
  permissionList.value.forEach((perm) => {
    const groupKey = perm.menu_name || '未关联页面'
    if (!groups[groupKey]) {
      groups[groupKey] = []
    }
    groups[groupKey].push(perm)
  })
  return Object.keys(groups).map((menuName) => ({
    module: menuName,
    permissions: groups[menuName]
  }))
})

// 获取所有权限ID
const getAllPermissionIds = (permissions: any[]): number[] => {
  const ids: number[] = []
  permissions.forEach((item) => {
    ids.push(item.id)
  })
  return ids
}

// 检查是否全选
const checkPermissionSelectAll = () => {
  const allPermissionIds = getAllPermissionIds(permissionList.value)
  const selectedCount = selectedPermissions.value.length
  const totalCount = allPermissionIds.length

  if (selectedCount === 0) {
    permissionSelectAll.value = false
    permissionIsIndeterminate.value = false
  } else if (selectedCount === totalCount) {
    permissionSelectAll.value = true
    permissionIsIndeterminate.value = false
  } else {
    permissionSelectAll.value = false
    permissionIsIndeterminate.value = true
  }
}

// 全选/取消全选
const handlePermissionSelectAll = (checked: boolean) => {
  if (checked) {
    const allPermissionIds = getAllPermissionIds(permissionList.value)
    selectedPermissions.value = allPermissionIds
  } else {
    selectedPermissions.value = []
  }
  permissionIsIndeterminate.value = false
}

// 监听选中权限变化
watch(
  selectedPermissions,
  () => {
    checkPermissionSelectAll()
  },
  { deep: true }
)

// 获取权限列表
const getPermissionList = async () => {
  permissionLoading.value = true
  try {
    const res = await getPermissionListApi()
    permissionList.value = res.data || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  } finally {
    permissionLoading.value = false
  }
}

// 打开权限分配对话框
const assignPermissions = async (row: any) => {
  currentRow.value = row
  permissionDialogVisible.value = true

  // 获取权限列表
  await getPermissionList()

  // 获取角色当前的权限
  try {
    const res = await getRolePermissionsApi(row.id)
    selectedPermissions.value = res.data || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
    selectedPermissions.value = []
  }
}

// 保存权限分配
const savePermissions = async () => {
  if (!currentRow.value) return

  try {
    const res = await assignRolePermissionsApi({
      role_id: currentRow.value.id,
      permission_ids: selectedPermissions.value
    })

    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      permissionDialogVisible.value = false
      // 刷新角色列表以获取最新数据
      getList()
    } else {
      ElMessage.error(res.message || t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('exampleDemo.saveFailed'))
  }
}
</script>

<template>
  <ContentWrap>
    <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <div class="mt-20px">
      <BaseButton type="primary" @click="AddAction" v-hasPermi="'system:role:add'">
        {{ t('exampleDemo.add') }}
      </BaseButton>
      <BaseButton
        :loading="delLoading"
        type="danger"
        @click="delData(null)"
        v-hasPermi="'system:role:delete'"
      >
        {{ t('exampleDemo.del') }}
      </BaseButton>
    </div>

    <Table
      :columns="tableColumns"
      :data="dataList"
      :loading="loading"
      :pagination="{
        total
      }"
      @register="tableRegister"
    />
  </ContentWrap>

  <Dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :height="isDetail ? 400 : 'auto'"
    :width="800"
    @close="dialogVisible = false"
  >
    <Write v-if="!isDetail" ref="writeRefEl" :current-row="currentRow" />

    <Detail v-if="isDetail" ref="detailRef" :current-row="currentRow" />

    <template #footer>
      <BaseButton v-if="!isDetail" type="primary" :loading="saveLoading" @click="save">
        {{ t('exampleDemo.save') }}
      </BaseButton>
      <BaseButton @click="dialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>

  <!-- 菜单分配对话框 -->
  <Dialog
    v-model="menuDialogVisible"
    :title="t('role.menu')"
    :width="500"
    @close="menuDialogVisible = false"
  >
    <div v-loading="menuLoading">
      <!-- 全选复选框 -->
      <div class="menu-select-all mb-20px">
        <el-checkbox v-model="selectAll" :indeterminate="isIndeterminate" @change="handleSelectAll">
          全选
        </el-checkbox>
      </div>

      <el-tree
        ref="menuTreeRef"
        :data="menuList"
        show-checkbox
        node-key="id"
        :props="{ label: 'title', children: 'children' }"
        @check="checkSelectAll"
      />
    </div>

    <template #footer>
      <BaseButton type="primary" @click="saveMenus">{{ t('exampleDemo.save') }}</BaseButton>
      <BaseButton @click="menuDialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>

  <!-- 权限分配对话框 -->
  <Dialog
    v-model="permissionDialogVisible"
    title="权限分配"
    :width="700"
    @close="permissionDialogVisible = false"
  >
    <div v-loading="permissionLoading">
      <!-- 全选复选框 -->
      <div class="permission-select-all mb-20px">
        <el-checkbox
          v-model="permissionSelectAll"
          :indeterminate="permissionIsIndeterminate"
          @change="handlePermissionSelectAll"
        >
          全选
        </el-checkbox>
      </div>

      <!-- 权限列表 -->
      <div class="permission-list">
        <el-checkbox-group v-model="selectedPermissions">
          <div v-for="module in groupedPermissions" :key="module.module" class="permission-module">
            <div class="module-title">{{ module.module }}</div>
            <div class="module-permissions">
              <el-checkbox
                v-for="perm in module.permissions"
                :key="perm.id"
                :label="perm.id"
                class="permission-item"
              >
                <span class="permission-name">{{ perm.name }}</span>
                <span class="permission-code">({{ perm.code }})</span>
              </el-checkbox>
            </div>
          </div>
        </el-checkbox-group>
      </div>
    </div>

    <template #footer>
      <BaseButton type="primary" @click="savePermissions">{{ t('exampleDemo.save') }}</BaseButton>
      <BaseButton @click="permissionDialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>

<style scoped lang="scss">
.menu-select-all,
.permission-select-all {
  padding: 10px 0;
  border-bottom: 1px solid #e4e7ed;
  margin-bottom: 20px;

  :deep(.el-checkbox) {
    font-size: 14px;
    font-weight: 500;
  }
}

.permission-list {
  max-height: 400px;
  overflow-y: auto;
}

.permission-module {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.module-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
  padding-left: 10px;
  border-left: 3px solid #409eff;
}

.module-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding-left: 13px;
}

.permission-item {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f5f7fa;
  }

  .permission-name {
    font-size: 14px;
    color: #606266;
  }

  .permission-code {
    font-size: 12px;
    color: #909399;
    margin-left: 4px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .menu-select-all,
  .permission-select-all {
    margin-bottom: 15px;
    padding: 8px 0;
  }
}
</style>
