<script setup lang="tsx">
import { ContentWrap } from '@/components/ContentWrap'
import { useI18n } from '@/hooks/web/useI18n'
import { Table, TableColumn } from '@/components/Table'
import { ref, unref, nextTick, watch, reactive, computed } from 'vue'
import { ElTree, ElInput, ElDivider, ElMessage, ElTag } from 'element-plus'
import { getDepartmentApi, getUserByIdApi, saveUserApi, deleteUserByIdApi } from '@/api/department'
import type { DepartmentItem, DepartmentUserItem } from '@/api/department/types'
import { useTable } from '@/hooks/web/useTable'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { Dialog } from '@/components/Dialog'
import { getRoleListApi } from '@/api/role'
import { CrudSchema, useCrudSchemas } from '@/hooks/web/useCrudSchemas'
import { BaseButton } from '@/components/Button'
import { assignUserRolesApi, getUserRolesApi } from '@/api/user-role'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { pageSize, currentPage } = tableState
    const res = await getUserByIdApi({
      department_id: unref(currentNodeKey),
      pageIndex: unref(currentPage),
      pageSize: unref(pageSize),
      ...unref(searchParams)
    })
    return {
      list: res.data?.list || [],
      total: res.data?.total || 0
    }
  }
})

const { dataList, loading, total, pageSize, currentPage } = tableState
const { getList, getElTableExpose } = tableMethods

const treeData = ref<DepartmentItem[]>([])
const currentNodeKey = ref('')

// 获取部门数据
const getDepartmentData = async () => {
  const res = await getDepartmentApi()
  const data = res.data || []
  // 添加"全部"选项作为根节点
  const allDepartments = {
    id: '',
    name: t('userDemo.departmentList'),
    children: data
  }
  treeData.value = [allDepartments]
  currentNodeKey.value = ''
  nextTick(() => {
    getList()
  })
}

getDepartmentData()

// 树节点点击事件
const handleNodeClick = (data: DepartmentItem) => {
  currentNodeKey.value = data.id?.toString() || ''
  getList()
}

// 搜索参数
const searchParams = ref({})

const setSearchParams = (params: any) => {
  searchParams.value = params
  getList()
}

// 表格列定义
const tableColumns = reactive<TableColumn[]>([
  {
    field: 'index',
    label: t('userDemo.index'),
    type: 'index',
    width: '80px'
  },
  {
    field: 'username',
    label: t('userDemo.username')
  },
  {
    field: 'nickname',
    label: t('userDemo.account')
  },
  {
    field: 'email',
    label: t('userDemo.email')
  },
  {
    field: 'roles',
    label: '用户权限',
    width: '200px',
    formatter: (_: DepartmentUserItem) => {
      return getUserRoleNames(_)
    }
  },
  {
    field: 'department_id',
    label: t('userDemo.department'),
    formatter: (_: DepartmentUserItem, __: unknown, cellValue: any) => {
      if (_.department && typeof _.department === 'object') {
        return _.department.name || _.department.departmentName || t('userDemo.superiorDepartment')
      }
      const dept = departmentList.value.find((d) => d.id === cellValue)
      if (dept) {
        return dept.name || dept.departmentName || t('userDemo.superiorDepartment')
      }
      return cellValue || t('userDemo.superiorDepartment')
    }
  },
  {
    field: 'status',
    label: t('userDemo.status'),
    formatter: (row: DepartmentUserItem) => {
      return (
        <ElTag type={row.status ? 'success' : 'danger'}>
          {row.status ? t('userDemo.enable') : t('userDemo.disable')}
        </ElTag>
      )
    }
  },
  {
    field: 'createTime',
    label: t('userDemo.createTime'),
    formatter: (row: DepartmentUserItem) => {
      return row.created_at || ''
    }
  },
  {
    field: 'action',
    label: t('userDemo.action'),
    width: '420px',
    slots: {
      default: (data: any) => {
        return (
          <>
            <BaseButton type="primary" onClick={() => action(data.row, 'edit')}>
              {t('exampleDemo.edit')}
            </BaseButton>
            <BaseButton type="success" onClick={() => action(data.row, 'detail')}>
              {t('exampleDemo.detail')}
            </BaseButton>
            <BaseButton type="warning" onClick={() => openRoleDialog(data.row)}>
              {t('role.assignRole')}
            </BaseButton>
            <BaseButton type="danger" onClick={() => delData(data.row)}>
              {t('exampleDemo.del')}
            </BaseButton>
          </>
        )
      }
    }
  }
])

