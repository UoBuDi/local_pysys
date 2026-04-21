<template>
  <div class="special-records">
    <el-tabs v-model="activeTab" type="border-card" @tab-change="handleTabChange">
      <el-tab-pane label="U型车" name="u-car">
        <div class="tab-content">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>U型车监控</span>
              </div>
            </template>
            <el-empty description="U型车数据展示区域" />
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="未付车" name="unpaid-car">
        <div class="tab-content">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>未付车监控</span>
              </div>
            </template>
            <el-empty description="未付车数据展示区域" />
          </el-card>
        </div>
      </el-tab-pane>
      <el-tab-pane label="无卡车" name="no-truck">
        <div class="tab-content">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>无卡车记录</span>
                <div class="header-actions">
                  <el-button type="success" @click="handleExport">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-button>
                  <el-upload
                    :show-file-list="false"
                    :before-upload="handleImport"
                    accept=".xlsx,.xls"
                    style="margin-left: 10px"
                  >
                    <el-button type="warning">
                      <el-icon><Upload /></el-icon>
                      导入
                    </el-button>
                  </el-upload>
                </div>
              </div>
            </template>

            <div class="filter-section">
              <el-form :inline="true" :model="noTruckFilter" class="filter-form">
                <el-form-item label="日期">
                  <el-date-picker
                    v-model="noTruckFilter.date"
                    type="date"
                    placeholder="选择日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    style="width: 150px"
                  />
                </el-form-item>

                <el-form-item label="收费出口">
                  <el-select
                    v-model="noTruckFilter.exitStation"
                    placeholder="请选择收费出口"
                    clearable
                    style="width: 150px"
                  >
                    <el-option
                      v-for="item in exitStationOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="收费入口">
                  <el-select
                    v-model="noTruckFilter.entryStation"
                    placeholder="请选择收费入口"
                    clearable
                    filterable
                    remote
                    :remote-method="remoteSearchStation"
                    :loading="stationLoading"
                    allow-create
                    default-first-option
                    style="width: 150px"
                  >
                    <el-option
                      v-for="item in entryStationOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="车道号">
                  <el-select
                    v-model="noTruckFilter.laneNumber"
                    placeholder="请选择车道号"
                    clearable
                    filterable
                    allow-create
                    default-first-option
                    style="width: 120px"
                  >
                    <el-option
                      v-for="item in laneNumberOptions"
                      :key="item.value"
                      :label="item.label"
                      :value="item.value"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="交易时间">
                  <el-time-picker
                    v-model="noTruckFilter.transactionTime"
                    placeholder="选择时间"
                    format="HH:mm:ss"
                    value-format="HH:mm:ss"
                    style="width: 150px"
                  />
                </el-form-item>

                <el-form-item label="车牌">
                  <el-input
                    v-model="noTruckFilter.licensePlate"
                    placeholder="请输入车牌"
                    clearable
                    style="width: 180px"
                  />
                </el-form-item>

                <el-form-item label="无卡操作原因">
                  <el-input
                    v-model="noTruckFilter.noCardReason"
                    placeholder="请输入原因"
                    clearable
                    style="width: 400px"
                  />
                </el-form-item>

                <el-form-item label="备注">
                  <el-input
                    v-model="noTruckFilter.remark"
                    placeholder="请输入备注"
                    clearable
                    style="width: 280px"
                  />
                </el-form-item>

                <el-form-item>
                  <el-button type="primary" @click="handleAddNoTruck">
                    <el-icon><Plus /></el-icon>
                    添加
                  </el-button>
                  <el-button @click="handleResetFilter">
                    <el-icon><Refresh /></el-icon>
                    重置
                  </el-button>
                </el-form-item>
              </el-form>
            </div>

            <el-table
              ref="tableRef"
              :data="noTruckTableData"
              border
              stripe
              style="width: 100%"
              max-height="500"
              v-loading="tableLoading"
              @selection-change="handleSelectionChange"
            >
              <el-table-column type="selection" width="55" align="center" />
              <el-table-column type="index" label="序号" width="60" align="center" />
              <el-table-column prop="date" label="日期" width="120" align="center" />
              <el-table-column
                prop="exit_station_display"
                label="收费出口"
                width="120"
                align="center"
              />
              <el-table-column
                prop="entry_station_display"
                label="收费入口"
                width="120"
                align="center"
              />
              <el-table-column prop="lane_number" label="车道号" width="100" align="center" />
              <el-table-column
                prop="transaction_time"
                label="交易时间"
                width="120"
                align="center"
              />
              <el-table-column prop="license_plate" label="车牌" width="120" align="center" />
              <el-table-column prop="reason" label="无卡操作原因" min-width="150" align="center" />
              <el-table-column prop="remark" label="备注" min-width="150" align="center" />
              <el-table-column label="操作" width="150" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="handleEdit(row)">
                    <el-icon><Edit /></el-icon>
                    编辑
                  </el-button>
                  <el-button type="danger" link @click="handleDelete(row)">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <div class="batch-actions" v-if="selectedRows.length > 0">
              <el-button type="danger" @click="handleBatchDelete">
                批量删除 ({{ selectedRows.length }})
              </el-button>
              <el-button type="success" @click="handleBatchExport">
                批量导出 ({{ selectedRows.length }})
              </el-button>
            </div>

            <el-pagination
              v-model:current-page="noTruckPagination.currentPage"
              v-model:page-size="noTruckPagination.pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="noTruckPagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              style="margin-top: 20px; justify-content: flex-end"
              @size-change="handleNoTruckSizeChange"
              @current-change="handleNoTruckCurrentChange"
            />
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog
      v-model="editDialogVisible"
      :title="editForm.id ? '编辑记录' : '新增记录'"
      width="600px"
    >
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="editForm.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="收费出口">
          <el-select
            v-model="editForm.exit_station"
            placeholder="请选择收费出口"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="item in exitStationOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="收费入口">
          <el-select
            v-model="editForm.entry_station"
            placeholder="请选择收费入口"
            clearable
            filterable
            remote
            :remote-method="remoteSearchStation"
            :loading="stationLoading"
            allow-create
            default-first-option
            style="width: 100%"
          >
            <el-option
              v-for="item in entryStationOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="车道号">
          <el-select
            v-model="editForm.lane_number"
            placeholder="请选择车道号"
            clearable
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="item in laneNumberOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="交易时间">
          <el-time-picker
            v-model="editForm.transaction_time"
            placeholder="选择时间"
            format="HH:mm:ss"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="车牌" required>
          <el-input v-model="editForm.license_plate" placeholder="请输入车牌" />
        </el-form-item>
        <el-form-item label="无卡操作原因">
          <el-input v-model="editForm.reason" placeholder="请输入原因" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Download, Upload, Edit, Delete, Refresh } from '@element-plus/icons-vue'
