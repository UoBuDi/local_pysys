<template>
  <div class="investigation-detail">
    <!-- 搜索区域 -->
    <el-card class="search-panel">
      <template #header>
        <div class="card-header">
          <span>追查详单</span>
        </div>
      </template>

      <el-form :model="searchForm" :inline="true" class="search-form">
        <el-form-item label="通行标识ID">
          <el-input
            v-model="searchForm.pass_id"
            placeholder="请输入通行标识ID"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="车牌号码">
          <el-input
            v-model="searchForm.plate_number"
            placeholder="请输入车牌号码"
            clearable
            style="width: 160px"
          />
        </el-form-item>
        <el-form-item label="创建人">
          <el-input
            v-model="searchForm.created_by"
            placeholder="请输入创建人"
            clearable
            style="width: 130px"
          />
        </el-form-item>
        <el-form-item label="复核状态">
          <el-select
            v-model="searchForm.review_status"
            placeholder="全部"
            clearable
            style="width: 130px"
          >
            <el-option label="未复核" value="unreviewed" />
            <el-option label="已复核" value="reviewed" />
          </el-select>
        </el-form-item>
        <el-form-item label="加入时间">
          <el-date-picker
            v-model="searchForm.time_range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            value-format="YYYY-MM-DD HH:mm:ss"
            format="YYYY-MM-DD HH:mm:ss"
            :default-time="defaultTime"
            clearable
            style="width: 380px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleExport" v-hasPermi="'investigation:export'">
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-panel">
      <el-table
        :data="tableData"
        border
        stripe
        v-loading="loading"
        style="width: 100%"
        :max-height="tableMaxHeight"
        @row-click="handleRowClick"
        highlight-current-row
        class="clickable-table"
      >
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="pass_id" label="通行标识ID" min-width="280" show-overflow-tooltip />
        <el-table-column prop="plate_number" label="车牌号码" width="120" align="center" />
        <el-table-column prop="add_time" label="加入时间" width="180" align="center" />
        <el-table-column prop="created_by" label="创建人" width="100" align="center" />
        <el-table-column prop="review_result" label="复核结果" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.review_result">{{ row.review_result }}</span>
            <el-tag v-else type="info" size="small">未复核</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="reviewed_by" label="复核人" width="100" align="center">
          <template #default="{ row }">
            {{ row.reviewed_by || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="review_time" label="复核时间" width="180" align="center">
          <template #default="{ row }">
            {{ row.review_time || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click.stop="handleReview(row)"
              v-hasPermi="'investigation:review'"
            >
              复核
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click.stop="handleDelete(row)"
              v-hasPermi="'investigation:delete'"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 通行记录详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`通行记录详情 - ${detailRow.pass_id}`"
      width="85%"
      top="3vh"
      destroy-on-close
    >
      <!-- 追查基本信息 -->
      <el-descriptions :column="4" border size="small" class="detail-info">
        <el-descriptions-item label="通行标识ID">{{ detailRow.pass_id }}</el-descriptions-item>
        <el-descriptions-item label="车牌号码">{{ detailRow.plate_number }}</el-descriptions-item>
        <el-descriptions-item label="加入时间">{{ detailRow.add_time }}</el-descriptions-item>
        <el-descriptions-item label="创建人">{{ detailRow.created_by }}</el-descriptions-item>
        <el-descriptions-item label="复核结果">
          <el-tag v-if="detailRow.review_result" type="success" size="small">{{ detailRow.review_result }}</el-tag>
          <el-tag v-else type="info" size="small">未复核</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="复核人">{{ detailRow.reviewed_by || '-' }}</el-descriptions-item>
        <el-descriptions-item label="复核时间">{{ detailRow.review_time || '-' }}</el-descriptions-item>
      </el-descriptions>

      <!-- 通行记录表格 -->
      <div style="margin-top: 16px">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 8px">
          通行记录（共 {{ passRecordTotal }} 条）
        </div>
        <el-table
          :data="passRecordData"
          border
          stripe
          v-loading="detailLoading"
          style="width: 100%"
          :max-height="400"
          size="small"
        >
          <el-table-column type="index" label="序号" width="55" align="center" />
          <el-table-column
            v-for="col in passRecordColumns"
            :key="col"
            :prop="col"
            :label="col"
            min-width="140"
            show-overflow-tooltip
          />
        </el-table>
        <el-empty v-if="!detailLoading && passRecordData.length === 0" description="未查询到相关通行记录" />
      </div>
    </el-dialog>

    <!-- 复核对话框 -->
    <el-dialog
      v-model="reviewDialogVisible"
      title="提交复核结果"
      width="500px"
      destroy-on-close
    >
      <el-form :model="reviewForm" label-width="80px">
        <el-form-item label="通行标识ID">
          <el-input :model-value="reviewForm.pass_id" disabled />
        </el-form-item>
        <el-form-item label="车牌号码">
          <el-input :model-value="reviewForm.plate_number" disabled />
        </el-form-item>
        <el-form-item label="复核结果" required>
          <el-input
            v-model="reviewForm.review_result"
            type="textarea"
            :rows="4"
            placeholder="请输入复核结果（最多200字符）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reviewDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitReview" :loading="reviewLoading">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getInvestigationList,
  reviewInvestigation,
  deleteInvestigation,
  exportInvestigation,
  getPassRecords,
  type InvestigationRecord
} from '@/api/investigation'

const defaultTime = [new Date(0, 0, 0, 0, 0, 0), new Date(0, 0, 0, 23, 59, 59)]

// 搜索表单
const searchForm = reactive({
  pass_id: '',
  plate_number: '',
  created_by: '',
  review_status: '',
  time_range: null as [string, string] | null
})

// 表格数据
const tableData = ref<InvestigationRecord[]>([])
const loading = ref(false)
const tableMaxHeight = ref(600)

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 复核对话框
const reviewDialogVisible = ref(false)
const reviewLoading = ref(false)
const reviewForm = reactive({
  id: 0,
  pass_id: '',
  plate_number: '',
  review_result: ''
})

// 详情对话框
const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const detailRow = reactive({
  pass_id: '',
  plate_number: '',
  add_time: '',
  created_by: '',
  review_result: '' as string | null,
  reviewed_by: '' as string | null,
  review_time: '' as string | null
})
const passRecordData = ref<Record<string, any>[]>([])
const passRecordColumns = ref<string[]>([])
const passRecordTotal = ref(0)

/** 计算表格最大高度 */
const calcTableHeight = () => {
  tableMaxHeight.value = window.innerHeight - 320
}

/** 查询数据 */
const handleSearch = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.page,
      page_size: pagination.page_size
    }
    if (searchForm.pass_id) params.pass_id = searchForm.pass_id
    if (searchForm.plate_number) params.plate_number = searchForm.plate_number
    if (searchForm.created_by) params.created_by = searchForm.created_by
    if (searchForm.review_status) params.review_status = searchForm.review_status
    if (searchForm.time_range && searchForm.time_range.length === 2) {
      params.start_time = searchForm.time_range[0]
      params.end_time = searchForm.time_range[1]
    }

    const res: any = await getInvestigationList(params)
    if (res.code === 200) {
      tableData.value = res.data?.records || []
      pagination.total = res.data?.total || 0
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (e: any) {
    ElMessage.error('查询失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

/** 重置搜索 */
const handleReset = () => {
  searchForm.pass_id = ''
  searchForm.plate_number = ''
  searchForm.created_by = ''
  searchForm.review_status = ''
  searchForm.time_range = null
  pagination.page = 1
  handleSearch()
}

/** 点击行打开详情弹窗 */
const handleRowClick = async (row: InvestigationRecord) => {
  // 填充基本信息
  detailRow.pass_id = row.pass_id
  detailRow.plate_number = row.plate_number
  detailRow.add_time = row.add_time
  detailRow.created_by = row.created_by
  detailRow.review_result = row.review_result
  detailRow.reviewed_by = row.reviewed_by
  detailRow.review_time = row.review_time

  // 重置通行记录数据
  passRecordData.value = []
  passRecordColumns.value = []
  passRecordTotal.value = 0

  detailDialogVisible.value = true

  // 查询通行记录
  detailLoading.value = true
  try {
    const res: any = await getPassRecords(row.pass_id)
    if (res.code === 200) {
      passRecordData.value = res.data?.records || []
      passRecordColumns.value = res.data?.columns || []
      passRecordTotal.value = res.data?.total || 0
    } else {
      ElMessage.warning(res.message || '查询通行记录失败')
    }
  } catch (e: any) {
    ElMessage.error('查询通行记录失败: ' + (e.message || '未知错误'))
  } finally {
    detailLoading.value = false
  }
}

/** 打开复核对话框 */
const handleReview = (row: InvestigationRecord) => {
  reviewForm.id = row.id
  reviewForm.pass_id = row.pass_id
  reviewForm.plate_number = row.plate_number
  reviewForm.review_result = row.review_result || ''
  reviewDialogVisible.value = true
}

/** 提交复核 */
const submitReview = async () => {
  if (!reviewForm.review_result.trim()) {
    ElMessage.warning('请输入复核结果')
    return
  }
  reviewLoading.value = true
  try {
    const res: any = await reviewInvestigation({
      id: reviewForm.id,
      review_result: reviewForm.review_result.trim()
    })
    if (res.code === 200) {
      ElMessage.success('复核成功')
      reviewDialogVisible.value = false
      handleSearch()
    } else {
      ElMessage.error(res.message || '复核失败')
    }
  } catch (e: any) {
    ElMessage.error('复核失败: ' + (e.message || '未知错误'))
  } finally {
    reviewLoading.value = false
  }
}

/** 删除记录 */
const handleDelete = async (row: InvestigationRecord) => {
  try {
    await ElMessageBox.confirm(
      `确认删除通行标识ID为 "${row.pass_id}" 的追查记录？`,
      '删除确认',
      { type: 'warning' }
    )
    const res: any = await deleteInvestigation(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      handleSearch()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch {
    // 用户取消
  }
}

/** 导出数据 */
const handleExport = async () => {
  try {
    const params: Record<string, any> = {}
    if (searchForm.pass_id) params.pass_id = searchForm.pass_id
    if (searchForm.plate_number) params.plate_number = searchForm.plate_number
    if (searchForm.created_by) params.created_by = searchForm.created_by
    if (searchForm.review_status) params.review_status = searchForm.review_status
    if (searchForm.time_range && searchForm.time_range.length === 2) {
      params.start_time = searchForm.time_range[0]
      params.end_time = searchForm.time_range[1]
    }

    const res: any = await exportInvestigation(params)
    const blob = new Blob([res as any], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `追查详单_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error('导出失败: ' + (e.message || '未知错误'))
  }
}

onMounted(() => {
  calcTableHeight()
  window.addEventListener('resize', calcTableHeight)
  handleSearch()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', calcTableHeight)
})
</script>

<style scoped>
.investigation-detail {
  padding: 16px;
}

.search-panel {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0;
}

.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.clickable-table :deep(.el-table__row) {
  cursor: pointer;
}

.detail-info {
  margin-bottom: 8px;
}
</style>