// 表单相关的crud schema（只用于生成form和detail schema）
const crudSchemas = reactive<CrudSchema[]>([
  {
    field: 'username',
    label: t('userDemo.username')
  },
  {
    field: 'nickname',
    label: t('userDemo.account')
  },
  {
    field: 'password',
    label: t('userDemo.password'),
    form: {
      component: 'InputPassword',
      componentProps: {
        placeholder: '留空则不修改密码，如需修改请输入新密码',
        showPassword: true,
        autocomplete: 'new-password'
      }
    },
    detail: {
      hidden: true
    }
  },
  {
    field: 'email',
    label: t('userDemo.email')
  },
  {
    field: 'department_id',
    label: t('userDemo.department'),
    form: {
      component: 'Select',
      componentProps: {
        options: computed(() =>
          departmentList.value.map((dept) => ({
            label: dept.name || dept.departmentName,
            value: dept.id
          }))
        ),
        loading: computed(() => departmentLoading.value),
        placeholder: t('userDemo.pleaseSelectDepartment'),
        clearable: true
      }
    }
  },
  {
    field: 'status',
    label: t('userDemo.status')
  }
])

// @ts-ignore
const { allSchemas } = useCrudSchemas(crudSchemas)

// 搜索表单schema
const searchSchema = reactive<FormSchema[]>([
  {
    field: 'username',
    label: t('userDemo.username'),
    component: 'Input'
  },
  {
    field: 'nickname',
    label: t('userDemo.account'),
    component: 'Input'
  },
  {
    field: 'email',
    label: t('userDemo.email'),
    component: 'Input'
  },
  {
    field: 'status',
    label: t('userDemo.status'),
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

const departmentList = ref<DepartmentItem[]>([])
const departmentLoading = ref(false)

const loadDepartmentList = async () => {
  departmentLoading.value = true
  try {
    const res = await getDepartmentApi()
    departmentList.value = res.data || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
    departmentList.value = []
  } finally {
    departmentLoading.value = false
  }
}

loadDepartmentList()

// 角色列表缓存
const roleListCache = ref<Map<number, any>>(new Map())
const allRolesList = ref<any[]>([])

// 获取所有角色列表
const loadAllRoles = async () => {
  try {
    const res = await getRoleListApi()
    allRolesList.value = res.data?.list || []
    // 构建角色缓存
    roleListCache.value = new Map()
    allRolesList.value.forEach((role) => {
      roleListCache.value.set(role.id, role)
    })
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  }
}

loadAllRoles()

// 获取用户角色名称
const getUserRoleNames = (user: DepartmentUserItem) => {
  if (!user.roles || !Array.isArray(user.roles)) {
    return '-'
  }
  return user.roles
    .map((roleId: number) => {
      const role = roleListCache.value.get(roleId)
      return role ? role.name : ''
    })
    .filter((name: string) => name)
    .join(', ')
}

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isDetail = ref(false)

const currentRow = ref<DepartmentUserItem | null>(null)

const AddAction = () => {
  dialogTitle.value = t('exampleDemo.add')
  currentRow.value = null
  dialogVisible.value = true
  isDetail.value = false
}

const delLoading = ref(false)

const delData = async (row: DepartmentUserItem | null) => {
  const elTableExpose = await getElTableExpose()
  const selection = row
    ? [row]
    : ((await elTableExpose?.getSelectionRows()) as DepartmentUserItem[])

  if (!selection.length) {
    return
  }

  delLoading.value = true

  try {
    // 将选中的行ID转换为数字数组
    const idsToDelete = selection.map((item) => item.id)
    await deleteUserByIdApi(idsToDelete)
    ElMessage.success(t('exampleDemo.delSuccess'))
    getList()
  } catch (error) {
    ElMessage.error(t('exampleDemo.delFailed'))
  } finally {
    delLoading.value = false
  }
}

const action = (row: DepartmentUserItem, type: string) => {
  console.log('action函数被调用，原始行数据:', row)
  dialogTitle.value = t(type === 'edit' ? 'exampleDemo.edit' : 'exampleDemo.detail')
  isDetail.value = type === 'detail'

  let processedRow: DepartmentUserItem
  if (row.department && row.department.id) {
    processedRow = { ...row, department_id: row.department.id }
    console.log('处理后的行数据（添加department_id）:', processedRow)
  } else {
    processedRow = row
    console.log('使用原始行数据:', processedRow)
  }

  // 如果是详情窗口，将department_id替换为部门名称
  if (type === 'detail') {
    const detailRow = { ...processedRow }
    if (detailRow.department_id) {
      const dept = departmentList.value.find((d) => d.id === detailRow.department_id)
      if (dept) {
        detailRow.department_id = dept.name || dept.departmentName || ''
      }
    } else if (
      detailRow.department &&
      (detailRow.department.name || detailRow.department.departmentName)
    ) {
      detailRow.department_id = detailRow.department.name || detailRow.department.departmentName
    }
    currentRow.value = detailRow as DepartmentUserItem
  } else {
    currentRow.value = processedRow as DepartmentUserItem
  }

  dialogVisible.value = true
}

const saveLoading = ref(false)

const save = async () => {
  const writeRef = unref(writeRefEl)
  if (!writeRef) return
  const formData = await writeRef.submit()
  if (!formData) return

  console.log('保存用户，提交的表单数据:', formData)

  // 处理表单数据
  const processedData = { ...formData }

  // 如果是编辑用户（有id），删除不必要的字段，只保留需要的字段
  if (processedData.id) {
    console.log('编辑用户，清理不必要的字段')
    // 删除不需要的字段
    delete processedData.created_at
    delete processedData.updated_at
    delete processedData.createTime
    delete processedData.role
    delete processedData.account
  }

  console.log('处理后的表单数据:', processedData)

  saveLoading.value = true
  try {
    const res = await saveUserApi(processedData)
    console.log('保存用户API响应:', res)
    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      dialogVisible.value = false
      getList()
    } else {
      ElMessage.error(res.message || t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error(t('exampleDemo.saveFailed'))
  } finally {
    saveLoading.value = false
  }
}

const writeRefEl = ref<ComponentRef<typeof Write>>()

const detailRef = ref<ComponentRef<typeof Detail>>()

const print = () => {
  const detailRefEl = unref(detailRef)
  detailRefEl?.print()
}

// 分配角色相关
const roleDialogVisible = ref(false)
const roleLoading = ref(false)
const roleList = ref<any[]>([])
const selectedRoles = ref<number[]>([])

// 获取角色列表
const getRoleList = async () => {
  roleLoading.value = true
  try {
    const res = await getRoleListApi()
    roleList.value = res.data?.list || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  } finally {
    roleLoading.value = false
  }
}

// 打开角色分配对话框
const openRoleDialog = async (row: DepartmentUserItem) => {
  currentRow.value = row
  roleDialogVisible.value = true

  // 获取角色列表
  await getRoleList()

  // 获取用户当前的角色
  try {
    const res = await getUserRolesApi(row.id)
    selectedRoles.value = res.data || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
    selectedRoles.value = []
  }
}

// 保存角色分配
const saveRoles = async () => {
  if (!currentRow.value) return

  try {
    const res = await assignUserRolesApi({
      user_id: currentRow.value.id,
      role_ids: selectedRoles.value
    })

    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      roleDialogVisible.value = false
    } else {
      ElMessage.error(res.message || t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('exampleDemo.saveFailed'))
  }
}
</script>

<template>
  <div class="flex">
    <ContentWrap class="mr-20px flex-shrink-0" :style="{ width: '200px' }">
      <div class="flex justify-between items-center mb-10px">
        <span>{{ t('userDemo.departmentList') }}</span>
      </div>
      <ElDivider />
      <ElTree
        :data="treeData"
        node-key="id"
        :props="{
          label: 'name'
        }"
        :expand-on-click-node="false"
        :current-node-key="currentNodeKey"
        @node-click="handleNodeClick"
      />
    </ContentWrap>

    <ContentWrap class="flex-grow">
      <Search :schema="searchSchema" @search="setSearchParams" @reset="setSearchParams" />

      <div class="mt-20px">
        <BaseButton type="primary" @click="AddAction">{{ t('exampleDemo.add') }}</BaseButton>
        <BaseButton :loading="delLoading" type="danger" @click="delData(null)">
          {{ t('exampleDemo.del') }}
        </BaseButton>
      </div>

      <Table
        v-model:pageSize="pageSize"
        v-model:currentPage="currentPage"
        :columns="tableColumns"
        :data="dataList"
        :loading="loading"
        :pagination="{
          total
        }"
        @register="tableRegister"
      />
    </ContentWrap>
  </div>

  <Dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :height="isDetail ? 400 : 'auto'"
    :width="800"
    @close="dialogVisible = false"
  >
    <Write
      v-if="!isDetail"
      ref="writeRefEl"
      :current-row="currentRow"
      :schema="allSchemas.formSchema"
    />

    <Detail
      v-if="isDetail"
      ref="detailRef"
      :current-row="currentRow"
      :schema="allSchemas.detailSchema"
    />

    <template #footer>
      <BaseButton v-if="!isDetail" type="primary" :loading="saveLoading" @click="save">
        {{ t('exampleDemo.save') }}
      </BaseButton>
      <BaseButton v-else type="primary" @click="print">
        {{ t('exampleDemo.print') }}
      </BaseButton>
      <BaseButton @click="dialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>

  <!-- 角色分配对话框 -->
  <Dialog
    v-model="roleDialogVisible"
    :title="t('role.role')"
    :width="500"
    @close="roleDialogVisible = false"
  >
    <div v-loading="roleLoading">
      <el-select v-model="selectedRoles" multiple :placeholder="t('role.role')" style="width: 100%">
        <el-option v-for="role in roleList" :key="role.id" :label="role.name" :value="role.id" />
      </el-select>
    </div>

    <template #footer>
      <BaseButton type="primary" @click="saveRoles">{{ t('exampleDemo.save') }}</BaseButton>
      <BaseButton @click="roleDialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>