import request from '@/axios'
import detailQueryOptions from '@/assets/data/detail-query-options.json'

const activeTab = ref('no-truck')
const tableRef = ref()

const noTruckFilter = reactive({
  date: '',
  exitStation: '',
  entryStation: '',
  laneNumber: '',
  transactionTime: '',
  licensePlate: '',
  noCardReason: '',
  remark: ''
})

const exitStationOptions = ref<{ value: string; label: string }[]>(
  detailQueryOptions.exitstation?.options || []
)

const entryStationOptions = ref<{ value: string; label: string }[]>([])

const stationLoading = ref(false)
const tableLoading = ref(false)
let searchTimer: ReturnType<typeof setTimeout> | null = null

const laneNumberOptions = ref<{ value: string; label: string }[]>(
  detailQueryOptions.lanenumber?.options || []
)

interface NoTruckRecord {
  id: number
  date: string
  exit_station: string
  entry_station: string
  entry_station_name?: string
  exit_station_name?: string
  entry_station_display?: string
  exit_station_display?: string
  lane_number: string
  transaction_time: string
  license_plate: string
  reason: string
  remark: string
  created_at: string
  updated_at: string
}

const noTruckTableData = ref<NoTruckRecord[]>([])
const selectedRows = ref<NoTruckRecord[]>([])

