<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import { getRoleListApi, saveRoleApi, deleteRoleApi } from '@/api/role'
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
import { assignRoleMenusApi, getRoleMenusApi } from '@/api/role'

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
    label: t('userDemo.createTime')
  },
  {
    field: 'action',
    label: t('userDemo.action'),
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
            <BaseButton type="warning" onClick={() => assignMenus(data.row)}>
              {t('role.menu')}
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

const print = () => {
  const detailRefEl = unref(detailRef)
  detailRefEl?.print()
}

// 菜单分配相关
const menuDialogVisible = ref(false)
const menuLoading = ref(false)
const menuList = ref<any[]>([])
const selectedMenus = ref<number[]>([])

// 获取菜单列表
const getMenuList = async () => {
  menuLoading.value = true
  try {
    const res = await getMenuListApi()
    menuList.value = res.data?.list || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
  } finally {
    menuLoading.value = false
  }
}

// 打开菜单分配对话框
const assignMenus = async (row: any) => {
  currentRow.value = row
  menuDialogVisible.value = true

  // 获取菜单列表
  await getMenuList()

  // 获取角色当前的菜单
  try {
    const res = await getRoleMenusApi(row.id)
    selectedMenus.value = res.data || []
  } catch (error) {
    ElMessage.error(t('exampleDemo.loadFailed'))
    selectedMenus.value = []
  }
}

// 保存菜单分配
const saveMenus = async () => {
  if (!currentRow.value) return

  try {
    const res = await assignRoleMenusApi({
      role_id: currentRow.value.id,
      menu_ids: selectedMenus.value
    })

    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      menuDialogVisible.value = false
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
      <BaseButton type="primary" @click="AddAction">{{ t('exampleDemo.add') }}</BaseButton>
      <BaseButton :loading="delLoading" type="danger" @click="delData(null)">
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
      <BaseButton v-else type="primary" @click="print">
        {{ t('exampleDemo.print') }}
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
      <el-tree
        ref="menuTreeRef"
        :data="menuList"
        show-checkbox
        node-key="id"
        :props="{
          label: 'name',
          children: 'children'
        }"
        v-model:checked-keys="selectedMenus"
      />
    </div>

    <template #footer>
      <BaseButton type="primary" @click="saveMenus">{{ t('exampleDemo.save') }}</BaseButton>
      <BaseButton @click="menuDialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>
