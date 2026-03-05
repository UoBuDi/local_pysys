<script setup lang="tsx">
import { ContentWrap } from '@/components/ContentWrap'
import { Search } from '@/components/Search'
import { Dialog } from '@/components/Dialog'
import { useI18n } from '@/hooks/web/useI18n'
import { ElTag, ElMessage } from 'element-plus'
import { Table } from '@/components/Table'
import { getDepartmentTableApi, saveDepartmentApi, deleteDepartmentApi } from '@/api/department'
import type { DepartmentItem } from '@/api/department/types'
import { useTable } from '@/hooks/web/useTable'
import { ref, unref, reactive } from 'vue'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { CrudSchema, useCrudSchemas } from '@/hooks/web/useCrudSchemas'
import { BaseButton } from '@/components/Button'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const { currentPage, pageSize } = tableState
    const res = await getDepartmentTableApi({
      pageIndex: unref(currentPage),
      pageSize: unref(pageSize),
      ...unref(searchParams)
    })

    // 处理后端返回的数据格式，支持分页和非分页两种情况
    let list = []
    let total = 0

    if (res.data && typeof res.data === 'object' && 'list' in res.data) {
      // 分页情况下，res.data是包含list和total的对象
      list = res.data.list || []
      total = res.data.total || 0
    } else {
      // 非分页情况下，res.data直接是部门列表
      list = res.data || []
      total = list.length
    }

    return {
      list,
      total
    }
  }
})

const { getList, getElTableExpose } = tableMethods

const searchParams = ref({})

getList()

// 表格CRUD相关
const crudSchemas = reactive<CrudSchema[]>([
  {
    field: 'index',
    label: t('userDemo.index'),
    type: 'index',
    width: '80px'
  },
  {
    field: 'name',
    label: t('userDemo.departmentName'),
    search: {
      component: 'Input'
    }
  },
  {
    field: 'status',
    label: t('userDemo.status'),
    formatter: (row: DepartmentItem) => {
      return (
        <ElTag type={row.status ? 'success' : 'danger'}>
          {row.status ? t('userDemo.enable') : t('userDemo.disable')}
        </ElTag>
      )
    },
    search: {
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
  },
  {
    field: 'createTime',
    label: t('userDemo.createTime'),
    formatter: (row: DepartmentItem) => {
      return row.created_at || ''
    }
  },
  {
    field: 'action',
    label: t('userDemo.action'),
    width: '260px',
    search: {
      hidden: true
    },
    form: {
      hidden: true
    },
    detail: {
      hidden: true
    },
    table: {
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
              <BaseButton type="danger" onClick={() => delData(data.row)}>
                {t('exampleDemo.del')}
              </BaseButton>
            </>
          )
        }
      }
    }
  }
])

// @ts-ignore
const { allSchemas } = useCrudSchemas(crudSchemas)

const dialogVisible = ref(false)
const dialogTitle = ref('')

const currentRow = ref<DepartmentItem | null>(null)
const actionType = ref('')

const AddAction = () => {
  dialogTitle.value = t('exampleDemo.add')
  currentRow.value = null
  dialogVisible.value = true
  actionType.value = ''
}

const delLoading = ref(false)

const delData = async (row: DepartmentItem | null) => {
  const elTableExpose = await getElTableExpose()
  const selection = row ? [row] : ((await elTableExpose?.getSelectionRows()) as DepartmentItem[])

  if (!selection.length) {
    return
  }

  delLoading.value = true

  try {
    // 将选中的行ID转换为数字数组
    const idsToDelete = selection.map((item) => item.id)
    await deleteDepartmentApi(idsToDelete)
    ElMessage.success(t('exampleDemo.delSuccess'))
    getList()
  } catch (error) {
    ElMessage.error(t('exampleDemo.delFailed'))
  } finally {
    delLoading.value = false
  }
}

const action = (row: DepartmentItem, type: string) => {
  dialogTitle.value = t(type === 'edit' ? 'exampleDemo.edit' : 'exampleDemo.detail')
  actionType.value = type
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
    const res = await saveDepartmentApi(formData)
    if (res.code === 200) {
      ElMessage.success(t('exampleDemo.saveSuccess'))
      dialogVisible.value = false
      getList()
    } else {
      ElMessage.error(t('exampleDemo.saveFailed'))
    }
  } catch (error) {
    ElMessage.error(t('exampleDemo.saveFailed'))
  } finally {
    saveLoading.value = false
  }
}

const writeRefEl = ref<ComponentRef<typeof Write>>()

const detailRef = ref<ComponentRef<typeof Detail>>()

// const print = () => {
//   const detailRefEl = unref(detailRef)
//   detailRefEl?.print()
// }

const setSearchParams = (params: any) => {
  searchParams.value = params
  getList()
}
</script>

<template>
  <ContentWrap>
    <Search :schema="allSchemas.searchSchema" @search="setSearchParams" @reset="setSearchParams" />

    <div class="mt-20px">
      <BaseButton type="primary" @click="AddAction">{{ t('exampleDemo.add') }}</BaseButton>
      <BaseButton :loading="delLoading" type="danger" @click="delData(null)">
        {{ t('exampleDemo.del') }}
      </BaseButton>
    </div>

    <Table
      :pageSize="unref(tableState.pageSize)"
      :currentPage="unref(tableState.currentPage)"
      :columns="allSchemas.tableColumns"
      :data="unref(tableState.dataList)"
      :loading="unref(tableState.loading)"
      :pagination="{
        total: unref(tableState.total)
      }"
      @register="tableRegister"
      @update:pageSize="(val) => (tableState.pageSize = val)"
      @update:currentPage="(val) => (tableState.currentPage = val)"
    />
  </ContentWrap>

  <Dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    :height="actionType === 'detail' ? 400 : 'auto'"
    :width="800"
    @close="dialogVisible = false"
  >
    <Write
      v-if="actionType !== 'detail'"
      ref="writeRefEl"
      :current-row="currentRow"
      :schema="allSchemas.formSchema"
    />

    <Detail
      v-if="actionType === 'detail'"
      ref="detailRef"
      :current-row="currentRow"
      :schema="allSchemas.detailSchema"
    />

    <template #footer>
      <BaseButton
        v-if="actionType !== 'detail'"
        type="primary"
        :loading="saveLoading"
        @click="save"
      >
        {{ t('exampleDemo.save') }}
      </BaseButton>
      <BaseButton v-else type="primary" disabled>
        {{ t('exampleDemo.print') }}
      </BaseButton>
      <BaseButton @click="dialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>