const noTruckPagination = reactive({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

const editDialogVisible = ref(false)
const editForm = reactive({
  id: null as number | null,
  date: '',
  exit_station: '',
  entry_station: '',
  lane_number: '',
  transaction_time: '',
  license_plate: '',
  reason: '',
  remark: ''
})

const loadStations = async (keyword: string = '') => {
  try {
    stationLoading.value = true
    const res = await request.get({
      url: '/api/stations/',
      params: { keyword, limit: 50 }
    })
    if (res.code === 200 && res.data) {
      entryStationOptions.value = res.data
    }
  } catch (error) {
    console.error('加载收费站数据失败:', error)
  } finally {
    stationLoading.value = false
  }
}

const remoteSearchStation = (query: string) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    loadStations(query)
  }, 300)
}

const loadNoTruckRecords = async () => {
  try {
    tableLoading.value = true
    const res = await request.get({
      url: '/api/special-records/',
      params: {
        record_type: 'no-truck',
        page: noTruckPagination.currentPage,
        page_size: noTruckPagination.pageSize
      }
    })
    if (res.code === 200 && res.data) {
      noTruckTableData.value = res.data.list || []
      noTruckPagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载无卡车记录失败:', error)
    ElMessage.error('加载数据失败')
  } finally {
    tableLoading.value = false
  }
}

const handleAddNoTruck = async () => {
  if (!noTruckFilter.date) {
    ElMessage.warning('请选择日期')
    return
  }
  if (!noTruckFilter.licensePlate) {
    ElMessage.warning('请输入车牌')
    return
  }

  try {
    const res = await request.post({
      url: '/api/special-records/',
      data: {
        record_type: 'no-truck',
        date: noTruckFilter.date,
        exit_station: noTruckFilter.exitStation,
        entry_station: noTruckFilter.entryStation,
        lane_number: noTruckFilter.laneNumber,
        transaction_time: noTruckFilter.transactionTime,
        license_plate: noTruckFilter.licensePlate,
        reason: noTruckFilter.noCardReason,
        remark: noTruckFilter.remark
      }
    })

    if (res.code === 200) {
      ElMessage.success('添加成功')
      handleResetFilter()
      loadNoTruckRecords()
    } else {
      ElMessage.error(res.message || '添加失败')
    }
  } catch (error) {
    console.error('添加无卡车记录失败:', error)
    ElMessage.error('添加失败')
  }
}

const handleResetFilter = () => {
  noTruckFilter.date = ''
  noTruckFilter.exitStation = ''
  noTruckFilter.entryStation = ''
  noTruckFilter.laneNumber = ''
  noTruckFilter.transactionTime = ''
  noTruckFilter.licensePlate = ''
  noTruckFilter.noCardReason = ''
  noTruckFilter.remark = ''
}

const handleSelectionChange = (rows: NoTruckRecord[]) => {
  selectedRows.value = rows
}

const handleEdit = async (row: NoTruckRecord) => {
  editForm.id = row.id
  editForm.date = row.date
  editForm.exit_station = row.exit_station
  editForm.entry_station = row.entry_station
  editForm.lane_number = row.lane_number
  editForm.transaction_time = row.transaction_time
  editForm.license_plate = row.license_plate
  editForm.reason = row.reason
  editForm.remark = row.remark

  if (row.entry_station && row.entry_station_name) {
    const exists = entryStationOptions.value.find((item) => item.value === row.entry_station)
    if (!exists) {
      entryStationOptions.value.push({
        value: row.entry_station,
        label: row.entry_station_name
      })
    }
  }

  editDialogVisible.value = true
}

const handleSaveEdit = async () => {
  if (!editForm.date) {
    ElMessage.warning('请选择日期')
    return
  }
  if (!editForm.license_plate) {
    ElMessage.warning('请输入车牌')
    return
  }

  try {
    const res = await request.put({
      url: `/api/special-records/${editForm.id}`,
      data: {
        record_type: 'no-truck',
        date: editForm.date,
        exit_station: editForm.exit_station,
        entry_station: editForm.entry_station,
        lane_number: editForm.lane_number,
        transaction_time: editForm.transaction_time,
        license_plate: editForm.license_plate,
        reason: editForm.reason,
        remark: editForm.remark
      }
    })

    if (res.code === 200) {
      ElMessage.success('保存成功')
      editDialogVisible.value = false
      loadNoTruckRecords()
    } else {
      ElMessage.error(res.message || '保存失败')
    }
  } catch (error) {
    console.error('保存记录失败:', error)
    ElMessage.error('保存失败')
  }
}

const handleDelete = async (row: NoTruckRecord) => {
  try {
    await ElMessageBox.confirm('确定要删除该记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const res = await request.delete({ url: `/api/special-records/${row.id}` })

    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadNoTruckRecords()
    } else {
      ElMessage.error(res.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除记录失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedRows.value.length} 条记录吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const ids = selectedRows.value.map((row) => row.id)
    const res = await request.post({
      url: '/api/special-records/batch-delete',
      data: { ids }
    })

    if (res.code === 200) {
      ElMessage.success('批量删除成功')
      loadNoTruckRecords()
    } else {
      ElMessage.error(res.message || '批量删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

const handleExport = async () => {
  try {
    const res = await request.get({
      url: '/api/special-records/export/',
      params: { record_type: 'no-truck' },
      responseType: 'blob'
    })

    const blobData = res.data || res
    const blob = new Blob([blobData], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `无卡车记录_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handleBatchExport = async () => {
  try {
    const ids = selectedRows.value.map((row) => row.id)
    const res = await request.post({
      url: '/api/special-records/export/',
      data: { ids, record_type: 'no-truck' },
      responseType: 'blob'
    })

    const blobData = res.data || res
    const blob = new Blob([blobData], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `无卡车记录_选中${selectedRows.value.length}条_${new Date().toISOString().slice(0, 10)}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)

    ElMessage.success('导出成功')
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

const handleImport = async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('record_type', 'no-truck')

  try {
    tableLoading.value = true
    const res = await request.post({
      url: '/api/special-records/import/',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.code === 200) {
      ElMessage.success(`导入成功，共导入 ${res.data.count} 条记录`)
      loadNoTruckRecords()
    } else {
      ElMessage.error(res.message || '导入失败')
    }
  } catch (error) {
    console.error('导入失败:', error)
    ElMessage.error('导入失败')
  } finally {
    tableLoading.value = false
  }

  return false
}

const handleNoTruckSizeChange = (val: number) => {
  noTruckPagination.pageSize = val
  loadNoTruckRecords()
}

const handleNoTruckCurrentChange = (val: number) => {
  noTruckPagination.currentPage = val
  loadNoTruckRecords()
}

const handleTabChange = (tabName: string) => {
  if (tabName === 'no-truck') {
    loadNoTruckRecords()
  }
}

onMounted(() => {
  loadStations()
  if (activeTab.value === 'no-truck') {
    loadNoTruckRecords()
  }
})
</script>

<style lang="scss" scoped>
.special-records {
  padding: 20px;

  .tab-content {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-actions {
        display: flex;
        align-items: center;
      }
    }

    .filter-section {
      margin-bottom: 20px;

      .filter-form {
        display: flex;
        flex-wrap: wrap;

        .el-form-item {
          margin-bottom: 10px;
          margin-right: 10px;
        }
      }
    }

    .batch-actions {
      margin-top: 10px;
      padding: 10px;
      background-color: #f5f7fa;
      border-radius: 4px;
    }
  }
}
</style>
