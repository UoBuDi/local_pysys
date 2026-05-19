<script setup lang="tsx">
import { reactive, ref, unref } from 'vue'
import { getMenuListApi, saveMenuApi, deleteMenuApi } from '@/api/menu'
import { useTable } from '@/hooks/web/useTable'
import { useI18n } from '@/hooks/web/useI18n'
import { Table, TableColumn } from '@/components/Table'
import { ElTag, ElMessage } from 'element-plus'
import { Icon } from '@/components/Icon'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'
import { ContentWrap } from '@/components/ContentWrap'
import Write from './components/Write.vue'
import Detail from './components/Detail.vue'
import { Dialog } from '@/components/Dialog'
import { BaseButton } from '@/components/Button'

const { t } = useI18n()

const { tableRegister, tableState, tableMethods } = useTable({
  fetchDataApi: async () => {
    const res = await getMenuListApi()
    const list = res.data?.list || []

    // 将扁平列表转换为树形结构
    const buildTree = (items: any[], parentId = 0) => {
      return items
        .filter((item) => item.parentId === parentId || item.parent_id === parentId)
        .map((item) => ({
          ...item,
          children: buildTree(items, item.id)
        }))
    }

    const treeList = buildTree(list)
    return {
      list: treeList,
      total: list.length
    }
  }
})

const { dataList, loading } = tableState
const { getList, getElTableExpose } = tableMethods

const tableColumns = reactive<TableColumn[]>([
  {
    field: 'name',
    label: t('menu.menuName')
  },
  {
    field: 'icon',
    label: t('menu.icon'),
    slots: {
      default: (data: any) => {
        return (
          <>
            {data.row.icon ? (
              <Icon icon={data.row.icon} style="font-size: 20px;" />
            ) : (
              <span>-</span>
            )}
          </>
        )
      }
    }
  },
  {
    field: 'sortOrder',
    label: '排序',
    width: 80
  },
  {
    field: 'permission',
    label: t('menu.permission')
  },
  {
    field: 'component',
    label: t('menu.component')
  },
  {
    field: 'path',
    label: t('menu.path')
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
    label: t('menu.menuName'),
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
    await deleteMenuApi(idsToDelete)
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
    const res = await saveMenuApi(formData)
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
      row-key="id"
      :tree-props="{ children: 'children' }"
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

    <Detail v-if="isDetail" :current-row="currentRow" />

    <template #footer>
      <BaseButton v-if="!isDetail" type="primary" :loading="saveLoading" @click="save">
        {{ t('exampleDemo.save') }}
      </BaseButton>
      <BaseButton @click="dialogVisible = false">{{ t('exampleDemo.close') }}</BaseButton>
    </template>
  </Dialog>
</template>
